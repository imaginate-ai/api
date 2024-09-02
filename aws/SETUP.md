# AWS Guide

This guide will walk you through how to utilize the CloudFormation templates used to deploy this application!

## Prerequisites
1. Download the AWS CLI following [this documentation](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

## First Time Setup
1. Build the stacks corresponding to the files `roles.yml` and `billing.yml` through the AWS Cloud Console.
2. Determine the `dev` access credentials and `lambda_arn` from the `roles.yml` stack output for the next step 
3. Configure the `~/.aws/config` and `~/.aws/credentials` files with the necessary data. The location of these files can be determined [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html#cli-configure-files-where):

`~/.aws/config`:
```
[profile dev]
role_arn = <lambda_arn>
source_profile = default
```

`~/.aws/credentials`:
```
[default]
aws_access_key_id = <dev_id> 
aws_secret_access_key = <dev_key>
```
4. Add the following secrets to GitHub: `LAMBDA_ARN`, `DEV_ID`, `DEV_KEY`

**NOTE**: Upon building the `billing.yml` stack you should receive a confirmation email to verify the notification subscription

## Deploying / Updating Stack
**NOTE:** These commands must be run from the root directory
1. Build the updated Lambda code with: `python aws/build_lambda_code.py` which will create a `aws.zip` file
2. Deploy the code with: `./aws/deploy.sh`


## Documentation
- [AWS authentication and access credentials](https://docs.aws.amazon.com/cli/latest/userguide/cli-authentication-user.html)