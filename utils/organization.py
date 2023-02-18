import yaml

class OrganizationHelper:
    def __init__(self, session):
        self.orgs_client = session.client('organizations')
    
    def _get_all_accounts(self):
        accounts = []
        paginator = self.orgs_client.get_paginator('list_accounts')
        for page in paginator.paginate():
            accounts += page['Accounts']
        return accounts
    
    def _get_active_accounts(self):
        accounts = self._get_all_accounts()
        return [account for account in accounts if account['Status'] == 'ACTIVE']
    
    def _get_suspended_accounts(self):
        accounts = self._get_all_accounts()
        return [account for account in accounts if account['Status'] == 'SUSPENDED']
    
    def _output_to_file(self, accounts, file_name):
        output = {'accounts': [{'Id': account['Id'], 'Name': account['Name'], 'Status': account['Status']} for account in accounts]}
        with open(file_name, 'w') as f:
            yaml.dump(output, f)
    
    def output_all_accounts_to_file(self, file_name):
        accounts = self._get_all_accounts()
        self._output_to_file(accounts, file_name)
    
    def output_active_accounts_to_file(self, file_name):
        accounts = self._get_active_accounts()
        self._output_to_file(accounts, file_name)
    
    def output_suspended_accounts_to_file(self, file_name):
        accounts = self._get_suspended_accounts()
        self._output_to_file(accounts, file_name)
