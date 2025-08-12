# Container Entry Point Implementation

This document describes the comprehensive container entry point implementation for the User Behavior Analytics Platform.

## Overview

The entry point system consists of several components that work together to provide:

- **Environment validation and configuration loading**
- **Graceful shutdown handling**
- **Health check endpoints**
- **Automatic directory creation**
- **Application monitoring**
- **Comprehensive logging**

## Components

### 1. Main Entry Point Script (`entrypoint.sh`)

The main entry point script that orchestrates the container startup process.

**Features:**
- Environment variable validation
- Default configuration setup
- Required directory creation
- Health check server startup
- Streamlit application launch
- Application monitoring
- Graceful shutdown handling

**Usage:**
```bash
# Direct execution
./entrypoint.sh

# In Docker container (automatic)
docker run analytics-platform
```

### 2. Configuration Validator (`config_validator.py`)

Validates all environment variables and configuration settings.

**Features:**
- API key validation
- Streamlit configuration validation
- LLM provider configuration validation
- Directory structure validation
- Multimodal configuration validation

**Usage:**
```bash
# Validate current environment
python3 config_validator.py

# Get JSON output
python3 config_validator.py --json
```

### 3. Health Check Script (`healthcheck.py`)

Comprehensive health checking for the containerized application.

**Features:**
- Streamlit application health
- Environment configuration health
- Directory structure health
- System resource monitoring
- Process monitoring

**Usage:**
```bash
# Basic health check
python3 healthcheck.py

# JSON output
python3 healthcheck.py --json

# Docker health check (automatic)
HEALTHCHECK CMD python3 /app/healthcheck.py
```

### 4. Startup Monitor (`startup_monitor.py`)

Monitors the application startup process and provides detailed status information.

**Features:**
- Process startup monitoring
- Streamlit readiness checking
- Health endpoint verification
- Startup time measurement
- Detailed status reporting

**Usage:**
```bash
# Monitor startup with defaults
python3 startup_monitor.py

# Custom configuration
python3 startup_monitor.py --streamlit-port 8501 --health-port 8502 --timeout 120

# JSON output
python3 startup_monitor.py --json
```

## Environment Variables

### Required Variables

At least one API key must be provided:

```bash
# Google Gemini API
GOOGLE_API_KEY=your_google_api_key_here

# OR Volcano ARK API
ARK_API_KEY=your_ark_api_key_here
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```

### Optional Variables

```bash
# Streamlit Configuration
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_MAX_UPLOAD_SIZE=100
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Application Configuration
LOG_LEVEL=INFO
APP_TITLE=用户行为分析智能体平台

# LLM Configuration
DEFAULT_LLM_PROVIDER=google
LLM_MODEL=gemini-2.5-pro
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4000

# Volcano ARK Configuration
ARK_MODEL=doubao-seed-1-6-250615

# Provider Management
ENABLED_PROVIDERS=["google", "volcano"]
ENABLE_FALLBACK=true
FALLBACK_ORDER=["google", "volcano"]

# Multimodal Configuration
ENABLE_MULTIMODAL=true
MAX_IMAGE_SIZE_MB=10
SUPPORTED_IMAGE_FORMATS=["jpg", "jpeg", "png", "gif", "webp"]
IMAGE_ANALYSIS_TIMEOUT=60
```

## Directory Structure

The entry point automatically creates the following directories:

```
/app/
├── data/
│   ├── uploads/          # User uploaded files
│   └── processed/        # Processed data files
├── reports/              # Generated reports
├── logs/                 # Application logs
│   └── monitoring/       # Monitoring logs
└── config/               # Configuration files
```

## Health Check Endpoints

The entry point starts a health check server on port 8502 with the following endpoints:

### `/health`
Basic health status
```json
{
  "status": "healthy",
  "timestamp": "2025-01-12T10:30:00Z",
  "service": "user-behavior-analytics-platform"
}
```

### `/health/detailed`
Comprehensive health information
```json
{
  "status": "healthy",
  "timestamp": "2025-01-12T10:30:00Z",
  "service": "user-behavior-analytics-platform",
  "checks": {
    "directories": {"status": "healthy", ...},
    "environment": {"status": "healthy", ...},
    "streamlit": {"status": "healthy", ...}
  }
}
```

### `/version`
Application version information
```json
{
  "service": "user-behavior-analytics-platform",
  "version": "1.0.0",
  "build_date": "2025-01-12T10:30:00Z",
  "python_version": "3.11.0",
  "environment": {...}
}
```

## Graceful Shutdown

The entry point handles the following signals for graceful shutdown:

- `SIGTERM` - Termination signal (Docker stop)
- `SIGINT` - Interrupt signal (Ctrl+C)
- `SIGQUIT` - Quit signal

**Shutdown Process:**
1. Stop health check server
2. Send SIGTERM to Streamlit process
3. Wait up to 30 seconds for graceful shutdown
4. Force kill if necessary
5. Clean up and exit

## Logging

All components use structured logging with timestamps:

```
[2025-01-12 10:30:00] [  15.2s] INFO: Starting Streamlit application...
[2025-01-12 10:30:05] [  20.1s] INFO: Application startup completed successfully!
```

**Log Levels:**
- `DEBUG` - Detailed debugging information
- `INFO` - General information messages
- `WARN` - Warning messages (non-critical issues)
- `ERROR` - Error messages (critical issues)

## Testing

### Unit Tests

Run the entry point test suite:

```bash
python3 test_entrypoint.py
```

### Integration Tests

Test with Docker Compose:

```bash
# Build and start test container
docker-compose -f docker-compose.test.yml up --build

# Check health
curl http://localhost:8502/health

# Check detailed health
curl http://localhost:8502/health/detailed

# Check Streamlit
curl http://localhost:8501/_stcore/health
```

### Manual Testing

Test individual components:

```bash
# Test configuration validation
GOOGLE_API_KEY=test_key python3 config_validator.py

# Test health check
python3 healthcheck.py

# Test startup monitoring (will timeout without running app)
python3 startup_monitor.py --timeout 10
```

## Troubleshooting

### Common Issues

**1. API Key Validation Fails**
```bash
# Check if API keys are set
echo $GOOGLE_API_KEY
echo $ARK_API_KEY

# Validate configuration
python3 config_validator.py
```

**2. Directory Permission Issues**
```bash
# Check directory permissions
ls -la /app/data/

# Fix permissions (as root)
chown -R analytics:analytics /app/data/
chmod -R 775 /app/data/
```

**3. Health Check Fails**
```bash
# Check detailed health status
python3 healthcheck.py --json

# Check if Streamlit is running
curl http://localhost:8501/_stcore/health
```

**4. Startup Timeout**
```bash
# Monitor startup process
python3 startup_monitor.py --json

# Check container logs
docker logs <container_id>
```

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
./entrypoint.sh
```

## Security Considerations

1. **Non-root User**: Application runs as `analytics` user (UID 1000)
2. **API Key Protection**: API keys are handled securely through environment variables
3. **Directory Permissions**: Proper file permissions are set automatically
4. **Resource Limits**: Container resource limits prevent resource exhaustion
5. **Signal Handling**: Proper signal handling prevents data corruption

## Performance Optimization

1. **Startup Time**: Optimized startup sequence reduces container start time
2. **Health Checks**: Efficient health checks with appropriate timeouts
3. **Resource Monitoring**: System resource monitoring prevents overload
4. **Graceful Shutdown**: Proper shutdown prevents data loss

## Monitoring Integration

The entry point is designed to work with container orchestration platforms:

- **Docker**: Built-in health checks
- **Kubernetes**: Readiness and liveness probes
- **Docker Swarm**: Service health monitoring
- **Monitoring Systems**: Prometheus-compatible metrics endpoint

## Future Enhancements

Planned improvements:

1. **Metrics Endpoint**: Prometheus metrics for monitoring
2. **Configuration Hot Reload**: Dynamic configuration updates
3. **Advanced Health Checks**: API connectivity verification
4. **Backup Integration**: Automated data backup on startup
5. **Multi-stage Health**: Progressive health check stages