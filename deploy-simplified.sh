#!/bin/bash

# Simplified Deployment Script
# Alternative deployment methods when Docker build fails

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    local level=$1
    shift
    local message="$*"
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $level:${NC} $message"
}

show_options() {
    echo "Simplified Deployment Options:"
    echo "1. Direct Python execution (no Docker)"
    echo "2. Use alternative Dockerfile with Chinese mirrors"
    echo "3. Use pre-built base image"
    echo "4. Development mode with local installation"
    echo ""
    read -p "Choose deployment method (1-4): " choice
    
    case $choice in
        1) deploy_direct ;;
        2) deploy_alternative ;;
        3) deploy_prebuilt ;;
        4) deploy_development ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac
}

# Option 1: Direct Python execution
deploy_direct() {
    print_status "INFO" "Starting direct Python deployment..."
    
    # Check Python version
    if ! python3 --version | grep -q "3.1[1-9]"; then
        print_status "WARN" "Python 3.11+ recommended"
    fi
    
    # Install dependencies
    print_status "INFO" "Installing Python dependencies..."
    pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
    
    # Create directories
    mkdir -p data/{development,production}/{uploads,processed}
    mkdir -p reports/{development,production}
    mkdir -p logs/{development,production}
    
    # Set environment
    export PYTHONPATH="$(pwd):$PYTHONPATH"
    export LOG_LEVEL="INFO"
    
    # Start application
    print_status "INFO" "Starting application directly..."
    python3 main.py
}

# Option 2: Alternative Dockerfile
deploy_alternative() {
    print_status "INFO" "Using alternative Dockerfile with Chinese mirrors..."
    
    # Build with alternative Dockerfile
    docker build -f Dockerfile.alternative -t analytics-platform:latest .
    
    # Run with docker-compose
    if [ -f docker-compose.dev.yml ]; then
        docker-compose -f docker-compose.dev.yml up -d
    else
        docker run -d \
            --name analytics-platform \
            -p 8501:8501 \
            -p 8502:8502 \
            -v "$(pwd)/data:/app/data" \
            -v "$(pwd)/reports:/app/reports" \
            -v "$(pwd)/logs:/app/logs" \
            analytics-platform:latest
    fi
    
    print_status "INFO" "Application started with alternative build"
}

# Option 3: Pre-built base image
deploy_prebuilt() {
    print_status "INFO" "Using pre-built base image approach..."
    
    # Create minimal Dockerfile using pre-built Python image
    cat > Dockerfile.minimal << 'EOF'
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Copy requirements and install with Chinese mirror
COPY requirements.txt .
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# Copy application
COPY . .

# Create directories
RUN mkdir -p data/development/{uploads,processed} reports logs

EXPOSE 8501
CMD ["python3", "main.py"]
EOF
    
    # Build with minimal Dockerfile
    docker build -f Dockerfile.minimal -t analytics-platform:minimal .
    
    # Run container
    docker run -d \
        --name analytics-platform \
        -p 8501:8501 \
        -v "$(pwd)/data:/app/data" \
        analytics-platform:minimal
    
    print_status "INFO" "Application started with minimal build"
}

# Option 4: Development mode
deploy_development() {
    print_status "INFO" "Setting up development environment..."
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies with Chinese mirror
    pip install --upgrade pip
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
    
    # Create .env file if not exists
    if [ ! -f .env ]; then
        cp .env.example .env
        print_status "INFO" "Created .env file from template"
        print_status "WARN" "Please edit .env file with your API keys"
    fi
    
    # Create directories
    mkdir -p data/development/{uploads,processed}
    mkdir -p reports/development
    mkdir -p logs/development
    
    # Start development server
    print_status "INFO" "Starting development server..."
    export PYTHONPATH="$(pwd):$PYTHONPATH"
    python3 -m streamlit run main.py --server.port 8501
}

# Check if running from correct directory
if [ ! -f "requirements.txt" ]; then
    print_status "ERROR" "Please run from project root directory"
    exit 1
fi

# Main execution
print_status "INFO" "ZenGrowth Simplified Deployment"
print_status "INFO" "Bypassing Docker build issues"
echo ""

show_options

