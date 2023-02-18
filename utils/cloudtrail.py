import boto3
import json

class CloudTrailHelper:
    def __init__(self, config, session):
        self.config = config
        self.s3_client = session.client('s3')
        self.sts_client = session.client('sts')
        self.cloudtrail_client = session.client('cloudtrail')
        self.logging_account_s3_client = self._get_logging_account_s3_client()

    def _get_assumed_role_client(self, service, role_arn):
        assumed_role = self.sts_client.assume_role(RoleArn=role_arn, RoleSessionName='assume-role-session')
                
        # Get temporary credentials for the assumed role
        temp_credentials = assumed_role['Credentials']

        # Return a client with the temporary credentials
        return boto3.client(service,
            aws_access_key_id=temp_credentials['AccessKeyId'],
            aws_secret_access_key=temp_credentials['SecretAccessKey'],
            aws_session_token=temp_credentials['SessionToken'])

    def _get_logging_account_s3_client(self):
    
        """Returns an S3 client object for the Logging Account."""

        logging_account_role_arn = f'arn:aws:iam::{self.config["LoggingAccountId"]}:role/{self.config["OrganizationAccountAccessRole"]}'
        return self._get_assumed_role_client('s3', logging_account_role_arn)

    def _get_cloudtrail_bucket_policy(self):

        """Returns cloudtrail bucket policy, sets a default if the policy is missing."""

        try:
            response = self.logging_account_s3_client.get_bucket_policy(Bucket=self.config['CloudTrailBucketName'])
            policy = json.loads(response['Policy'])
        except Exception as e:
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
                            f"arn:aws:s3:::{self.config['CloudTrailBucketName']}"
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
                            f"arn:aws:s3:::{self.config['CloudTrailBucketName']}/AWSLogs/{self.config['LoggingAccountId']}/*"
                        ]
                    }
                ]
            }
            # Set the bucket policy
            self.logging_account_s3_client.put_bucket_policy(Bucket=self.config['CloudTrailBucketName'], Policy=json.dumps(policy_json))
            print(f"{self.config['CloudTrailBucketName']}: Missing Bucket Policy, created default bucket policy.")

            # Get the policy and return it
            policy = policy_json

        return policy
    
    def _update_cloudtrail_bucket_policy(self, accounts):
        bucket_policy = self._get_cloudtrail_bucket_policy()
        
        for account in accounts:
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
                    f"arn:aws:s3:::{self.config['CloudTrailBucketName']}/AWSLogs/{account_id}/*"
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
                    f"arn:aws:s3:::{self.config['CloudTrailBucketName']}"
                ]
            }

            # Check if the account statements are already in the policy
            existing_statements = [s for s in bucket_policy['Statement'] if s['Sid'].startswith('CloudTrail_')]
            existing_put_object_sids = [s['Sid'] for s in existing_statements if account_id in s['Sid'] and 'PutObject' in s['Sid']]
            existing_get_acl_sids = [s['Sid'] for s in existing_statements if account_id in s['Sid'] and 'GetBucketAcl' in s['Sid']]

            if existing_put_object_sids and existing_get_acl_sids:
                print(f"Skipping account {account_id}, already in policy")
            else:
                if not existing_put_object_sids:
                    bucket_policy['Statement'].append(put_object_statement)
                    print(f"Adding PutObject statement for account {account_id} to Cloudtrail logging bucket policy")
                if not existing_get_acl_sids:
                    bucket_policy['Statement'].append(get_acl_statement)
                    print(f"Adding GetBucketAcl statement for account {account_id} to Cloudtrail logging bucket policy")
        
        # Update the bucket policy with the modified JSON
        self.logging_account_s3_client.put_bucket_policy(Bucket=self.config['CloudTrailBucketName'], Policy=json.dumps(bucket_policy))

    def _create_account_cloudtrail(self, cloudtrail_client):
    
        """Create a cloudtrail for the given account client and target bucket."""

        # Check if the CloudTrail trail already exists
        response = cloudtrail_client.describe_trails(trailNameList=[self.config['AccountCloudTrailName']])
        if len(response['trailList']) > 0:
            print(f"CloudTrail trail '{self.config['AccountCloudTrailName']}' already exists, skipping creation")
            trail_arn = response['trailList'][0]['TrailARN']
        else:
            # Create the CloudTrail trail
            response = cloudtrail_client.create_trail(
                Name=self.config['AccountCloudTrailName'],
                S3BucketName=self.config['CloudTrailBucketName'],
                IsMultiRegionTrail=True,
                EnableLogFileValidation=True,
                IncludeGlobalServiceEvents=True
            )

            # Get the ARN of the new trail
            trail_arn = response['TrailARN']
            print(f"CloudTrail trail '{self.config['AccountCloudTrailName']}' created with ARN '{trail_arn}'")

        # Start logging events to the trail
        cloudtrail_client.start_logging(Name=self.config['AccountCloudTrailName'])

        # Verify that the trail was created and logging events
        response = cloudtrail_client.describe_trails(trailNameList=[self.config['AccountCloudTrailName']])
        print(response)


    def add_cloudtrail_to_accounts(self, accounts):
        # Update bucket policy to allow write from CloudTrail in each account
        self._update_cloudtrail_bucket_policy(accounts)

        # Create a CloudTrail for the Organization Management account, if it does not already exist.
        self._create_account_cloudtrail(self.cloudtrail_client)

        for account in accounts:
            if account['Id'] != self.config["ManagementAccountId"]:
                role_arn = f'arn:aws:iam::{account["Id"]}:role/{self.config["OrganizationAccountAccessRole"]}'  
                cloudtrail_client = self._get_assumed_role_client("cloudtrail", role_arn)
                
                self._create_account_cloudtrail(cloudtrail_client)
            
    
            
    