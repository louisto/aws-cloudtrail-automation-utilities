# AWS CloudTrail Setup Script

Author: Louis To
LinkedIn: https://www.linkedin.com/in/louisto/

## Overview

This script was developed to help organizations set up CloudTrail in each member account and forward log events to a central Logging account. The script iterates through all AWS Organizations member accounts to create an account CloudTrail trail for management actions. Alternatively, a config file can be used to add CloudTrail trails for specific accounts rather than for all accounts in the organization.

The following features are included in this script:

* Automatically creates CloudTrail trails in each member account of an Organization
* Configures CloudTrail trails to log management events and store them in a central S3 bucket
* Configures an S3 bucket policy to allow CloudTrail to write logs to the specified bucket
* Can use a configuration file to target specific accounts in the organization

## Limitations/Requirements

* Management account credentials must be set with AWS Config
* Each member account should have an access role that can be assumed by the management user

## Usage

1. Clone this repository: `git clone https://github.com/louisto/aws-utils`
2. Navigate to the project directory: `cd aws-utils`
3. Install the required Python packages: `pip install -r requirements.txt`
4. Set the following environment variables:

    * AWS_ACCESS_KEY_ID
    * AWS_SECRET_ACCESS_KEY
    * AWS_DEFAULT_REGION

5. Run the script: `python3 make-cloudtrail.py`

## Help/Questions?

Please feel free to reach out to me on [LinkedIn](https://www.linkedin.com/in/louisto/) for help or questions.

## License

This project is licensed under the [MIT License](https://github.com/<your_username>/<your_repository>/blob/main/LICENSE).
