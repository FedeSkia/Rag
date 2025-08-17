#!/bin/bash

AWS_REGION="${AWS_REGION:-eu-west-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-507881105499}"
IMAGE_NAME="${IMAGE_NAME:-rag-langchain-vllm}"
ECR_REPOSITORY="${ECR_REPOSITORY:-rag-app}"
SERVICE_TAG="${SERVICE_TAG:-rag-langchain-vllm-latest}"

echo "Building image"
docker build -f ./docker/VLLM/Dockerfile --platform linux/amd64 -t $IMAGE_NAME .

# 2. Login ad ECR
echo -e "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# 3. Tag image for ECR
echo -e "🏷️ Tagging image with service-specific tag..."
docker tag $IMAGE_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$SERVICE_TAG

echo -e "⬆️ Pushing image to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$SERVICE_TAG
