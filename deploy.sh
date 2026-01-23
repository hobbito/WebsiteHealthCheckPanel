#!/bin/bash

# Health Check Panel - Deployment Script
# This script should be run on the DigitalOcean Droplet

set -e

echo "🚀 Health Check Panel - Deployment Script"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/healthcheck"
REPO_URL="https://github.com/YOUR-USERNAME/health-check-panel.git"
BRANCH="main"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed"
        exit 1
    fi
}

# Check prerequisites
log_info "Checking prerequisites..."
check_command "docker"
check_command "docker-compose"
check_command "git"

# Navigate to project directory
if [ ! -d "$PROJECT_DIR" ]; then
    log_error "Project directory $PROJECT_DIR does not exist"
    exit 1
fi

cd $PROJECT_DIR

# Pull latest changes
log_info "Pulling latest changes from $BRANCH..."
git fetch origin
git reset --hard origin/$BRANCH

# Stop services
log_info "Stopping services..."
docker-compose -f docker-compose.prod.yml down

# Build new images
log_info "Building new images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Start services
log_info "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for database
log_info "Waiting for database to be ready..."
sleep 10

# Run migrations
log_info "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec -T app alembic upgrade head

# Check services status
log_info "Checking services status..."
docker-compose -f docker-compose.prod.yml ps

# Health check
log_info "Running health check..."
sleep 5

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    log_info "✅ Application is healthy!"
else
    log_error "❌ Health check failed!"
    exit 1
fi

# Show logs
log_info "Recent logs:"
docker-compose -f docker-compose.prod.yml logs --tail=20

log_info "✨ Deployment completed successfully!"
log_info "Application is running at: http://$(curl -s ifconfig.me)"
