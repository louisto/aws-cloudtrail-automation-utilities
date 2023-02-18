"""
    Author: 
        Louis To
    
    LinkedIn: 
        https://www.linkedin.com/in/louisto/
    
    Description: 
        The create_cloudtrails.py script is designed to enable the creation of CloudTrail in accounts managed by an AWS Organization. 
        The script uses the configuration settings in the app_settings.yaml file and retrieves the list of accounts from the accounts.yaml file, 
        which can be generated using the create_accounts_list.py script.

        The script will create a CloudTrail in each account in the accounts.yaml file. 
        Each CloudTrail will write logs to an S3 bucket, which is specified in the app_settings.yaml file. 
        The bucket policy will also be updated to allow write access from the CloudTrail in each account.

        To run the script, you must have management account credentials set up with the AWS CLI configuration and specify the profile name in app_settings.yaml.
        Also, each member account must have an access role that can be assumed by the management user.

    Help or questions? 
        Please feel free to reach out to me on LinkedIn!
    
"""

import yaml
from utils.cloudtrail import CloudTrailHelper
from utils.organization import OrganizationHelper
from utils.session import SessionHelper

# Get an aws client session and config settings from app_settings.yaml
session_helper = SessionHelper('app_settings.yaml')
session, config = session_helper.get_session_and_config()

# Instantiate helpers
organization_helper = OrganizationHelper(session)
cloudtrail_helper = CloudTrailHelper(config, session)

# Get a list of accounts from the organization
accounts_output_file_name = 'accounts.yaml'
accounts = []
with open(accounts_output_file_name, "r") as file:
    accounts = yaml.safe_load(file)['accounts']

# Filter out accounts in SUSPENDED state
active_accounts = [account for account in accounts if account['Status'] == 'ACTIVE']

print(f"Executing this script will...")
print(f"""
Create a CloudTrail named {config['AccountCloudTrailName']} in each Account from accounts.yaml

Each Account CloudTrail will write logs to:
    S3 Bucket: {config['CloudTrailBucketName']}
    Account: {config['LoggingAccountId']}
    
""")
print("List of Accounts:")
[print(account["Id"]) for account in active_accounts]
print("")

selection : str = input("Confirm Create CloudTrails in each account [Y/n]: ")

if selection == 'Y':
    # Add CloudTrail to each account, Add Logging Account Bucket Permissions
    cloudtrail_helper.add_cloudtrail_to_accounts(active_accounts)
else:
    print("Invalid selection, operation cancelled.")