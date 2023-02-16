"""
    Author: 
        Louis To
    
    LinkedIn: 
        https://www.linkedin.com/in/louisto/
    
    Description: 
        This script was developed this script to help organizations set up CloudTrail in each member account and forward log events to a central Logging account. 
        The script iterates through all AWS Organizations member accounts to create an account CloudTrail trail for management actions. 
        Alternatively, a config file (see template in repo) can be used to add CloudTrail trails for specific accounts rather than for all accounts in the organization.

    Limitations / Requirements:
        Management account credentials must be set with aws config
        Each member account should have an access role that can be assumed by the management user

    Help or questions? 
        Please feel free to reach out to me on LinkedIn!
    
"""
import os
import json
import boto3
import yaml

def get_account_list_from_config(config_file_path: str) -> list:
    
    """Returns a list of accounts to update from the account-list.yaml file."""

    with open(config_file_path, 'r') as f:
        config = yaml.safe_load(f)

    # Get the list of accounts from the config file
    account_list = config.get('accounts')

    if account_list is None:
        raise ValueError("Invalid config file. 'accounts' key not found.")

    return account_list

def get_all_accounts(org_client) -> list:
    
    """Returns a list of all active accounts in the AWS Organization."""
    accounts = []
    next_token = None
    while True:
        if next_token:
            response = org_client.list_accounts(NextToken=next_token)
        else:
            response = org_client.list_accounts()

        for account in response['Accounts']:
            if account['Status'] != 'SUSPENDED':
                accounts.append(account)

        if 'NextToken' in response:
            next_token = response['NextToken']
        else:
            break
    return accounts

def get_logging_account_s3_client(sts_client, role_arn):
    
    """Returns an S3 client object authorized to access the S3 bucket for logging AWS CloudTrail events in a logging account."""

    logging_account_assumed_role = sts_client.assume_role(RoleArn=role_arn, RoleSessionName='assume-role-session')

    # Get temporary credentials for the assumed role
    temp_credentials = logging_account_assumed_role['Credentials']

    # Return an S3 client with the temporary credentials
    return boto3.client('s3',
        aws_access_key_id=temp_credentials['AccessKeyId'],
        aws_secret_access_key=temp_credentials['SecretAccessKey'],
        aws_session_token=temp_credentials['SessionToken'])

def set_logging_account_s3_bucket_default_policy(logging_account_s3_client, cloudtrail_bucket_name, logging_account_id):

    """
    Sets the default policy for an S3 bucket in the logging account that will allow CloudTrail to write logs to the bucket.

    This function first tries to retrieve the current policy for the specified S3 bucket. If the policy doesn't exist, the function creates a new policy with default permissions that will allow CloudTrail to write logs to the specified bucket.

    If the policy already exists, the function checks whether the policy includes permissions for the specified bucket and account ID. If the account ID and bucket are already included in the policy, the function does nothing. If they are not included, the function adds statements to the policy that will allow CloudTrail to write logs to the specified bucket for the specified account ID.

    Args:
        logging_account_s3_client (boto3.client): An S3 client object for the logging account.
        cloudtrail_bucket_name (str): The name of the S3 bucket where CloudTrail logs will be stored.
        logging_account_id (str): The AWS account ID for the logging account.

    Returns:
        dict: The new or current bucket policy as a dictionary.
    """

    try:
        bucket_policy = logging_account_s3_client.get_bucket_policy(Bucket=cloudtrail_bucket_name)
        return json.loads(bucket_policy['Policy'])
    except:
        # If the policy does not exist, create a new one with default settings
        policy_json = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowCloudTrailAclCheck",
                    "Effect": "Allow",
                    "Principal": {"Service": "cloudtrail.amazonaws.com"},
                    "Action": [
                        "s3:GetBucketAcl"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{cloudtrail_bucket_name}"
                    ]
                },
                {
                    "Sid": "AllowCloudTrailWrite",
                    "Effect": "Allow",
                    "Principal": {"Service": "cloudtrail.amazonaws.com"},
                    "Action": [
                        "s3:PutObject"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{cloudtrail_bucket_name}/AWSLogs/{logging_account_id}/*"
                    ]
                }
            ]
        }
        # Set the bucket policy
        logging_account_s3_client.put_bucket_policy(Bucket=cloudtrail_bucket_name, Policy=json.dumps(policy_json))
        print(f"Created new bucket policy for {cloudtrail_bucket_name}")

    bucket_policy = logging_account_s3_client.get_bucket_policy(Bucket=cloudtrail_bucket_name)
    return json.loads(bucket_policy['Policy'])

def update_bucket_policy(list_of_accounts, cloudtrail_bucket_name, bucket_policy_json, logging_account_s3_client):

    """Update the bucket policy of an S3 bucket used for CloudTrail logs with statements for each account in the list of accounts."""
    
    for account in list_of_accounts:
        account_id = str(account['Id'])
        
        put_object_statement = {
            "Sid": f"CloudTrail_PutObject_{account_id}",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudtrail.amazonaws.com"
            },
            "Action": [
                "s3:PutObject"
            ],
            "Resource": [ 
                f"arn:aws:s3:::{cloudtrail_bucket_name}/AWSLogs/{account_id}/*"
            ]
        }
        get_acl_statement = {
            "Sid": f"CloudTrail_GetBucketAcl_{account_id}",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudtrail.amazonaws.com"
            },
            "Action": [
                "s3:GetBucketAcl"
            ],
            "Resource": [
                f"arn:aws:s3:::{cloudtrail_bucket_name}"
            ]
        }
        # Check if the account statements are already in the policy
        existing_statements = [s for s in bucket_policy_json['Statement'] if s['Sid'].startswith('CloudTrail_')]
        existing_put_object_sids = [s['Sid'] for s in existing_statements if account_id in s['Sid'] and 'PutObject' in s['Sid']]
        existing_get_acl_sids = [s['Sid'] for s in existing_statements if account_id in s['Sid'] and 'GetBucketAcl' in s['Sid']]

        if existing_put_object_sids and existing_get_acl_sids:
            print(f"Skipping account {account_id}, already in policy")
        else:
            if not existing_put_object_sids:
                bucket_policy_json['Statement'].append(put_object_statement)
                print(f"Adding PutObject statement for account {account_id} to Cloudtrail logging bucket policy")
            if not existing_get_acl_sids:
                bucket_policy_json['Statement'].append(get_acl_statement)
                print(f"Adding GetBucketAcl statement for account {account_id} to Cloudtrail logging bucket policy")
    
    # Update the bucket policy with the modified JSON
    new_policy = json.dumps(bucket_policy_json)
    logging_account_s3_client.put_bucket_policy(Bucket=cloudtrail_bucket_name, Policy=new_policy)

def create_account_cloudtrail(cloudtrail_client, account_trail_name, cloudtrail_bucket_name):
    
    """Create a cloudtrail for the given account client and target bucket."""

    # Check if the CloudTrail trail already exists
    response = cloudtrail_client.describe_trails(trailNameList=[account_trail_name])
    if len(response['trailList']) > 0:
        print(f"CloudTrail trail '{account_trail_name}' already exists, skipping creation")
        trail_arn = response['trailList'][0]['TrailARN']
    else:
        # Create the CloudTrail trail
        response = cloudtrail_client.create_trail(
            Name=account_trail_name,
            S3BucketName=cloudtrail_bucket_name,
            IsMultiRegionTrail=True,
            EnableLogFileValidation=True,
            IncludeGlobalServiceEvents=True
        )

        # Get the ARN of the new trail
        trail_arn = response['TrailARN']
        print(f"CloudTrail trail '{account_trail_name}' created with ARN '{trail_arn}'")
    # Start logging events to the trail
    cloudtrail_client.start_logging(Name=account_trail_name)

    # Verify that the trail was created and logging events
    response = cloudtrail_client.describe_trails(trailNameList=[account_trail_name])
    print(response)

# User Selection: Config or All Accounts in Org
load_config: str = input("Please choose an option:\n1. Add CloudTrail to all accounts in the organization.\n2. Add CloudTrail only to accounts listed in account-list.yaml.\nEnter 1 or 2: ")
config_file_path = os.path.join(os.getcwd(), 'account-list.yaml')

# Read the management account ID and logging account ID from user input
management_account_id = input("Enter the management account ID: ") or '123456789012'
logging_account_id = input("Enter the logging account ID: ") or '234567890123'
member_account_access_role_name = input("Enter the name of the member account access role: ") or 'OrganizationAccountAccessRole'
cloudtrail_bucket_name = input("Enter the central cloudtrail bucket name: ") or 'aws-cloudtrail-logs-234567890123'
account_trail_name = input("Enter the trail name to create in each account: ") or 'management-events'

# Get a list of all accounts in the organization, skipping suspended accounts
org_client = boto3.client('organizations')

list_of_accounts = []
if load_config in ['1', '2']:
    if load_config == '1':
        list_of_accounts = get_all_accounts(org_client)
    else:
        list_of_accounts = get_account_list_from_config(str(config_file_path))
else:
    raise ValueError("Invalid input. Please enter either 1 or 2.")

# Get the current logging bucket policy, set a default one if none exists.
sts_client = boto3.client('sts')
logging_account_role_arn = f'arn:aws:iam::{logging_account_id}:role/{member_account_access_role_name}'
logging_account_s3_client = get_logging_account_s3_client(sts_client, logging_account_role_arn)
bucket_policy_json = set_logging_account_s3_bucket_default_policy(logging_account_s3_client, cloudtrail_bucket_name, logging_account_id)

# Add new resources and permissions for each account in the organization if not already in the bucket policy
update_bucket_policy(list_of_accounts, cloudtrail_bucket_name, bucket_policy_json, logging_account_s3_client)

# Start with the management account client
cloudtrail_client = boto3.client('cloudtrail')
sts_client = boto3.client('sts')
    
# Assume the OrganizationAccountAccessRole
for account in list_of_accounts:
    if account['Id'] != management_account_id:
        role_arn = f'arn:aws:iam::{account["Id"]}:role/{member_account_access_role_name}'  
        assumed_role = sts_client.assume_role(RoleArn=role_arn, RoleSessionName='assume-role-session')
        
        # Get temporary credentials for the assumed role
        temp_credentials = assumed_role['Credentials']

        # Create a CloudTrail client with the temporary credentials
        cloudtrail_client = boto3.client('cloudtrail',
            aws_access_key_id=temp_credentials['AccessKeyId'],
            aws_secret_access_key=temp_credentials['SecretAccessKey'],
            aws_session_token=temp_credentials['SessionToken'])    
    
    # Create cloudtrail in the account if it does not already exist
    create_account_cloudtrail(cloudtrail_client, account_trail_name, cloudtrail_bucket_name)

    
