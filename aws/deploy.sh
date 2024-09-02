#!/bin/bash
BUCKET_NAME="imaginate-templates-bucket"
STACK_NAME="imaginate"
REGION="us-east-1"
PROFILE="dev"

# Read environment variables
source .env

# AWS build/deploy
aws s3 mb s3://$BUCKET_NAME --region $REGION --profile $PROFILE
aws cloudformation package --template-file aws/deploy.yml --s3-bucket $BUCKET_NAME --output-template-file aws/packaged-deploy.yml --profile $PROFILE
aws cloudformation deploy --template-file aws/packaged-deploy.yml --stack-name $STACK_NAME --region $REGION --capabilities CAPABILITY_NAMED_IAM --profile $PROFILE --parameter-overrides mongoToken=$MONGO_TOKEN
