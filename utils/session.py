import boto3
import yaml

class SessionHelper:
    def __init__(self, app_settings_filename):
        
        # Get the app config
        self.config = {}
        with open(app_settings_filename, "r") as file:
            self.config = yaml.safe_load(file)
        
    def get_session_and_config(self):
        return (boto3.Session(profile_name=self.config['LocalProfile']), self.config)