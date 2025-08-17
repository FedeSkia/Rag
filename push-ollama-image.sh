#!/bin/bash

AWS_REGION="${AWS_REGION:-eu-west-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-507881105499}"
IMAGE_NAME="${IMAGE_NAME:-rag-langchain-ollama}"
ECR_REPOSITORY="${ECR_REPOSITORY:-rag-app}"
SERVICE_TAG="${SERVICE_TAG:-rag-langchain-ollama-latest}"
CLUSTER_NAME = "${CLUSTER_NAME:-my-rag-app-cluster}"
echo "Building image"
docker build -f ./docker/ollama/Dockerfile \
  --platform linux/amd64 \
  --build-arg OLLAMA_MODELS="qwen3:0.6b" \
  -t $IMAGE_NAME \
  ./docker/ollama

# 2. Login ad ECR
echo -e "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# --- Delete ONLY the image with the given tag in ECR (if present) ---
echo -e "🧹 Deleting existing ECR image with tag: $SERVICE_TAG (if any)..."
aws ecr batch-delete-image \
  --repository-name "$ECR_REPOSITORY" \
  --image-ids imageTag="$SERVICE_TAG" \
  --region "$AWS_REGION" >/dev/null 2>&1 || true


# 3. Tag image for ECR
echo -e "🏷️ Tagging image with service-specific tag..."
docker tag $IMAGE_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$SERVICE_TAG

echo -e "⬆️ Pushing image to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$SERVICE_TAG

# 6. Update del servizio ECS (se già exists)
echo -e "🔄 Updating ECS service..."
aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --force-new-deployment --region $AWS_REGION