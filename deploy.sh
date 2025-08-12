#!/bin/bash

# =================================
# User Behavior Analytics Platform
# Docker Deployment Script
# =================================

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
ACTION="up"
BUILD_ARGS=""
COMPOSE_FILE=""
ENV_FILE=""

# Function to print colored output
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
        *)
            echo -e "[${timestamp}] $level: $message"
            ;;
    esac
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Environment: development, production, test (default: development)"
    echo "  -a, --action ACTION      Action: up, down, build, logs, status (default: up)"
    echo "  -b, --build             Force rebuild of images"
    echo "  -d, --detach            Run in detached mode"
    echo "  -f, --follow            Follow logs (only with logs action)"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -e development -a up -b    # Build and start development environment"
    echo "  $0 -e production -a up -d     # Start production environment in detached mode"
    echo "  $0 -e development -a logs -f  # Follow development logs"
    echo "  $0 -e production -a down      # Stop production environment"
    echo ""
}

# Function to validate environment
validate_environment() {
    local env=$1
    
    case $env in
        "development"|"dev")
            ENVIRONMENT="development"
            COMPOSE_FILE="docker-compose.dev.yml"
            ENV_FILE=".env.dev"
            ;;
        "production"|"prod")
            ENVIRONMENT="production"
            COMPOSE_FILE="docker-compose.yml"
            ENV_FILE=".env"
            ;;
        "test")
            ENVIRONMENT="test"
            COMPOSE_FILE="docker-compose.test.yml"
            ENV_FILE=".env.test"
            ;;
        *)
            print_status "ERROR" "Invalid environment: $env"
            print_status "INFO" "Valid environments: development, production, test"
            exit 1
            ;;
    esac
}

# Function to check prerequisites
check_prerequisites() {
    print_status "INFO" "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        print_status "ERROR" "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_status "ERROR" "Docker is not running"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_status "ERROR" "Docker Compose is not available"
        exit 1
    fi
    
    # Check if compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_status "ERROR" "Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Check if environment file exists (warn if missing)
    if [ ! -f "$ENV_FILE" ]; then
        print_status "WARN" "Environment file not found: $ENV_FILE"
        print_status "INFO" "Using default environment variables"
        
        # Suggest creating from example
        local example_file="${ENV_FILE}.example"
        if [ -f "$example_file" ]; then
            print_status "INFO" "You can create $ENV_FILE from $example_file"
            print_status "INFO" "cp $example_file $ENV_FILE"
        fi
    fi
    
    print_status "INFO" "Prerequisites check completed"
}

# Function to create required directories
create_directories() {
    print_status "INFO" "Creating required directories for $ENVIRONMENT environment..."
    
    local base_dirs=("data" "reports" "logs" "config")
    
    for base_dir in "${base_dirs[@]}"; do
        local env_dir="${base_dir}/${ENVIRONMENT}"
        if [ ! -d "$env_dir" ]; then
            print_status "DEBUG" "Creating directory: $env_dir"
            mkdir -p "$env_dir"
        fi
    done
    
    # Create specific subdirectories
    mkdir -p "data/${ENVIRONMENT}/uploads"
    mkdir -p "data/${ENVIRONMENT}/processed"
    mkdir -p "logs/${ENVIRONMENT}/monitoring"
    
    print_status "INFO" "Directories created successfully"
}

# Function to build images
build_images() {
    print_status "INFO" "Building Docker images for $ENVIRONMENT environment..."
    
    local build_cmd="docker-compose -f $COMPOSE_FILE"
    
    if [ -f "$ENV_FILE" ]; then
        build_cmd="$build_cmd --env-file $ENV_FILE"
    fi
    
    build_cmd="$build_cmd build $BUILD_ARGS"
    
    print_status "DEBUG" "Build command: $build_cmd"
    eval $build_cmd
    
    print_status "INFO" "Images built successfully"
}

# Function to start services
start_services() {
    print_status "INFO" "Starting services for $ENVIRONMENT environment..."
    
    local up_cmd="docker-compose -f $COMPOSE_FILE"
    
    if [ -f "$ENV_FILE" ]; then
        up_cmd="$up_cmd --env-file $ENV_FILE"
    fi
    
    up_cmd="$up_cmd up $BUILD_ARGS"
    
    print_status "DEBUG" "Start command: $up_cmd"
    eval $up_cmd
}

# Function to stop services
stop_services() {
    print_status "INFO" "Stopping services for $ENVIRONMENT environment..."
    
    local down_cmd="docker-compose -f $COMPOSE_FILE"
    
    if [ -f "$ENV_FILE" ]; then
        down_cmd="$down_cmd --env-file $ENV_FILE"
    fi
    
    down_cmd="$down_cmd down"
    
    print_status "DEBUG" "Stop command: $down_cmd"
    eval $down_cmd
    
    print_status "INFO" "Services stopped successfully"
}

# Function to show logs
show_logs() {
    print_status "INFO" "Showing logs for $ENVIRONMENT environment..."
    
    local logs_cmd="docker-compose -f $COMPOSE_FILE"
    
    if [ -f "$ENV_FILE" ]; then
        logs_cmd="$logs_cmd --env-file $ENV_FILE"
    fi
    
    logs_cmd="$logs_cmd logs $BUILD_ARGS"
    
    print_status "DEBUG" "Logs command: $logs_cmd"
    eval $logs_cmd
}

# Function to show status
show_status() {
    print_status "INFO" "Showing status for $ENVIRONMENT environment..."
    
    local ps_cmd="docker-compose -f $COMPOSE_FILE"
    
    if [ -f "$ENV_FILE" ]; then
        ps_cmd="$ps_cmd --env-file $ENV_FILE"
    fi
    
    ps_cmd="$ps_cmd ps"
    
    print_status "DEBUG" "Status command: $ps_cmd"
    eval $ps_cmd
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            validate_environment "$2"
            shift 2
            ;;
        -a|--action)
            ACTION="$2"
            shift 2
            ;;
        -b|--build)
            BUILD_ARGS="$BUILD_ARGS --build"
            shift
            ;;
        -d|--detach)
            BUILD_ARGS="$BUILD_ARGS -d"
            shift
            ;;
        -f|--follow)
            BUILD_ARGS="$BUILD_ARGS -f"
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_status "ERROR" "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_status "INFO" "================================"
    print_status "INFO" "Docker Deployment Script"
    print_status "INFO" "Environment: $ENVIRONMENT"
    print_status "INFO" "Action: $ACTION"
    print_status "INFO" "Compose File: $COMPOSE_FILE"
    print_status "INFO" "================================"
    
    # Set default compose file if not set
    if [ -z "$COMPOSE_FILE" ]; then
        validate_environment "$ENVIRONMENT"
    fi
    
    # Check prerequisites
    check_prerequisites
    
    # Create directories
    create_directories
    
    # Execute action
    case $ACTION in
        "up"|"start")
            start_services
            ;;
        "down"|"stop")
            stop_services
            ;;
        "build")
            build_images
            ;;
        "logs")
            show_logs
            ;;
        "status"|"ps")
            show_status
            ;;
        *)
            print_status "ERROR" "Invalid action: $ACTION"
            print_status "INFO" "Valid actions: up, down, build, logs, status"
            exit 1
            ;;
    esac
    
    print_status "INFO" "Deployment script completed successfully"
}

# Execute main function
main "$@"
