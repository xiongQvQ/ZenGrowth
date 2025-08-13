#!/bin/bash
set -e

# ================================
# User Behavior Analytics Platform
# Container Entry Point Script
# Enhanced version with robust configuration handling
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
HEALTH_CHECK_PID=""
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
    
    # Stop health check server if running
    if [ -n "$HEALTH_CHECK_PID" ]; then
        log "INFO" "Stopping health check server (PID: $HEALTH_CHECK_PID)..."
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
    
    # Use the configuration validator if available
    if command -v python3 >/dev/null 2>&1 && [ -f "/app/config_validator.py" ]; then
        log "DEBUG" "Running comprehensive configuration validation..."
        
        if python3 /app/config_validator.py 2>/tmp/validation_output.log; then
            log "INFO" "Configuration validation passed"
            
            # Show validation info if available
            if [ -s /tmp/validation_output.log ]; then
                log "DEBUG" "Validation details:"
                cat /tmp/validation_output.log | while read -r line; do
                    if [[ "$line" == *"Information:"* ]] || [[ "$line" == *"ℹ️"* ]]; then
                        log "DEBUG" "$line"
                    fi
                done
            fi
            
            rm -f /tmp/validation_output.log
            return 0
        else
            log "ERROR" "Configuration validation failed"
            
            if [ -s /tmp/validation_output.log ]; then
                cat /tmp/validation_output.log | while read -r line; do
                    if [[ "$line" == *"Error"* ]] || [[ "$line" == *"❌"* ]]; then
                        log "ERROR" "$line"
                    elif [[ "$line" == *"Warning"* ]] || [[ "$line" == *"⚠️"* ]]; then
                        log "WARN" "$line"
                    fi
                done
            fi
            
            rm -f /tmp/validation_output.log
            return 1
        fi
    else
        log "WARN" "config_validator.py not available, using basic validation"
        
        # Basic validation fallback
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
        
        if [ $validation_errors -gt 0 ]; then
            log "ERROR" "Environment validation failed with $validation_errors errors"
            return 1
        fi
        
        log "INFO" "Basic environment validation completed successfully"
        return 0
    fi
}

# Function to load environment variables from .env file
load_env_file() {
    local env_file="${1:-.env}"
    
    if [ -f "$env_file" ]; then
        log "INFO" "Loading environment variables from $env_file"
        
        # Use the dedicated configuration validator
        if command -v python3 >/dev/null 2>&1 && [ -f "/app/config_validator.py" ]; then
            log "DEBUG" "Using config_validator.py for environment parsing"
            
            # Run the configuration validator
            if python3 /app/config_validator.py --load-env "$env_file" --export-shell > /tmp/env_vars.sh 2>/tmp/env_errors.log; then
                # Check for parsing warnings
                if [ -s /tmp/env_errors.log ]; then
                    log "WARN" "Environment parsing warnings:"
                    cat /tmp/env_errors.log | while read -r line; do
                        if [[ "$line" == *"Warning:"* ]] || [[ "$line" == *"Error:"* ]]; then
                            log "WARN" "$line"
                        fi
                    done
                fi
                
                # Source the parsed environment variables
                if [ -f /tmp/env_vars.sh ] && [ -s /tmp/env_vars.sh ]; then
                    source /tmp/env_vars.sh
                    log "INFO" "Environment variables loaded and validated from $env_file"
                else
                    log "ERROR" "Failed to generate environment variables"
                    rm -f /tmp/env_vars.sh /tmp/env_errors.log
                    return 1
                fi
                
                # Cleanup
                rm -f /tmp/env_vars.sh /tmp/env_errors.log
            else
                log "ERROR" "Configuration validation failed"
                if [ -s /tmp/env_errors.log ]; then
                    cat /tmp/env_errors.log | while read -r line; do
                        log "ERROR" "$line"
                    done
                fi
                rm -f /tmp/env_vars.sh /tmp/env_errors.log
                return 1
            fi
        else
            log "WARN" "config_validator.py not available, using basic .env parsing"
            # Fallback to basic parsing
            while IFS='=' read -r key value; do
                if [[ ! -z "$key" && ! "$key" =~ ^[[:space:]]*# ]]; then
                    # Remove quotes
                    value=$(echo "$value" | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/")
                    export "$key"="$value"
                fi
            done < "$env_file"
            log "INFO" "Environment variables loaded using basic parsing"
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
    
    # API configuration defaults
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

# Function to start health check server
start_health_check_server() {
    log "INFO" "Starting health check server on port $HEALTH_CHECK_PORT..."
    
    # Use the existing healthcheck.py if available
    if [ -f "/app/healthcheck.py" ]; then
        log "DEBUG" "Using existing healthcheck.py for health check server"
        
        # Start health check server using Python HTTP server
        python3 -c "
import http.server
import socketserver
import json
import subprocess
import sys
from datetime import datetime

class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_basic_health()
        elif self.path == '/health/detailed':
            self.send_detailed_health()
        elif self.path == '/version':
            self.send_version()
        else:
            self.send_response(404)
            self.end_headers()
    
    def send_basic_health(self):
        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'user-behavior-analytics-platform'
        }
        self.send_json_response(health)
    
    def send_detailed_health(self):
        try:
            # Run the detailed health check
            result = subprocess.run([
                'python3', '/app/healthcheck.py', '--json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                health_data = json.loads(result.stdout)
                self.send_json_response(health_data)
            else:
                error_health = {
                    'status': 'unhealthy',
                    'timestamp': datetime.now().isoformat(),
                    'error': 'Health check failed',
                    'details': result.stderr
                }
                self.send_json_response(error_health, status=500)
        except Exception as e:
            error_health = {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
            self.send_json_response(error_health, status=500)
    
    def send_version(self):
        version = {
            'service': 'user-behavior-analytics-platform',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        }
        self.send_json_response(version)
    
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def log_message(self, format, *args):
        pass  # Suppress default logging

try:
    with socketserver.TCPServer(('', $HEALTH_CHECK_PORT), HealthCheckHandler) as httpd:
        httpd.serve_forever()
except Exception as e:
    print(f'Health check server failed: {e}')
    sys.exit(1)
" &
        
        HEALTH_CHECK_PID=$!
        log "INFO" "Health check server started (PID: $HEALTH_CHECK_PID)"
        
        # Wait a moment to ensure server starts
        sleep 2
        
        # Test health check server
        if curl -f "http://localhost:$HEALTH_CHECK_PORT/health" >/dev/null 2>&1; then
            log "INFO" "Health check server is responding"
        else
            log "WARN" "Health check server may not be responding properly"
        fi
    else
        log "WARN" "healthcheck.py not found, health check server disabled"
    fi
}

# Function to test API connectivity
test_api_connectivity() {
    log "INFO" "Testing API connectivity..."
    
    # We'll skip actual API testing in the entry point to avoid delays
    # The application will handle API testing during startup
    if [ -n "$GOOGLE_API_KEY" ]; then
        log "INFO" "Google API key configured, connectivity will be tested by application"
    fi
    
    if [ -n "$ARK_API_KEY" ]; then
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
        
        # Check if health check server is still running
        if [ -n "$HEALTH_CHECK_PID" ] && ! kill -0 "$HEALTH_CHECK_PID" 2>/dev/null; then
            log "WARN" "Health check server has died, restarting..."
            start_health_check_server
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
    
    # Step 5: Start health check server
    start_health_check_server
    
    # Step 6: Start Streamlit application
    if ! start_streamlit; then
        log "ERROR" "Failed to start Streamlit application, exiting..."
        exit 1
    fi
    
    log "INFO" "================================"
    log "INFO" "Application startup completed successfully!"
    log "INFO" "Streamlit UI: http://$STREAMLIT_SERVER_ADDRESS:$STREAMLIT_SERVER_PORT"
    log "INFO" "Health Check: http://localhost:$HEALTH_CHECK_PORT/health"
    log "INFO" "Detailed Health: http://localhost:$HEALTH_CHECK_PORT/health/detailed"
    log "INFO" "Version Info: http://localhost:$HEALTH_CHECK_PORT/version"
    log "INFO" "================================"
    
    # Step 7: Monitor application
    monitor_application
}

# Execute main function
main "$@"