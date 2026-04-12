#!/bin/bash
# YieldBot AI Deployment Script
# Builds Docker image and deploys to VPS

set -e

# Configuration
IMAGE_NAME="yieldbot-ai"
CONTAINER_NAME="yieldbot-ai"
REGISTRY_URL="${REGISTRY_URL:-}"  # Optional: docker.io/username/yieldbot-ai

echo "🚀 YieldBot AI Deployment Script"
echo "================================"

# Step 1: Build Docker image
echo "📦 Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

if [ -n "${REGISTRY_URL}" ]; then
    # Step 2: Tag and push to registry (optional)
    echo "🏷️  Tagging image for registry..."
    docker tag ${IMAGE_NAME}:latest ${REGISTRY_URL}/${IMAGE_NAME}:latest
    
    echo "📤 Pushing to registry..."
    docker push ${REGISTRY_URL}/${IMAGE_NAME}:latest
fi

# Step 3: Stop existing container
echo "🛑 Stopping existing container (if running)..."
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true

# Step 4: Start new container
echo "▶️  Starting new container..."
docker run -d \
    --name ${CONTAINER_NAME} \
    --restart unless-stopped \
    --env-file .env \
    -v $(pwd)/logs:/app/logs \
    -v $(pwd)/state:/app/state \
    ${IMAGE_NAME}:latest

# Step 5: Show logs
echo "✅ Deployment complete!"
echo "📊 Viewing logs (Ctrl+C to exit, container continues running)..."
docker logs -f ${CONTAINER_NAME}
