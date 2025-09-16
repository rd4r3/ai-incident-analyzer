#!/bin/bash
echo "🧹 Cleaning up Docker containers..."

# Stop all running containers
echo "Stopping containers..."
docker stop $(docker ps -q) 2>/dev/null || true

# Remove all containers
echo "Removing containers..."
docker rm $(docker ps -a -q) 2>/dev/null || true

# Remove all volumes
echo "Removing volumes..."
docker volume rm $(docker volume ls -q) 2>/dev/null || true

# Remove all networks
echo "Removing networks..."
docker network rm $(docker network ls -q) 2>/dev/null || true

# Remove all images
echo "Removing images..."
docker rmi $(docker images -q) 2>/dev/null || true

# Prune system
echo "Pruning system..."
docker system prune -a -f --volumes

echo "✅ Cleanup complete!"