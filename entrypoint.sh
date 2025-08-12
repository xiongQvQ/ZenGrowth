#!/bin/bash
set -e

# ================================
# User Behavior Analytics Platform
# Container Entry Point Script
# ================================

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables
SCRIPT_PID=$$
STREAMLIT_PID=""
HEALTH_CHECK_PORT=8502

# Function to log messages with timestamp
log() {
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
            if [ "${LOG_LEVEL:-INFO}" = "DEBUG" ]; then
                echo -e "${BLUE}[${timestamp}] DEBUG:${NC} $message"
            fi
            ;;
        *)
            echo -e "[${timestamp}] $level: $message"
            ;;
    esac
}

# Function to handle graceful shutdown
graceful_shutdown() {
    log "INFO" "Received shutdown signal, initiating graceful shutdown..."
    
    # Stop monitoring service if running
    if [ -n "$HEALTH_CHECK_PID" ]; then
        log "INFO" "Stopping enhanced monitoring service (PID: $HEALTH_CHECK_PID)..."
        kill -TERM "$HEALTH_CHECK_PID" 2>/dev/null || true
        wait "$HEALTH_CHECK_PID" 2>/dev/null || true
    fi
    
    # Stop Streamlit application
    if [ -n "$STREAMLIT_PID" ]; then
        log "INFO" "Stopping Streamlit application (PID: $STREAMLIT_PID)..."
        kill -TERM "$STREAMLIT_PID" 2>/dev/null || true
        
        # Wait for graceful shutdown with timeout
        local timeout=30
        local count=0
        while kill -0 "$STREAMLIT_PID" 2>/dev/null && [ $count -lt $timeout ]; do
            sleep 1
            count=$((count + 1))
        done
        
        # Force kill if still running
        if kill -0 "$STREAMLIT_PID" 2>/dev/null; then
            log "WARN" "Streamlit did not shutdown gracefully, forcing termination..."
            kill -KILL "$STREAMLIT_PID" 2>/dev/null || true
        fi
    fi
    
    log "INFO" "Graceful shutdown completed"
    exit 0
}

# Function to validate environment variables
validate_environment() {
    log "INFO" "Validating environment configuration..."
    
    local validation_errors=0
    
    # Check for at least one API key
    if [ -z "$GOOGLE_API_KEY" ] && [ -z "$ARK_API_KEY" ]; then
        log "ERROR" "At least one API key must be provided (GOOGLE_API_KEY or ARK_API_KEY)"
        validation_errors=$((validation_errors + 1))
    else
        if [ -n "$GOOGLE_API_KEY" ]; then
            log "INFO" "Google API key configured"
        fi
        if [ -n "$ARK_API_KEY" ]; then
            log "INFO" "Volcano ARK API key configured"
        fi
    fi
    
    # Validate port number
    local port=${STREAMLIT_SERVER_PORT:-8501}
    if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1024 ] || [ "$port" -gt 65535 ]; then
        log "ERROR" "Invalid port number: $port (must be between 1024-65535)"
        validation_errors=$((validation_errors + 1))
    fi
    
    # Validate memory settings
    local max_upload=${STREAMLIT_SERVER_MAX_UPLOAD_SIZE:-100}
    if ! [[ "$max_upload" =~ ^[0-9]+$ ]] || [ "$max_upload" -lt 1 ] || [ "$max_upload" -gt 1000 ]; then
        log "WARN" "Max upload size $max_upload MB may be too large or small"
    fi
    
    # Check log level
    local log_level=${LOG_LEVEL:-INFO}
    case $log_level in
        DEBUG|INFO|WARN|ERROR)
            log "DEBUG" "Log level set to: $log_level"
            ;;
        *)
            log "WARN" "Invalid log level '$log_level', defaulting to INFO"
            export LOG_LEVEL="INFO"
            ;;
    esac
    
    if [ $validation_errors -gt 0 ]; then
        log "ERROR" "Environment validation failed with $validation_errors errors"
        return 1
    fi
    
    log "INFO" "Environment validation completed successfully"
    return 0
}

# Function to load environment variables from .env file
load_env_file() {
    local env_file="${1:-.env}"
    
    if [ -f "$env_file" ]; then
        log "INFO" "Loading environment variables from $env_file"
        
        # Use Python to properly parse .env file with JSON arrays
        if command -v python3 >/dev/null 2>&1; then
            # Export variables using Python parser
            eval $(python3 -c "
import os
import sys
from pathlib import Path

env_file = Path('$env_file')
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if (value.startswith('\"') and value.endswith('\"')) or (value.startswith(\"'\") and value.endswith(\"'\")):
                    value = value[1:-1]
                # Escape special characters for shell
                value = value.replace('\"', '\\\"').replace('\$', '\\\$')
                print(f'export {key}=\"{value}\"')
")
            log "INFO" "Environment variables loaded from $env_file"
        else
            log "WARN" "Python3 not available, using basic .env parsing"
            # Fallback to basic parsing
            while IFS='=' read -r key value; do
                if [[ ! -z "$key" && ! "$key" =~ ^[[:space:]]*# ]]; then
                    # Remove quotes
                    value=$(echo "$value" | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/")
                    export "$key"="$value"
                fi
            done < "$env_file"
        fi
    else
        log "DEBUG" "Environment file $env_file not found, using defaults"
    fi
}

# Function to set default environment variables
set_default_environment() {
    log "INFO" "Setting default environment variables..."
    
    # First try to load from .env file
    load_env_file "/app/.env"
    
    # Then set defaults for any missing variables
    # Streamlit configuration
    export STREAMLIT_SERVER_HEADLESS=${STREAMLIT_SERVER_HEADLESS:-true}
    export STREAMLIT_SERVER_PORT=${STREAMLIT_SERVER_PORT:-8501}
    export STREAMLIT_SERVER_ADDRESS=${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}
    export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=${STREAMLIT_SERVER_MAX_UPLOAD_SIZE:-100}
    export STREAMLIT_BROWSER_GATHER_USAGE_STATS=${STREAMLIT_BROWSER_GATHER_USAGE_STATS:-false}
    
    # Application configuration
    export LOG_LEVEL=${LOG_LEVEL:-INFO}
    export APP_TITLE=${APP_TITLE:-"用户行为分析智能体平台"}
    
    # API configuration defaults (根据.env文件配置)
    export DEFAULT_LLM_PROVIDER=${DEFAULT_LLM_PROVIDER:-volcano}
    export ENABLED_PROVIDERS=${ENABLED_PROVIDERS:-'["volcano", "google"]'}
    export ENABLE_FALLBACK=${ENABLE_FALLBACK:-true}
    export FALLBACK_ORDER=${FALLBACK_ORDER:-'["volcano", "google"]'}
    export ENABLE_MULTIMODAL=${ENABLE_MULTIMODAL:-true}
    export MAX_IMAGE_SIZE_MB=${MAX_IMAGE_SIZE_MB:-10}
    
    # LLM model configuration
    export LLM_MODEL=${LLM_MODEL:-gemini-2.5-pro}
    export LLM_TEMPERATURE=${LLM_TEMPERATURE:-0.1}
    export LLM_MAX_TOKENS=${LLM_MAX_TOKENS:-4000}
    
    # Volcano ARK configuration
    export ARK_BASE_URL=${ARK_BASE_URL:-https://ark.cn-beijing.volces.com/api/v3}
    export ARK_MODEL=${ARK_MODEL:-doubao-seed-1-6-250615}
    
    log "DEBUG" "Environment variables configured:"
    log "DEBUG" "  - Streamlit Port: $STREAMLIT_SERVER_PORT"
    log "DEBUG" "  - Streamlit Address: $STREAMLIT_SERVER_ADDRESS"
    log "DEBUG" "  - Max Upload Size: ${STREAMLIT_SERVER_MAX_UPLOAD_SIZE}MB"
    log "DEBUG" "  - Log Level: $LOG_LEVEL"
    log "DEBUG" "  - Default LLM Provider: $DEFAULT_LLM_PROVIDER"
}

# Function to create required directories
create_directories() {
    log "INFO" "Creating required application directories..."
    
    local directories=(
        "/app/data"
        "/app/data/uploads"
        "/app/data/processed"
        "/app/reports"
        "/app/logs"
        "/app/logs/monitoring"
        "/app/config"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            log "DEBUG" "Creating directory: $dir"
            mkdir -p "$dir"
        fi
        
        # Set appropriate permissions
        if [[ "$dir" == *"/uploads"* ]] || [[ "$dir" == *"/processed"* ]] || [[ "$dir" == *"/reports"* ]] || [[ "$dir" == *"/logs"* ]]; then
            chmod 775 "$dir" 2>/dev/null || log "WARN" "Could not set permissions for $dir"
        else
            chmod 755 "$dir" 2>/dev/null || log "WARN" "Could not set permissions for $dir"
        fi
    done
    
    # Verify directory creation and permissions
    local failed_dirs=0
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            log "ERROR" "Failed to create directory: $dir"
            failed_dirs=$((failed_dirs + 1))
        elif [ ! -w "$dir" ]; then
            log "WARN" "Directory not writable: $dir"
        else
            log "DEBUG" "Directory ready: $dir"
        fi
    done
    
    if [ $failed_dirs -gt 0 ]; then
        log "ERROR" "Failed to create $failed_dirs required directories"
        return 1
    fi
    
    log "INFO" "All required directories created successfully"
    return 0
}

# Function to start enhanced monitoring service
start_monitoring_service() {
    log "INFO" "Starting enhanced monitoring service on port $HEALTH_CHECK_PORT..."

    # Start the enhanced monitoring service using our monitoring_endpoints.py
    python3 /app/monitoring_endpoints.py --port $HEALTH_CHECK_PORT --host 0.0.0.0 &

    HEALTH_CHECK_PID=$!
    log "INFO" "Enhanced monitoring service started (PID: $HEALTH_CHECK_PID)"

    # Wait a moment to ensure server starts
    sleep 5

    # Test monitoring service endpoints
    local endpoints=("/health" "/metrics" "/status")
    local working_endpoints=0

    for endpoint in "${endpoints[@]}"; do
        if curl -f "http://localhost:$HEALTH_CHECK_PORT$endpoint" >/dev/null 2>&1; then
            log "DEBUG" "Monitoring endpoint responding: $endpoint"
            working_endpoints=$((working_endpoints + 1))
        else
            log "WARN" "Monitoring endpoint not responding: $endpoint"
        fi
    done

    if [ $working_endpoints -gt 0 ]; then
        log "INFO" "Enhanced monitoring service is responding ($working_endpoints/${#endpoints[@]} endpoints)"
        log "INFO" "Available monitoring endpoints:"
        log "INFO" "  - Health Check: http://localhost:$HEALTH_CHECK_PORT/health"
        log "INFO" "  - Detailed Health: http://localhost:$HEALTH_CHECK_PORT/health/detailed"
        log "INFO" "  - Prometheus Metrics: http://localhost:$HEALTH_CHECK_PORT/metrics"
        log "INFO" "  - JSON Metrics: http://localhost:$HEALTH_CHECK_PORT/metrics/json"
        log "INFO" "  - System Status: http://localhost:$HEALTH_CHECK_PORT/status"
        log "INFO" "  - Version Info: http://localhost:$HEALTH_CHECK_PORT/version"
        log "INFO" "  - API Connectivity: http://localhost:$HEALTH_CHECK_PORT/api/connectivity"
    else
        log "WARN" "Enhanced monitoring service may not be responding properly"
    fi
}

# Function to test API connectivity
test_api_connectivity() {
    log "INFO" "Testing API connectivity..."
    
    local connectivity_ok=true
    
    # Test Google API if key is provided
    if [ -n "$GOOGLE_API_KEY" ]; then
        log "DEBUG" "Testing Google Gemini API connectivity..."
        # We'll skip actual API testing in the entry point to avoid delays
        # The application will handle API testing during startup
        log "INFO" "Google API key configured, connectivity will be tested by application"
    fi
    
    # Test Volcano ARK API if key is provided
    if [ -n "$ARK_API_KEY" ]; then
        log "DEBUG" "Testing Volcano ARK API connectivity..."
        # We'll skip actual API testing in the entry point to avoid delays
        # The application will handle API testing during startup
        log "INFO" "Volcano ARK API key configured, connectivity will be tested by application"
    fi
    
    return 0
}

# Function to start Streamlit application
start_streamlit() {
    log "INFO" "Starting Streamlit application..."
    
    local streamlit_args=(
        "run" "main.py"
        "--server.headless=$STREAMLIT_SERVER_HEADLESS"
        "--server.port=$STREAMLIT_SERVER_PORT"
        "--server.address=$STREAMLIT_SERVER_ADDRESS"
        "--server.maxUploadSize=$STREAMLIT_SERVER_MAX_UPLOAD_SIZE"
        "--browser.gatherUsageStats=$STREAMLIT_BROWSER_GATHER_USAGE_STATS"
        "--server.enableCORS=false"
        "--server.enableXsrfProtection=false"
    )
    
    log "DEBUG" "Streamlit command: streamlit ${streamlit_args[*]}"
    
    # Start Streamlit in background
    streamlit "${streamlit_args[@]}" &
    STREAMLIT_PID=$!
    
    log "INFO" "Streamlit application started (PID: $STREAMLIT_PID)"
    log "INFO" "Application will be available at http://$STREAMLIT_SERVER_ADDRESS:$STREAMLIT_SERVER_PORT"
    
    # Wait for Streamlit to start
    local timeout=60
    local count=0
    while [ $count -lt $timeout ]; do
        if curl -f "http://localhost:$STREAMLIT_SERVER_PORT/_stcore/health" >/dev/null 2>&1; then
            log "INFO" "Streamlit application is ready and responding"
            return 0
        fi
        sleep 2
        count=$((count + 2))
        
        # Check if process is still running
        if ! kill -0 "$STREAMLIT_PID" 2>/dev/null; then
            log "ERROR" "Streamlit process died during startup"
            return 1
        fi
    done
    
    log "WARN" "Streamlit application may not be fully ready yet (timeout after ${timeout}s)"
    return 0
}

# Function to monitor application
monitor_application() {
    log "INFO" "Starting application monitoring..."
    
    while true; do
        # Check if Streamlit is still running
        if ! kill -0 "$STREAMLIT_PID" 2>/dev/null; then
            log "ERROR" "Streamlit process has died, initiating shutdown..."
            graceful_shutdown
        fi
        
        # Check if monitoring service is still running
        if [ -n "$HEALTH_CHECK_PID" ] && ! kill -0 "$HEALTH_CHECK_PID" 2>/dev/null; then
            log "WARN" "Enhanced monitoring service has died, restarting..."
            start_monitoring_service
        fi
        
        sleep 30
    done
}

# Main execution function
main() {
    log "INFO" "================================"
    log "INFO" "User Behavior Analytics Platform"
    log "INFO" "Container Entry Point v1.0.0"
    log "INFO" "================================"
    
    # Set up signal handlers for graceful shutdown
    trap graceful_shutdown SIGTERM SIGINT SIGQUIT
    
    # Step 1: Set default environment variables
    set_default_environment
    
    # Step 2: Validate environment
    if ! validate_environment; then
        log "ERROR" "Environment validation failed, exiting..."
        exit 1
    fi
    
    # Step 3: Create required directories
    if ! create_directories; then
        log "ERROR" "Directory creation failed, exiting..."
        exit 1
    fi
    
    # Step 4: Test API connectivity (basic check)
    test_api_connectivity
    
    # Step 5: Start enhanced monitoring service
    start_monitoring_service
    
    # Step 6: Start Streamlit application
    if ! start_streamlit; then
        log "ERROR" "Failed to start Streamlit application, exiting..."
        exit 1
    fi
    
    log "INFO" "================================"
    log "INFO" "Application startup completed successfully!"
    log "INFO" "Streamlit UI: http://$STREAMLIT_SERVER_ADDRESS:$STREAMLIT_SERVER_PORT"
    log "INFO" "Enhanced Monitoring Service: http://localhost:$HEALTH_CHECK_PORT"
    log "INFO" "  - Health Check: http://localhost:$HEALTH_CHECK_PORT/health"
    log "INFO" "  - Detailed Health: http://localhost:$HEALTH_CHECK_PORT/health/detailed"
    log "INFO" "  - Prometheus Metrics: http://localhost:$HEALTH_CHECK_PORT/metrics"
    log "INFO" "  - System Status: http://localhost:$HEALTH_CHECK_PORT/status"
    log "INFO" "  - Version Info: http://localhost:$HEALTH_CHECK_PORT/version"
    log "INFO" "  - API Connectivity: http://localhost:$HEALTH_CHECK_PORT/api/connectivity"
    log "INFO" "================================"
    
    # Step 7: Monitor application
    monitor_application
}

# Execute main function
main "$@"