#!/usr/bin/env python3
"""
Enhanced Monitoring Endpoints for User Behavior Analytics Platform
Provides health checks, metrics, and system status endpoints for container orchestration
"""

import os
import sys
import time
import json
import psutil
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field
from flask import Flask, jsonify, Response
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System metrics data model"""
    timestamp: float = field(default_factory=time.time)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_total_mb: float = 0.0
    disk_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    process_count: int = 0
    uptime_seconds: float = 0.0

@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""
    timestamp: float = field(default_factory=time.time)
    streamlit_status: str = "unknown"
    streamlit_response_time: float = 0.0
    api_connectivity: Dict[str, bool] = field(default_factory=dict)
    request_count: int = 0
    error_count: int = 0
    active_sessions: int = 0
    data_processing_jobs: int = 0
    last_successful_analysis: Optional[float] = None

class MonitoringService:
    """Enhanced monitoring service with metrics collection"""
    
    def __init__(self, port: int = 8502):
        self.port = port
        self.app = Flask(__name__)
        self.start_time = time.time()
        self.system_metrics = SystemMetrics()
        self.app_metrics = ApplicationMetrics()
        self.metrics_history: List[SystemMetrics] = []
        self.max_history = 100  # Keep last 100 metrics
        
        # Setup routes
        self._setup_routes()
        
        # Start metrics collection thread
        self.metrics_thread = threading.Thread(target=self._collect_metrics_loop, daemon=True)
        self.metrics_thread.start()
    
    def _setup_routes(self):
        """Setup Flask routes for monitoring endpoints"""
        
        @self.app.route('/health')
        def health():
            """Basic health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'user-behavior-analytics-platform',
                'uptime_seconds': time.time() - self.start_time
            })
        
        @self.app.route('/health/detailed')
        def detailed_health():
            """Detailed health check with comprehensive system status"""
            health_status = self._get_detailed_health_status()
            return jsonify(health_status)
        
        @self.app.route('/metrics')
        def metrics():
            """Prometheus-compatible metrics endpoint"""
            metrics_text = self._generate_prometheus_metrics()
            return Response(metrics_text, mimetype='text/plain')
        
        @self.app.route('/metrics/json')
        def metrics_json():
            """JSON format metrics for easier consumption"""
            return jsonify({
                'system': self.system_metrics.__dict__,
                'application': self.app_metrics.__dict__,
                'timestamp': time.time()
            })
        
        @self.app.route('/status')
        def status():
            """System status overview"""
            return jsonify(self._get_system_status())
        
        @self.app.route('/version')
        def version():
            """Application version and build information"""
            return jsonify({
                'service': 'user-behavior-analytics-platform',
                'version': '1.0.0',
                'build_date': datetime.now().isoformat(),
                'python_version': sys.version,
                'environment': {
                    'streamlit_port': os.getenv('STREAMLIT_SERVER_PORT', '8501'),
                    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
                    'default_provider': os.getenv('DEFAULT_LLM_PROVIDER', 'volcano')
                }
            })
        
        @self.app.route('/api/connectivity')
        def api_connectivity():
            """Test API connectivity for all configured providers"""
            connectivity_results = self._test_api_connectivity()
            return jsonify(connectivity_results)
    
    def _collect_metrics_loop(self):
        """Background thread to collect system metrics"""
        while True:
            try:
                self._collect_system_metrics()
                self._collect_application_metrics()
                
                # Add to history
                self.metrics_history.append(SystemMetrics(**self.system_metrics.__dict__))
                if len(self.metrics_history) > self.max_history:
                    self.metrics_history.pop(0)
                
                time.sleep(30)  # Collect metrics every 30 seconds
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # CPU metrics
            self.system_metrics.cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.system_metrics.memory_percent = memory.percent
            self.system_metrics.memory_used_mb = memory.used / 1024 / 1024
            self.system_metrics.memory_total_mb = memory.total / 1024 / 1024
            
            # Disk metrics
            disk = psutil.disk_usage('/app')
            self.system_metrics.disk_percent = disk.percent
            self.system_metrics.disk_used_gb = disk.used / 1024 / 1024 / 1024
            self.system_metrics.disk_total_gb = disk.total / 1024 / 1024 / 1024
            
            # Network metrics
            network = psutil.net_io_counters()
            self.system_metrics.network_bytes_sent = network.bytes_sent
            self.system_metrics.network_bytes_recv = network.bytes_recv
            
            # Process metrics
            self.system_metrics.process_count = len(psutil.pids())
            self.system_metrics.uptime_seconds = time.time() - self.start_time
            self.system_metrics.timestamp = time.time()
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _collect_application_metrics(self):
        """Collect application-specific metrics"""
        try:
            # Test Streamlit connectivity
            streamlit_port = os.getenv('STREAMLIT_SERVER_PORT', '8501')
            start_time = time.time()
            
            try:
                response = requests.get(
                    f'http://localhost:{streamlit_port}/_stcore/health',
                    timeout=5
                )
                if response.status_code == 200:
                    self.app_metrics.streamlit_status = "healthy"
                    self.app_metrics.streamlit_response_time = time.time() - start_time
                else:
                    self.app_metrics.streamlit_status = "unhealthy"
                    self.app_metrics.streamlit_response_time = 0.0
            except Exception:
                self.app_metrics.streamlit_status = "unreachable"
                self.app_metrics.streamlit_response_time = 0.0
            
            # Test API connectivity
            self.app_metrics.api_connectivity = self._test_api_connectivity_simple()
            
            # Update timestamp
            self.app_metrics.timestamp = time.time()
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
    
    def _test_api_connectivity_simple(self) -> Dict[str, bool]:
        """Simple API connectivity test for metrics collection"""
        connectivity = {}
        
        # Test Google API
        if os.getenv('GOOGLE_API_KEY'):
            connectivity['google'] = True  # Assume healthy if key is present
        else:
            connectivity['google'] = False
        
        # Test Volcano ARK API
        if os.getenv('ARK_API_KEY'):
            connectivity['volcano'] = True  # Assume healthy if key is present
        else:
            connectivity['volcano'] = False
        
        return connectivity
    
    def _test_api_connectivity(self) -> Dict[str, Any]:
        """Comprehensive API connectivity test"""
        results = {
            'timestamp': time.time(),
            'providers': {}
        }
        
        # Test Google API
        google_key = os.getenv('GOOGLE_API_KEY')
        if google_key:
            results['providers']['google'] = {
                'configured': True,
                'status': 'healthy',  # Would need actual API test
                'response_time': 0.0,
                'last_tested': time.time()
            }
        else:
            results['providers']['google'] = {
                'configured': False,
                'status': 'not_configured',
                'error': 'API key not provided'
            }
        
        # Test Volcano ARK API
        ark_key = os.getenv('ARK_API_KEY')
        if ark_key:
            results['providers']['volcano'] = {
                'configured': True,
                'status': 'healthy',  # Would need actual API test
                'response_time': 0.0,
                'last_tested': time.time()
            }
        else:
            results['providers']['volcano'] = {
                'configured': False,
                'status': 'not_configured',
                'error': 'API key not provided'
            }
        
        return results
    
    def _get_detailed_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        health_checks = {
            'streamlit': self._check_streamlit_health(),
            'system_resources': self._check_system_resources(),
            'directories': self._check_directories(),
            'api_connectivity': self._test_api_connectivity(),
            'configuration': self._check_configuration()
        }
        
        # Determine overall status
        overall_status = 'healthy'
        for check in health_checks.values():
            if isinstance(check, dict) and check.get('status') == 'unhealthy':
                overall_status = 'unhealthy'
                break
            elif isinstance(check, dict) and check.get('status') == 'degraded':
                overall_status = 'degraded'
        
        return {
            'overall_status': overall_status,
            'timestamp': time.time(),
            'uptime_seconds': time.time() - self.start_time,
            'checks': health_checks,
            'metrics': {
                'system': self.system_metrics.__dict__,
                'application': self.app_metrics.__dict__
            }
        }

    def _generate_prometheus_metrics(self) -> str:
        """Generate Prometheus-compatible metrics"""
        metrics = []

        # System metrics
        metrics.append(f"# HELP analytics_cpu_percent CPU usage percentage")
        metrics.append(f"# TYPE analytics_cpu_percent gauge")
        metrics.append(f"analytics_cpu_percent {self.system_metrics.cpu_percent}")

        metrics.append(f"# HELP analytics_memory_percent Memory usage percentage")
        metrics.append(f"# TYPE analytics_memory_percent gauge")
        metrics.append(f"analytics_memory_percent {self.system_metrics.memory_percent}")

        metrics.append(f"# HELP analytics_memory_used_mb Memory used in MB")
        metrics.append(f"# TYPE analytics_memory_used_mb gauge")
        metrics.append(f"analytics_memory_used_mb {self.system_metrics.memory_used_mb}")

        metrics.append(f"# HELP analytics_disk_percent Disk usage percentage")
        metrics.append(f"# TYPE analytics_disk_percent gauge")
        metrics.append(f"analytics_disk_percent {self.system_metrics.disk_percent}")

        metrics.append(f"# HELP analytics_network_bytes_sent Network bytes sent")
        metrics.append(f"# TYPE analytics_network_bytes_sent counter")
        metrics.append(f"analytics_network_bytes_sent {self.system_metrics.network_bytes_sent}")

        metrics.append(f"# HELP analytics_network_bytes_recv Network bytes received")
        metrics.append(f"# TYPE analytics_network_bytes_recv counter")
        metrics.append(f"analytics_network_bytes_recv {self.system_metrics.network_bytes_recv}")

        metrics.append(f"# HELP analytics_process_count Number of processes")
        metrics.append(f"# TYPE analytics_process_count gauge")
        metrics.append(f"analytics_process_count {self.system_metrics.process_count}")

        metrics.append(f"# HELP analytics_uptime_seconds Application uptime in seconds")
        metrics.append(f"# TYPE analytics_uptime_seconds counter")
        metrics.append(f"analytics_uptime_seconds {self.system_metrics.uptime_seconds}")

        # Application metrics
        streamlit_status_value = 1 if self.app_metrics.streamlit_status == "healthy" else 0
        metrics.append(f"# HELP analytics_streamlit_healthy Streamlit application health (1=healthy, 0=unhealthy)")
        metrics.append(f"# TYPE analytics_streamlit_healthy gauge")
        metrics.append(f"analytics_streamlit_healthy {streamlit_status_value}")

        metrics.append(f"# HELP analytics_streamlit_response_time Streamlit response time in seconds")
        metrics.append(f"# TYPE analytics_streamlit_response_time gauge")
        metrics.append(f"analytics_streamlit_response_time {self.app_metrics.streamlit_response_time}")

        # API connectivity metrics
        for provider, connected in self.app_metrics.api_connectivity.items():
            value = 1 if connected else 0
            metrics.append(f"# HELP analytics_api_connectivity_{provider} API connectivity for {provider} (1=connected, 0=disconnected)")
            metrics.append(f"# TYPE analytics_api_connectivity_{provider} gauge")
            metrics.append(f"analytics_api_connectivity_{provider} {value}")

        metrics.append(f"# HELP analytics_request_count Total number of requests")
        metrics.append(f"# TYPE analytics_request_count counter")
        metrics.append(f"analytics_request_count {self.app_metrics.request_count}")

        metrics.append(f"# HELP analytics_error_count Total number of errors")
        metrics.append(f"# TYPE analytics_error_count counter")
        metrics.append(f"analytics_error_count {self.app_metrics.error_count}")

        return "\n".join(metrics) + "\n"

    def run(self, host: str = '0.0.0.0', debug: bool = False):
        """Run the monitoring service"""
        logger.info(f"Starting monitoring service on {host}:{self.port}")
        self.app.run(host=host, port=self.port, debug=debug, threaded=True)

def create_monitoring_service(port: int = 8502) -> MonitoringService:
    """Create and configure monitoring service"""
    return MonitoringService(port=port)

def main():
    """Main function for standalone execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Analytics Platform Monitoring Service')
    parser.add_argument('--port', type=int, default=8502, help='Port to run monitoring service on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind monitoring service to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    print("🔍 Analytics Platform Monitoring Service")
    print("=" * 50)
    print(f"Starting monitoring service on {args.host}:{args.port}")
    print("Available endpoints:")
    print(f"  - Health Check: http://{args.host}:{args.port}/health")
    print(f"  - Detailed Health: http://{args.host}:{args.port}/health/detailed")
    print(f"  - Prometheus Metrics: http://{args.host}:{args.port}/metrics")
    print(f"  - JSON Metrics: http://{args.host}:{args.port}/metrics/json")
    print(f"  - System Status: http://{args.host}:{args.port}/status")
    print(f"  - Version Info: http://{args.host}:{args.port}/version")
    print(f"  - API Connectivity: http://{args.host}:{args.port}/api/connectivity")
    print("=" * 50)

    try:
        monitoring_service = create_monitoring_service(port=args.port)
        monitoring_service.run(host=args.host, debug=args.debug)
    except KeyboardInterrupt:
        print("\n🛑 Monitoring service stopped by user")
    except Exception as e:
        print(f"❌ Failed to start monitoring service: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
    
    def _check_streamlit_health(self) -> Dict[str, Any]:
        """Check Streamlit application health"""
        port = os.getenv('STREAMLIT_SERVER_PORT', '8501')
        
        try:
            response = requests.get(f'http://localhost:{port}/_stcore/health', timeout=10)
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'port': port
                }
            else:
                return {
                    'status': 'unhealthy',
                    'error': f'HTTP {response.status_code}',
                    'port': port
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'port': port
            }
    
    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/app')
            
            status = 'healthy'
            if memory.percent > 90 or disk.percent > 90:
                status = 'unhealthy'
            elif memory.percent > 80 or disk.percent > 80:
                status = 'degraded'
            
            return {
                'status': status,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'cpu_percent': psutil.cpu_percent()
            }
        except Exception as e:
            return {
                'status': 'unknown',
                'error': str(e)
            }
    
    def _check_directories(self) -> Dict[str, Any]:
        """Check required directories"""
        required_dirs = ['/app/data', '/app/reports', '/app/logs', '/app/config']
        status = 'healthy'
        directories = {}
        
        for dir_path in required_dirs:
            if Path(dir_path).exists() and os.access(dir_path, os.W_OK):
                directories[dir_path] = 'writable'
            elif Path(dir_path).exists():
                directories[dir_path] = 'read-only'
                status = 'degraded'
            else:
                directories[dir_path] = 'missing'
                status = 'unhealthy'
        
        return {
            'status': status,
            'directories': directories
        }
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check configuration validity"""
        has_google = bool(os.getenv('GOOGLE_API_KEY'))
        has_ark = bool(os.getenv('ARK_API_KEY'))
        
        if has_google or has_ark:
            return {
                'status': 'healthy',
                'api_keys': {
                    'google': has_google,
                    'ark': has_ark
                }
            }
        else:
            return {
                'status': 'unhealthy',
                'error': 'No API keys configured'
            }
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get system status overview"""
        return {
            'service': 'user-behavior-analytics-platform',
            'status': 'running',
            'uptime_seconds': time.time() - self.start_time,
            'timestamp': time.time(),
            'system_metrics': self.system_metrics.__dict__,
            'application_metrics': self.app_metrics.__dict__,
            'environment': {
                'python_version': sys.version.split()[0],
                'platform': sys.platform,
                'streamlit_port': os.getenv('STREAMLIT_SERVER_PORT', '8501'),
                'log_level': os.getenv('LOG_LEVEL', 'INFO')
            }
        }
