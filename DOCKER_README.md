# Docker Setup for User Behavior Analytics Platform

This directory contains Docker configuration files for containerizing the User Behavior Analytics Platform.

## Files Overview

- **Dockerfile**: Multi-stage Docker build configuration
- **.dockerignore**: Excludes unnecessary files from build context
- **docker-build.sh**: Optimized build script with caching and multi-architecture support
- **healthcheck.py**: Health check script for container monitoring

## Quick Start

### 1. Build the Docker Image

```bash
# Simple build
./docker-build.sh

# Build with specific tag
./docker-build.sh v1.0.0

# Build development image
./docker-build.sh --dev

# Build for multiple architectures
./docker-build.sh --multi-arch
```

### 2. Run the Container

```bash
# Basic run with environment variables
docker run -d -p 8501:8501 \
  --name analytics-platform \
  -e GOOGLE_API_KEY=your_google_api_key \
  -e ARK_API_KEY=your_ark_api_key \
  user-behavior-analytics:latest

# Run with volume mounts for data persistence
docker run -d -p 8501:8501 \
  --name analytics-platform \
  -e GOOGLE_API_KEY=your_google_api_key \
  -e ARK_API_KEY=your_ark_api_key \
  -v analytics-data:/app/data \
  -v analytics-reports:/app/reports \
  -v analytics-logs:/app/logs \
  user-behavior-analytics:latest
```

### 3. Health Check

```bash
# Check container health
docker exec analytics-platform python healthcheck.py

# View container logs
docker logs analytics-platform

# Monitor container stats
docker stats analytics-platform
```

## Environment Variables

### Required (at least one API key)
- `GOOGLE_API_KEY`: Google Gemini API key
- `ARK_API_KEY`: Volcano ARK API key

### Optional Configuration
- `STREAMLIT_SERVER_PORT`: Application port (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Bind address (default: 0.0.0.0)
- `STREAMLIT_SERVER_HEADLESS`: Run in headless mode (default: true)
- `STREAMLIT_SERVER_MAX_UPLOAD_SIZE`: Max upload size in MB (default: 100)
- `LOG_LEVEL`: Logging level (default: INFO)
- `DEFAULT_LLM_PROVIDER`: Default LLM provider (default: volcano)
- `ENABLE_MULTIMODAL`: Enable multimodal support (default: true)

### API Provider Configuration
- `ARK_BASE_URL`: Volcano ARK API base URL
- `ARK_MODEL`: Volcano model name
- `LLM_MODEL`: Google Gemini model name
- `LLM_TEMPERATURE`: Model temperature setting
- `LLM_MAX_TOKENS`: Maximum tokens per request

## Volume Mounts

The container uses the following directories that should be mounted for data persistence:

- `/app/data/uploads`: Uploaded GA4 data files
- `/app/data/processed`: Processed data cache
- `/app/reports`: Generated analysis reports
- `/app/logs`: Application logs
- `/app/config`: External configuration files (optional)

## Docker Image Details

### Multi-Stage Build
The Dockerfile uses a 4-stage build process:

1. **Base**: System dependencies and Python runtime
2. **Dependencies**: Python package installation with caching
3. **Application**: Application code and entry point setup
4. **Production**: Minimal runtime image with security optimizations

### Security Features
- Non-root user execution (UID 1000)
- Minimal attack surface with slim base image
- Proper file permissions and ownership
- Health check endpoint for monitoring

### Image Optimization
- Multi-stage build reduces final image size
- Layer caching for faster rebuilds
- .dockerignore excludes unnecessary files
- Virtual environment isolation

## Build Options

### Development Build
```bash
./docker-build.sh --dev
```
- Includes development tools
- Targets application stage
- Suitable for debugging

### Production Build
```bash
./docker-build.sh --prod
```
- Minimal runtime image
- Optimized for deployment
- Security hardened

### Multi-Architecture Build
```bash
./docker-build.sh --multi-arch
```
- Builds for AMD64 and ARM64
- Requires Docker Buildx
- Suitable for cloud deployment

## Troubleshooting

### Common Issues

1. **Build fails with permission errors**
   ```bash
   # Ensure Docker daemon is running
   docker info
   
   # Check file permissions
   ls -la Dockerfile docker-build.sh
   ```

2. **Container fails to start**
   ```bash
   # Check logs
   docker logs analytics-platform
   
   # Run health check
   docker exec analytics-platform python healthcheck.py
   ```

3. **API connection issues**
   ```bash
   # Verify environment variables
   docker exec analytics-platform env | grep -E "(GOOGLE|ARK)_API_KEY"
   
   # Test API connectivity
   docker exec analytics-platform python -c "
   from config.crew_config import get_llm
   llm = get_llm()
   print('LLM provider available')
   "
   ```

4. **File upload issues**
   ```bash
   # Check volume mounts
   docker inspect analytics-platform | grep -A 10 "Mounts"
   
   # Verify directory permissions
   docker exec analytics-platform ls -la /app/data/
   ```

### Performance Tuning

1. **Memory optimization**
   ```bash
   # Run with memory limit
   docker run --memory=4g --memory-swap=4g ...
   ```

2. **CPU optimization**
   ```bash
   # Run with CPU limit
   docker run --cpus=2.0 ...
   ```

3. **Storage optimization**
   ```bash
   # Use named volumes for better performance
   docker volume create analytics-data
   docker run -v analytics-data:/app/data ...
   ```

## Monitoring and Logging

### Health Monitoring
The container includes a comprehensive health check system:

- **Streamlit Health**: Verifies web application is responsive
- **Environment Check**: Validates required configuration
- **Directory Check**: Ensures data directories are accessible

### Log Collection
```bash
# View real-time logs
docker logs -f analytics-platform

# Export logs
docker logs analytics-platform > analytics.log

# Use log driver for centralized logging
docker run --log-driver=json-file --log-opt max-size=10m ...
```

### Metrics Collection
The container exposes metrics for monitoring systems:

- Health check endpoint: `http://localhost:8501/_stcore/health`
- Application metrics: Available through Streamlit's built-in monitoring
- Custom metrics: Can be added via the health check script

## Integration with Orchestration

### Docker Compose
See `docker-compose.yml` for complete orchestration setup.

### Kubernetes
The image is compatible with Kubernetes deployment:
- Supports health checks
- Configurable via environment variables
- Stateless design with external data volumes

### Cloud Platforms
Optimized for cloud deployment on:
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances
- Docker Swarm

## Security Considerations

1. **API Keys**: Never include API keys in the image. Use environment variables or secrets management.
2. **Network Security**: Run behind a reverse proxy for HTTPS termination.
3. **Resource Limits**: Set appropriate memory and CPU limits.
4. **Updates**: Regularly update base images for security patches.
5. **Scanning**: Use container security scanning tools.

## Support

For issues related to Docker deployment:
1. Check the troubleshooting section above
2. Review container logs
3. Run the health check script
4. Verify environment configuration