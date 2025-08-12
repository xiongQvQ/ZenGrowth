#!/bin/bash

# Docker build script for User Behavior Analytics Platform
# Provides optimized build process with caching and multi-architecture support

set -e

# Configuration
IMAGE_NAME="user-behavior-analytics"
IMAGE_TAG="${1:-latest}"
REGISTRY="${REGISTRY:-}"
PLATFORM="${PLATFORM:-linux/amd64,linux/arm64}"
BUILD_ARGS=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Help function
show_help() {
    cat << EOF
Docker Build Script for User Behavior Analytics Platform

Usage: $0 [TAG] [OPTIONS]

Arguments:
  TAG                 Docker image tag (default: latest)

Environment Variables:
  REGISTRY           Docker registry URL (optional)
  PLATFORM           Target platforms (default: linux/amd64,linux/arm64)
  BUILD_TYPE         Build type: dev, prod (default: prod)
  CACHE_FROM         Cache source image (optional)

Examples:
  $0                 # Build with latest tag
  $0 v1.0.0          # Build with specific tag
  BUILD_TYPE=dev $0  # Build development image
  REGISTRY=myregistry.com $0 v1.0.0  # Build and tag for registry

Options:
  -h, --help         Show this help message
  --no-cache         Build without using cache
  --dev              Build development image
  --prod             Build production image (default)
  --push             Push image to registry after build
  --multi-arch       Build for multiple architectures
EOF
}

# Parse command line arguments
NO_CACHE=false
PUSH_IMAGE=false
MULTI_ARCH=false
BUILD_TYPE="${BUILD_TYPE:-prod}"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --dev)
            BUILD_TYPE="dev"
            shift
            ;;
        --prod)
            BUILD_TYPE="prod"
            shift
            ;;
        --push)
            PUSH_IMAGE=true
            shift
            ;;
        --multi-arch)
            MULTI_ARCH=true
            shift
            ;;
        *)
            if [[ -z "$IMAGE_TAG" || "$IMAGE_TAG" == "latest" ]]; then
                IMAGE_TAG="$1"
            fi
            shift
            ;;
    esac
done

# Validate Docker installation
if ! command -v docker &> /dev/null; then
    error "Docker is not installed or not in PATH"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    error "Docker daemon is not running"
    exit 1
fi

# Build image name with registry if provided
FULL_IMAGE_NAME="$IMAGE_NAME:$IMAGE_TAG"
if [[ -n "$REGISTRY" ]]; then
    FULL_IMAGE_NAME="$REGISTRY/$FULL_IMAGE_NAME"
fi

log "Starting Docker build process..."
log "Image: $FULL_IMAGE_NAME"
log "Build Type: $BUILD_TYPE"
log "Platform: $PLATFORM"

# Prepare build arguments
if [[ "$BUILD_TYPE" == "dev" ]]; then
    BUILD_ARGS="$BUILD_ARGS --target application"
    warning "Building development image (includes development tools)"
else
    BUILD_ARGS="$BUILD_ARGS --target production"
    log "Building production image (optimized for deployment)"
fi

# Add cache arguments
if [[ "$NO_CACHE" == "true" ]]; then
    BUILD_ARGS="$BUILD_ARGS --no-cache"
    warning "Building without cache"
else
    if [[ -n "$CACHE_FROM" ]]; then
        BUILD_ARGS="$BUILD_ARGS --cache-from $CACHE_FROM"
        log "Using cache from: $CACHE_FROM"
    fi
fi

# Add platform arguments for multi-architecture builds
if [[ "$MULTI_ARCH" == "true" ]]; then
    if ! docker buildx version &> /dev/null; then
        error "Docker Buildx is required for multi-architecture builds"
        exit 1
    fi
    
    log "Building for multiple architectures: $PLATFORM"
    BUILD_COMMAND="docker buildx build --platform $PLATFORM"
    
    if [[ "$PUSH_IMAGE" == "true" ]]; then
        BUILD_ARGS="$BUILD_ARGS --push"
    else
        BUILD_ARGS="$BUILD_ARGS --load"
        warning "Multi-arch build will only load the image for current platform"
    fi
else
    BUILD_COMMAND="docker build"
fi

# Add build metadata
BUILD_ARGS="$BUILD_ARGS --label org.opencontainers.image.created=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
BUILD_ARGS="$BUILD_ARGS --label org.opencontainers.image.version=$IMAGE_TAG"
BUILD_ARGS="$BUILD_ARGS --label org.opencontainers.image.title='User Behavior Analytics Platform'"
BUILD_ARGS="$BUILD_ARGS --label org.opencontainers.image.description='Multi-agent analytics platform for GA4 data analysis'"

# Execute build
log "Executing build command..."
echo "Command: $BUILD_COMMAND $BUILD_ARGS -t $FULL_IMAGE_NAME ."

if $BUILD_COMMAND $BUILD_ARGS -t "$FULL_IMAGE_NAME" .; then
    success "Docker image built successfully: $FULL_IMAGE_NAME"
    
    # Show image information
    if [[ "$MULTI_ARCH" != "true" || "$PUSH_IMAGE" != "true" ]]; then
        log "Image information:"
        docker images "$FULL_IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    fi
    
    # Push image if requested and not multi-arch (multi-arch pushes automatically)
    if [[ "$PUSH_IMAGE" == "true" && "$MULTI_ARCH" != "true" ]]; then
        if [[ -z "$REGISTRY" ]]; then
            warning "No registry specified, skipping push"
        else
            log "Pushing image to registry..."
            if docker push "$FULL_IMAGE_NAME"; then
                success "Image pushed successfully: $FULL_IMAGE_NAME"
            else
                error "Failed to push image"
                exit 1
            fi
        fi
    fi
    
    # Provide usage instructions
    echo
    success "Build completed successfully!"
    echo
    echo "To run the container:"
    echo "  docker run -d -p 8501:8501 --name analytics-platform \\"
    echo "    -e GOOGLE_API_KEY=your_google_key \\"
    echo "    -e ARK_API_KEY=your_ark_key \\"
    echo "    -v analytics-data:/app/data \\"
    echo "    -v analytics-reports:/app/reports \\"
    echo "    $FULL_IMAGE_NAME"
    echo
    echo "To run with Docker Compose:"
    echo "  docker-compose up -d"
    
else
    error "Docker build failed"
    exit 1
fi