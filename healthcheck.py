#!/usr/bin/env python3
"""
Health check script for User Behavior Analytics Platform Docker container
Verifies that the Streamlit application is running and responsive
Enhanced version with comprehensive system checks
"""

import sys
import requests
import json
import os
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

def check_streamlit_health() -> Dict[str, Any]:
    """Check if Streamlit application is healthy"""
    port = os.getenv('STREAMLIT_SERVER_PORT', '8501')
    host = os.getenv('STREAMLIT_SERVER_ADDRESS', 'localhost')
    
    try:
        # Check Streamlit health endpoint
        response = requests.get(
            f'http://{host}:{port}/_stcore/health',
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                'status': 'healthy',
                'service': 'streamlit',
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code
            }
        else:
            return {
                'status': 'unhealthy',
                'service': 'streamlit',
                'error': f'HTTP {response.status_code}',
                'status_code': response.status_code
            }
            
    except requests.exceptions.ConnectionError:
        return {
            'status': 'unhealthy',
            'service': 'streamlit',
            'error': 'Connection refused'
        }
    except requests.exceptions.Timeout:
        return {
            'status': 'unhealthy',
            'service': 'streamlit',
            'error': 'Request timeout'
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'service': 'streamlit',
            'error': str(e)
        }

def check_environment() -> Dict[str, Any]:
    """Check if required environment variables are set"""
    required_vars = []
    optional_vars = [
        'GOOGLE_API_KEY',
        'ARK_API_KEY',
        'STREAMLIT_SERVER_PORT',
        'STREAMLIT_SERVER_ADDRESS',
        'LOG_LEVEL'
    ]
    
    # At least one API key should be present
    has_google_key = bool(os.getenv('GOOGLE_API_KEY'))
    has_ark_key = bool(os.getenv('ARK_API_KEY'))
    
    if not (has_google_key or has_ark_key):
        return {
            'status': 'unhealthy',
            'service': 'environment',
            'error': 'No API keys configured (GOOGLE_API_KEY or ARK_API_KEY required)'
        }
    
    env_status = {
        'status': 'healthy',
        'service': 'environment',
        'api_keys': {
            'google': has_google_key,
            'ark': has_ark_key
        },
        'config': {
            'port': os.getenv('STREAMLIT_SERVER_PORT', '8501'),
            'host': os.getenv('STREAMLIT_SERVER_ADDRESS', '0.0.0.0'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO')
        }
    }
    
    return env_status

def check_directories() -> Dict[str, Any]:
    """Check if required directories exist and are writable"""
    required_dirs = [
        '/app/data/uploads',
        '/app/data/processed',
        '/app/reports',
        '/app/logs',
        '/app/logs/monitoring',
        '/app/config'
    ]
    
    dir_status = {
        'status': 'healthy',
        'service': 'directories',
        'directories': {},
        'summary': {
            'total': len(required_dirs),
            'healthy': 0,
            'degraded': 0,
            'missing': 0
        }
    }
    
    for dir_path in required_dirs:
        try:
            path_obj = Path(dir_path)
            if path_obj.exists():
                if os.access(dir_path, os.W_OK):
                    dir_status['directories'][dir_path] = 'writable'
                    dir_status['summary']['healthy'] += 1
                else:
                    dir_status['directories'][dir_path] = 'read-only'
                    dir_status['summary']['degraded'] += 1
                    if dir_status['status'] == 'healthy':
                        dir_status['status'] = 'degraded'
            else:
                dir_status['directories'][dir_path] = 'missing'
                dir_status['summary']['missing'] += 1
                dir_status['status'] = 'unhealthy'
        except Exception as e:
            dir_status['directories'][dir_path] = f'error: {str(e)}'
            dir_status['summary']['missing'] += 1
            dir_status['status'] = 'unhealthy'
    
    return dir_status

def check_system_resources() -> Dict[str, Any]:
    """Check system resource usage"""
    try:
        # Get memory usage
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        
        mem_total = None
        mem_available = None
        for line in meminfo.split('\n'):
            if line.startswith('MemTotal:'):
                mem_total = int(line.split()[1]) * 1024  # Convert to bytes
            elif line.startswith('MemAvailable:'):
                mem_available = int(line.split()[1]) * 1024  # Convert to bytes
        
        if mem_total and mem_available:
            mem_used_percent = ((mem_total - mem_available) / mem_total) * 100
        else:
            mem_used_percent = 0
        
        # Get disk usage for /app
        try:
            result = subprocess.run(['df', '/app'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    fields = lines[1].split()
                    if len(fields) >= 5:
                        disk_used_percent = int(fields[4].rstrip('%'))
                    else:
                        disk_used_percent = 0
                else:
                    disk_used_percent = 0
            else:
                disk_used_percent = 0
        except Exception:
            disk_used_percent = 0
        
        # Determine status based on resource usage
        status = 'healthy'
        if mem_used_percent > 90 or disk_used_percent > 90:
            status = 'unhealthy'
        elif mem_used_percent > 80 or disk_used_percent > 80:
            status = 'degraded'
        
        return {
            'status': status,
            'service': 'system_resources',
            'memory': {
                'total_mb': round(mem_total / 1024 / 1024) if mem_total else 0,
                'available_mb': round(mem_available / 1024 / 1024) if mem_available else 0,
                'used_percent': round(mem_used_percent, 1)
            },
            'disk': {
                'used_percent': disk_used_percent
            }
        }
        
    except Exception as e:
        return {
            'status': 'unknown',
            'service': 'system_resources',
            'error': str(e)
        }

def check_application_processes() -> Dict[str, Any]:
    """Check if application processes are running"""
    try:
        # Check for Streamlit process
        result = subprocess.run(['pgrep', '-f', 'streamlit'], capture_output=True, text=True)
        streamlit_running = result.returncode == 0 and result.stdout.strip()
        
        # Check for Python processes
        result = subprocess.run(['pgrep', '-f', 'python'], capture_output=True, text=True)
        python_processes = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        
        status = 'healthy' if streamlit_running else 'unhealthy'
        
        return {
            'status': status,
            'service': 'application_processes',
            'processes': {
                'streamlit_running': streamlit_running,
                'python_processes': python_processes
            }
        }
        
    except Exception as e:
        return {
            'status': 'unknown',
            'service': 'application_processes',
            'error': str(e)
        }

def run_comprehensive_check() -> Dict[str, Any]:
    """Run comprehensive health check and return results"""
    checks = {
        'streamlit': check_streamlit_health(),
        'environment': check_environment(),
        'directories': check_directories(),
        'system_resources': check_system_resources(),
        'processes': check_application_processes()
    }
    
    # Determine overall health
    overall_status = 'healthy'
    critical_failures = 0
    warnings = 0
    
    for check_name, check_result in checks.items():
        status = check_result.get('status', 'unknown')
        
        if status == 'unhealthy':
            critical_failures += 1
            overall_status = 'unhealthy'
        elif status == 'degraded':
            warnings += 1
            if overall_status == 'healthy':
                overall_status = 'degraded'
        elif status == 'unknown':
            warnings += 1
            if overall_status == 'healthy':
                overall_status = 'degraded'
    
    return {
        'overall_status': overall_status,
        'timestamp': time.time(),
        'summary': {
            'total_checks': len(checks),
            'critical_failures': critical_failures,
            'warnings': warnings,
            'healthy_checks': len(checks) - critical_failures - warnings
        },
        'checks': checks
    }

def main():
    """Main health check function"""
    print("🏥 User Behavior Analytics Platform - Health Check")
    print("=" * 50)
    
    # Run comprehensive check
    health_report = run_comprehensive_check()
    overall_status = health_report['overall_status']
    checks = health_report['checks']
    summary = health_report['summary']
    
    # Print summary
    print(f"📊 Health Check Summary:")
    print(f"   Total Checks: {summary['total_checks']}")
    print(f"   Healthy: {summary['healthy_checks']}")
    print(f"   Warnings: {summary['warnings']}")
    print(f"   Critical: {summary['critical_failures']}")
    print()
    
    # Print detailed results
    for check_name, check_result in checks.items():
        status = check_result.get('status', 'unknown')
        service = check_result.get('service', check_name)
        
        if status == 'healthy':
            print(f"✅ {service.title().replace('_', ' ')}: {status}")
        elif status == 'degraded':
            print(f"⚠️  {service.title().replace('_', ' ')}: {status}")
        else:
            print(f"❌ {service.title().replace('_', ' ')}: {status}")
            
        if 'error' in check_result:
            print(f"   Error: {check_result['error']}")
        
        # Print additional details for specific checks
        if check_name == 'environment' and status in ['healthy', 'degraded']:
            api_keys = check_result.get('api_keys', {})
            print(f"   API Keys: Google={api_keys.get('google', False)}, ARK={api_keys.get('ark', False)}")
        
        if check_name == 'streamlit' and status == 'healthy':
            response_time = check_result.get('response_time', 0)
            print(f"   Response Time: {response_time:.3f}s")
        
        if check_name == 'directories' and 'summary' in check_result:
            dir_summary = check_result['summary']
            print(f"   Directories: {dir_summary['healthy']}/{dir_summary['total']} healthy")
        
        if check_name == 'system_resources' and status in ['healthy', 'degraded']:
            memory = check_result.get('memory', {})
            disk = check_result.get('disk', {})
            print(f"   Memory: {memory.get('used_percent', 0)}% used")
            print(f"   Disk: {disk.get('used_percent', 0)}% used")
        
        if check_name == 'processes' and 'processes' in check_result:
            processes = check_result['processes']
            print(f"   Streamlit: {'Running' if processes.get('streamlit_running') else 'Not Running'}")
            print(f"   Python Processes: {processes.get('python_processes', 0)}")
        
        print()
    
    print("=" * 50)
    print(f"🎯 Overall Status: {overall_status.upper()}")
    
    # Output JSON format if requested
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        print("\n📄 JSON Output:")
        print(json.dumps(health_report, indent=2))
    
    # Exit with appropriate code
    if overall_status == 'healthy':
        sys.exit(0)
    elif overall_status == 'degraded':
        sys.exit(1)  # Warning status
    else:
        sys.exit(2)  # Critical status

if __name__ == '__main__':
    main()