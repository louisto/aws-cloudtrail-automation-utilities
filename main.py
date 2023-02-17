"""
    Author: 
        Louis To
    
    LinkedIn: 
        https://www.linkedin.com/in/louisto/
    
    Description: 
        This script was developed to add Account CloudTrails to accounts managed by an AWS Organization.
        The script is driven by app_settings.yaml, which contains all settings necessary to execute.

    Limitations / Requirements:
        Management account credentials must be set with aws config
        Each member account should have an access role that can be assumed by the management user

    Help or questions? 
        Please feel free to reach out to me on LinkedIn!
    
"""

import yaml
import boto3
from utils.cloudtrail import CloudTrailHelper
from utils.organization import OrganizationHelper

#Get the app config
app_settings = 'app_settings.yaml'
config = {}
with open(app_settings, "r") as file:
    config = yaml.safe_load(file)

session = boto3.Session(profile_name=config['LocalProfile'])

#Instantiate helpers
organization_helper = OrganizationHelper(session)
cloudtrail_helper = CloudTrailHelper(config, session)

#Get a list of accounts from the organization
accounts_output_file_name = 'accounts.yaml'
organization_helper.output_active_accounts_to_file(accounts_output_file_name)

accounts = []
with open(accounts_output_file_name, "r") as file:
    accounts = yaml.safe_load(file)['accounts']

#Update bucket policy to allow write from CloudTrail in each account
cloudtrail_helper.update_cloudtrail_bucket_policy(accounts)

#Add CloudTrail to each account
cloudtrail_helper.add_cloudtrail_to_accounts(accounts)
