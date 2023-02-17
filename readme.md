# AWS CloudTrail Setup Script

Author: Louis To
LinkedIn: https://www.linkedin.com/in/louisto/

## Overview

This utility suite was developed to help create a CloudTrail in each member account in an Organization and forward log events to a central logging account bucket. 

create_accounts_list.py
Creates accounts.yaml, which is a list of accounts from the Organization. Options for the account list are:
* All Accounts
* Active Accounts Only
* Suspended Accounts Only

create_cloudtrails.py
* Automatically create a CloudTrail in each account in the accounts.yaml file. 
* Each CloudTrail will write logs to the central logging account bucket, which is specified in the app_settings.yaml file. 

## Limitations/Requirements

* Management account credentials must be set with AWS Config
* Each member account should have an access role that can be assumed by the management user

## Usage

1. Clone this repository: `git clone https://github.com/louisto/aws-utils`
2. Navigate to the project directory: `cd aws-utils`
3. Install the required Python packages: `pip install -r requirements.txt`
4. Use aws configure to create a profile
5. Update app-settings.yaml to reflect your organization requirements
6. Execute create_accounts_list.py to generate a list of accounts
7. Execute create_cloudtrails.py to create the cloudtrails in each account

## Help/Questions?

Please feel free to reach out to me on [LinkedIn](https://www.linkedin.com/in/louisto/) for help or questions.

## License

This project is licensed under the [MIT License](https://github.com/<your_username>/<your_repository>/blob/main/LICENSE).
