"""
    Author: 
        Louis To
    
    LinkedIn: 
        https://www.linkedin.com/in/louisto/
    
    Description: 
        The create_accounts_list.py script is a utility script that helps generate a list of member accounts for an AWS Organization. 
        This list can then be used to automate the process of adding CloudTrails to these accounts. 
        
        The user can create a list for:
            all accounts
            active accounts 
            suspended accounts
        
        The list of accounts is written to accounts.yaml.
        
        To run the script, you must have management account credentials set up with the AWS CLI configuration and specify the profile name in app_settings.yaml.

    Help or questions? 
        Please feel free to reach out to me on LinkedIn!
    
"""

from utils.organization import OrganizationHelper
from utils.session import SessionHelper

# Get an aws client session and config settings from app_settings.yaml
session_helper = SessionHelper('app_settings.yaml')
session, config = session_helper.get_session_and_config()

# Instantiate helpers
org_helper = OrganizationHelper(session)

# Get a list of accounts from the organization
accounts_output_file_name = 'accounts.yaml'

print("Management Account: {config['ManagementAccountId']}")
print("What account list would you like to create?")
print("  1 - All Accounts in Organization")
print("  2 - All Active Accounts")
print("  3 - All Suspended Accounts")
selection : str = input("Choice: ")

file_name = 'accounts.yaml'
if selection == '1':
    org_helper.output_all_accounts_to_file(file_name)
elif selection == '2':
    org_helper.output_active_accounts_to_file(file_name)
elif selection == '3':
    org_helper.output_suspended_accounts_to_file(file_name)

print(f"List of selected Accounts have been written to {file_name}")
