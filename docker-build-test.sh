#!/bin/bash

# Docker Build Test Script
# Tests different build strategies for connectivity issues

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${GREEN}[${timestamp}] INFO:${NC} $message"
            ;;
        "WARN")
            echo -e "${YELLOW}[${timestamp}] WARN:${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[${timestamp}] ERROR:${NC} $message"
            ;;
        "DEBUG")
            echo -e "${BLUE}[${timestamp}] DEBUG:${NC} $message"
            ;;
    esac
}

# Test Docker connectivity
test_docker() {
    print_status "INFO" "Testing Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_status "ERROR" "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_status "ERROR" "Docker is not running"
        exit 1
    fi
    
    print_status "INFO" "Docker is available"
}

# Test network connectivity
test_connectivity() {
    print_status "INFO" "Testing network connectivity..."
    
    # Test default Debian mirrors
    if curl -s --connect-timeout 10 http://deb.debian.org > /dev/null; then
        print_status "INFO" "Default Debian mirrors accessible"
        return 0
    else
        print_status "WARN" "Default Debian mirrors not accessible"
    fi
    
    # Test Chinese mirrors
    if curl -s --connect-timeout 10 http://mirrors.tuna.tsinghua.edu.cn > /dev/null; then
        print_status "INFO" "Chinese mirrors accessible"
        return 0
    else
        print_status "WARN" "Chinese mirrors not accessible"
    fi
    
    print_status "ERROR" "Network connectivity issues detected"
    return 1
}

# Build with original Dockerfile
build_original() {
    print_status "INFO" "Attempting build with original Dockerfile..."
    
    if docker build --no-cache -t analytics-platform:original . ; then
        print_status "INFO" "Original Dockerfile build successful"
        return 0
    else
        print_status "WARN" "Original Dockerfile build failed"
        return 1
    fi
}

# Build with alternative Dockerfile
build_alternative() {
    print_status "INFO" "Attempting build with alternative Dockerfile (Chinese mirrors)..."
    
    if docker build --no-cache -f Dockerfile.alternative -t analytics-platform:alternative . ; then
        print_status "INFO" "Alternative Dockerfile build successful"
        return 0
    else
        print_status "WARN" "Alternative Dockerfile build failed"
        return 1
    fi
}

# Build without network cache
build_no_cache() {
    print_status "INFO" "Attempting build with fresh package cache..."
    
    if docker build --no-cache --pull -t analytics-platform:no-cache . ; then
        print_status "INFO" "No-cache build successful"
        return 0
    else
        print_status "WARN" "No-cache build failed"
        return 1
    fi
}

# Main execution
main() {
    print_status "INFO" "Starting Docker build troubleshooting..."
    
    # Test prerequisites
    test_docker
    test_connectivity
    
    # Try different build strategies
    BUILD_SUCCESS=false
    
    # Strategy 1: Try original Dockerfile
    if build_original; then
        BUILD_SUCCESS=true
        SUCCESSFUL_METHOD="original"
    fi
    
    # Strategy 2: Try alternative Dockerfile with Chinese mirrors
    if [ "$BUILD_SUCCESS" = false ] && build_alternative; then
        BUILD_SUCCESS=true
        SUCCESSFUL_METHOD="alternative"
    fi
    
    # Strategy 3: Try no-cache build
    if [ "$BUILD_SUCCESS" = false ] && build_no_cache; then
        BUILD_SUCCESS=true
        SUCCESSFUL_METHOD="no-cache"
    fi
    
    # Report results
    if [ "$BUILD_SUCCESS" = true ]; then
        print_status "INFO" "Build successful using: $SUCCESSFUL_METHOD"
        print_status "INFO" "You can now deploy using:"
        case $SUCCESSFUL_METHOD in
            "original")
                echo "./deploy.sh -e development -a up -b"
                ;;
            "alternative")
                echo "docker build -f Dockerfile.alternative -t analytics-platform:latest ."
                echo "docker-compose up -d"
                ;;
            "no-cache")
                echo "./deploy.sh -e development -a up -b"
                ;;
        esac
    else
        print_status "ERROR" "All build strategies failed"
        print_status "INFO" "Consider trying the pre-built image option below"
    fi
}

# Execute main function
main "$@"

