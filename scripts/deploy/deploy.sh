#!/bin/bash
# HandyOsint Deployment Script

set -e

echo "🚀 HandyOsint Deployment Script"
echo "================================"

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "⚠️  Warning: Running as root"
fi

# Parse arguments
ENV=${1:-production}
VERSION=${2:-latest}

echo "Environment: $ENV"
echo "Version: $VERSION"

# Backup current deployment
if [ -d "deploy_backup" ]; then
    rm -rf deploy_backup
fi
if [ -d "deploy" ]; then
    mv deploy deploy_backup
    echo "✅ Backed up previous deployment"
fi

# Create new deployment directory
mkdir -p deploy
cp -r core ui main.py requirements.txt config.yaml deploy/
cp -r data logs reports exports deploy/ 2>/dev/null || true

# Create necessary directories in deploy
mkdir -p deploy/data deploy/logs deploy/reports deploy/exports

# Set permissions
chmod -R 755 deploy
chmod -R 777 deploy/data deploy/logs deploy/reports deploy/exports

# Create environment file
cat > deploy/.env << ENV
APP_ENV=$ENV
LOG_LEVEL=INFO
DB_PATH=./data/social_scan.db
EXPORT_DIR=./exports
REPORT_DIR=./reports
ENV

echo "✅ Deployment prepared in 'deploy/' directory"

# If Docker is available, build image
if command -v docker &> /dev/null; then
    echo "🐳 Building Docker image..."
    docker build -t handyosint:$VERSION .
    echo "✅ Docker image built: handyosint:$VERSION"
fi

echo ""
echo "🎉 Deployment ready!"
echo "To run: cd deploy && python main.py"
echo "Or with Docker: docker run -v \$(pwd)/data:/app/data handyosint:$VERSION"
