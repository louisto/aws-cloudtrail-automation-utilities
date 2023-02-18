# AWS CloudTrail Setup Script

Author: Louis To
LinkedIn: https://www.linkedin.com/in/louisto/

## Overview

This utility suite was developed to help create a CloudTrail in each member account in an Organization. 

###### Step 1: Update app_settings.yaml
The **app_settings.yaml** file is used to configure account settings for the script.

* LocalProfile
    * Name of the aws configure profile with management account access credentials
* ManagementAccountId
    * AccountId for the Management Account
* LoggingAccountId
    * AccountId for the Logging Account where all CloudTrail logs are being stored.
* CloudTrailBucketName
    * Name of the CloudTrail S3 Bucket in the Logging Account
* OrganizationAccountAccessRole
    * Access role that the management role can assume under each member account to create the CloudTrail trails.
* AccountCloudTrailName
    * Name of the CloudTrail to be created in each member account

###### Step 2: Create accounts.yaml
Use **create_accounts_list.py** to create a list of accounts. This script will read from your Organization Management account and output the list of
Organization Member Accounts to a accounts.yaml

* Options:
    * All Accounts
    * Active Accounts Only
    * Suspended Accounts Only

###### Step 3: Create CloudTrails
Use **create_cloudtrails.py** to create a CloudTrail for each account listed in accounts.yaml. 

This script will add each member account to the central CloudTrail Logging Bucket policy and then create a CloudTrail for each account.

## Limitations/Requirements

* Management account credentials must be set with an AWS Config profile
* Each member account should have an access role that can be assumed by the management user

## Usage

1. Clone this repository: `git clone https://github.com/louisto/aws-cloudtrail-automation-utilities`
2. Navigate to the project directory: `cd aws-utils`
3. Install the required Python packages: `pip install -r requirements.txt`
4. Use aws configure to create a profile
5. Update app_settings.yaml to reflect your organization requirements
6. Execute create_accounts_list.py to generate a list of accounts
7. Execute create_cloudtrails.py to create the cloudtrails in each account

## Help/Questions?

Please feel free to reach out to me on [LinkedIn](https://www.linkedin.com/in/louisto/) for help or questions.

## License

This project is licensed under the [MIT License](https://github.com/louisto/aws-cloudtrail-automation-utilities/blob/main/LICENSE).
