# Docker Deployment Guide
## User Behavior Analytics Platform

This guide provides comprehensive instructions for deploying the User Behavior Analytics Platform using Docker containers.

## 🚀 Quick Start

### Development Environment
```bash
# Start development environment
./deploy.sh -e development -a up -b

# Follow logs
./deploy.sh -e development -a logs -f
```

### Production Environment
```bash
# Start production environment
./deploy.sh -e production -a up -d

# Check status
./deploy.sh -e production -a status
```

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available
- 10GB free disk space

## 🏗️ Architecture Overview

The containerized platform includes:

- **Multi-stage Dockerfile** with optimized layers
- **Enhanced monitoring service** with Prometheus metrics
- **Security-hardened configurations** with non-root user
- **Comprehensive health checks** and status endpoints
- **Flexible configuration management** via environment variables and files

## 📁 File Structure

```
├── Dockerfile                     # Multi-stage container definition
├── docker-compose.yml            # Production configuration
├── docker-compose.dev.yml        # Development configuration
├── docker-compose.secure.yml     # Security-hardened configuration
├── docker-compose.test.yml       # Testing configuration
├── deploy.sh                     # Deployment automation script
├── entrypoint.sh                 # Container startup script
├── healthcheck.py                # Basic health check script
├── monitoring_endpoints.py       # Enhanced monitoring service
├── container_config_manager.py   # Configuration management
├── .dockerignore                 # Build context optimization
├── .env.example                  # Environment template
├── .env.dev.example             # Development environment template
├── .env.prod.example            # Production environment template
├── config/
│   ├── container.yml.example    # YAML configuration template
│   └── container.json.example   # JSON configuration template
└── security/
    ├── security-policy.yml      # Security policy definition
    ├── secure_env_handler.py    # Secure environment handler
    └── k8s-security.yml         # Kubernetes security configuration
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

**Required Variables:**
- `GOOGLE_API_KEY` or `ARK_API_KEY` (at least one required)

**Optional Variables:**
- `STREAMLIT_SERVER_PORT` (default: 8501)
- `LOG_LEVEL` (default: INFO)
- `DEFAULT_LLM_PROVIDER` (default: volcano)

### External Configuration Files

You can also use YAML or JSON configuration files:

```bash
# Copy and customize configuration templates
cp config/container.yml.example config/container.yml
cp config/container.json.example config/container.json
```

## 🐳 Docker Images

### Available Build Targets

1. **base** - Base Python environment with system dependencies
2. **dependencies** - Python packages installed
3. **application** - Application code and scripts
4. **production** - Optimized production image
5. **production-secure** - Security-hardened production image

### Building Images

```bash
# Build development image
docker build --target application -t analytics-platform:dev .

# Build production image
docker build --target production -t analytics-platform:latest .

# Build security-hardened image
docker build --target production-secure -t analytics-platform:secure .
```

## 🚀 Deployment Options

### 1. Development Deployment

```bash
# Using deployment script
./deploy.sh -e development -a up -b

# Using Docker Compose directly
docker-compose -f docker-compose.dev.yml up --build
```

**Features:**
- Hot reload enabled
- Debug logging
- Local volume mounts
- Development-friendly settings

### 2. Production Deployment

```bash
# Using deployment script
./deploy.sh -e production -a up -d

# Using Docker Compose directly
docker-compose up -d
```

**Features:**
- Optimized performance
- Resource limits
- Health checks
- Persistent volumes

### 3. Security-Hardened Deployment

```bash
# Using security-hardened configuration
docker-compose -f docker-compose.secure.yml up -d
```

**Features:**
- Read-only root filesystem
- Capability dropping
- Security contexts
- Enhanced monitoring

## 📊 Monitoring and Health Checks

### Available Endpoints

Once deployed, the following monitoring endpoints are available:

- **Health Check**: `http://localhost:8502/health`
- **Detailed Health**: `http://localhost:8502/health/detailed`
- **Prometheus Metrics**: `http://localhost:8502/metrics`
- **JSON Metrics**: `http://localhost:8502/metrics/json`
- **System Status**: `http://localhost:8502/status`
- **Version Info**: `http://localhost:8502/version`
- **API Connectivity**: `http://localhost:8502/api/connectivity`

### Health Check Examples

```bash
# Basic health check
curl http://localhost:8502/health

# Detailed system status
curl http://localhost:8502/health/detailed | jq

# Prometheus metrics
curl http://localhost:8502/metrics
```

## 🔒 Security Features

### Container Security

- **Non-root user execution** (UID 1000)
- **Read-only root filesystem** (in secure mode)
- **Capability dropping** (minimal required capabilities)
- **Resource limits** (CPU, memory, processes)
- **Security contexts** and AppArmor profiles

### Secret Management

- **Environment variable validation**
- **Docker secrets support**
- **Kubernetes secrets integration**
- **Secure environment handler**

### Network Security

- **Minimal exposed ports** (8501, 8502)
- **Network policies** for Kubernetes
- **Inter-container communication controls**

## 🔧 Troubleshooting

### Common Issues

1. **Container fails to start**
   ```bash
   # Check logs
   docker-compose logs analytics-platform
   
   # Validate configuration
   python3 container_config_manager.py
   ```

2. **Health checks failing**
   ```bash
   # Test health endpoint
   curl -f http://localhost:8502/health
   
   # Check detailed status
   python3 healthcheck.py --json
   ```

3. **API connectivity issues**
   ```bash
   # Verify API keys
   python3 security/secure_env_handler.py
   
   # Test API connectivity
   curl http://localhost:8502/api/connectivity
   ```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Set debug environment
export LOG_LEVEL=DEBUG
export DEBUG_MODE=true

# Restart with debug logging
./deploy.sh -e development -a up
```

## 📈 Performance Tuning

### Resource Limits

Adjust resource limits in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 4G      # Adjust based on your needs
      cpus: '2.0'     # Adjust based on your CPU
    reservations:
      memory: 1G
      cpus: '0.5'
```

### Volume Optimization

For better performance, use SSD storage for volumes:

```yaml
volumes:
  analytics-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /fast-ssd/analytics/data
```

## 🔄 Maintenance

### Updating the Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
./deploy.sh -e production -a down
./deploy.sh -e production -a up -b
```

### Backup and Restore

```bash
# Backup data volumes
docker run --rm -v analytics-data:/data -v $(pwd):/backup alpine tar czf /backup/data-backup.tar.gz -C /data .

# Restore data volumes
docker run --rm -v analytics-data:/data -v $(pwd):/backup alpine tar xzf /backup/data-backup.tar.gz -C /data
```

### Log Management

```bash
# View logs
./deploy.sh -e production -a logs

# Rotate logs (if needed)
docker-compose exec analytics-platform logrotate /etc/logrotate.conf
```

## 🚀 Kubernetes Deployment

For Kubernetes deployment, use the provided security configuration:

```bash
# Apply Kubernetes configuration
kubectl apply -f security/k8s-security.yml

# Check deployment status
kubectl get pods -n analytics-platform
```

## 📞 Support

For issues and questions:

1. Check the troubleshooting section above
2. Review container logs: `docker-compose logs`
3. Validate configuration: `python3 container_config_manager.py`
4. Test health endpoints: `curl http://localhost:8502/health/detailed`

## 📝 License

This deployment configuration is part of the User Behavior Analytics Platform project.
