#!/bin/bash
set -e

# Static variables
BUCKET_NAME="imaginate-templates-bucket"
STACK_NAME="imaginate"
REGION="us-east-1"
PROFILE="dev"

# Read environment variables
source .env

# Load first argument as MONGO_TOKEN if passed
if [ "$1" ]; then
  echo "Loading MONGO_TOKEN..."
  MONGO_TOKEN=$1
fi

# Make sure MONGO_TOKEN is not empty
if [ "$MONGO_TOKEN" = "" ]; then
  echo "MONGO_TOKEN is empty"
  exit 1
fi

# AWS build/deploy
echo "Fetching bucket..."
aws s3 mb s3://$BUCKET_NAME --region $REGION --profile $PROFILE # Make bucket (if it does not exist)
aws s3 rm s3://$BUCKET_NAME --region $REGION --profile $PROFILE --recursive # Delete all objects
echo "Packaging..."
aws cloudformation package --template-file aws/deploy.yml --s3-bucket $BUCKET_NAME --output-template-file aws/packaged-deploy.yml --region $REGION --profile $PROFILE # Compile template
ls aws
echo "Deploying..."
aws cloudformation deploy --template-file aws/packaged-deploy.yml --stack-name $STACK_NAME --capabilities CAPABILITY_NAMED_IAM --region $REGION --profile $PROFILE --parameter-overrides mongoToken=$MONGO_TOKEN # Deploy with template
echo "Check status..."
aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --profile $PROFILE --query "Stacks[0].StackStatus" --output text # Output stack status
