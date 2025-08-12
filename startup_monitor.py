#!/usr/bin/env python3
"""
Startup monitoring script for User Behavior Analytics Platform
Monitors application startup and provides detailed status information
"""

import time
import sys
import requests
import subprocess
import json
from datetime import datetime
from typing import Dict, Any, Optional

class StartupMonitor:
    """Monitor application startup process"""
    
    def __init__(self, streamlit_port: int = 8501, health_port: int = 8502, timeout: int = 120):
        self.streamlit_port = streamlit_port
        self.health_port = health_port
        self.timeout = timeout
        self.start_time = time.time()
    
    def log(self, level: str, message: str):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        elapsed = time.time() - self.start_time
        print(f"[{timestamp}] [{elapsed:6.1f}s] {level}: {message}")
    
    def check_streamlit_health(self) -> Dict[str, Any]:
        """Check Streamlit application health"""
        try:
            response = requests.get(
                f'http://localhost:{self.streamlit_port}/_stcore/health',
                timeout=5
            )
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'status_code': response.status_code
                }
            else:
                return {
                    'status': 'unhealthy',
                    'status_code': response.status_code,
                    'error': f'HTTP {response.status_code}'
                }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'connecting',
                'error': 'Connection refused'
            }
        except requests.exceptions.Timeout:
            return {
                'status': 'timeout',
                'error': 'Request timeout'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_health_endpoint(self) -> Dict[str, Any]:
        """Check custom health endpoint"""
        try:
            response = requests.get(
                f'http://localhost:{self.health_port}/health',
                timeout=5
            )
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'status_code': response.status_code
                }
        except requests.exceptions.ConnectionError:
            return {
                'status': 'connecting',
                'error': 'Connection refused'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def check_processes(self) -> Dict[str, Any]:
        """Check if required processes are running"""
        try:
            # Check for Streamlit process
            result = subprocess.run(['pgrep', '-f', 'streamlit'], capture_output=True, text=True)
            streamlit_pids = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # Check for Python processes
            result = subprocess.run(['pgrep', '-f', 'python'], capture_output=True, text=True)
            python_pids = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            return {
                'streamlit_processes': len(streamlit_pids),
                'python_processes': len(python_pids),
                'streamlit_pids': streamlit_pids,
                'python_pids': python_pids
            }
        except Exception as e:
            return {
                'error': str(e)
            }
    
    def wait_for_startup(self) -> bool:
        """Wait for application to start up completely"""
        self.log("INFO", f"Starting startup monitoring (timeout: {self.timeout}s)")
        self.log("INFO", f"Monitoring Streamlit on port {self.streamlit_port}")
        self.log("INFO", f"Monitoring health endpoint on port {self.health_port}")
        
        startup_phases = [
            ("Waiting for processes to start", self._wait_for_processes),
            ("Waiting for Streamlit to respond", self._wait_for_streamlit),
            ("Waiting for health endpoint", self._wait_for_health_endpoint),
            ("Verifying application readiness", self._verify_readiness)
        ]
        
        for phase_name, phase_func in startup_phases:
            self.log("INFO", f"Phase: {phase_name}")
            
            if not phase_func():
                self.log("ERROR", f"Failed during phase: {phase_name}")
                return False
            
            self.log("INFO", f"Completed: {phase_name}")
        
        elapsed = time.time() - self.start_time
        self.log("INFO", f"Application startup completed successfully in {elapsed:.1f}s")
        return True
    
    def _wait_for_processes(self) -> bool:
        """Wait for processes to start"""
        deadline = time.time() + 30  # 30 second timeout for processes
        
        while time.time() < deadline:
            processes = self.check_processes()
            
            if 'error' not in processes:
                if processes.get('streamlit_processes', 0) > 0:
                    self.log("INFO", f"Found {processes['streamlit_processes']} Streamlit process(es)")
                    return True
                elif processes.get('python_processes', 0) > 0:
                    self.log("DEBUG", f"Found {processes['python_processes']} Python process(es), waiting for Streamlit...")
            
            time.sleep(2)
        
        self.log("ERROR", "Timeout waiting for processes to start")
        return False
    
    def _wait_for_streamlit(self) -> bool:
        """Wait for Streamlit to respond"""
        deadline = time.time() + 60  # 60 second timeout for Streamlit
        last_status = None
        
        while time.time() < deadline:
            health = self.check_streamlit_health()
            status = health.get('status')
            
            if status != last_status:
                if status == 'healthy':
                    response_time = health.get('response_time', 0)
                    self.log("INFO", f"Streamlit is healthy (response time: {response_time:.3f}s)")
                    return True
                elif status == 'connecting':
                    self.log("DEBUG", "Streamlit not yet accepting connections...")
                elif status == 'timeout':
                    self.log("WARN", "Streamlit connection timeout")
                elif status == 'unhealthy':
                    self.log("WARN", f"Streamlit unhealthy: {health.get('error', 'Unknown error')}")
                else:
                    self.log("WARN", f"Streamlit status: {status}")
                
                last_status = status
            
            time.sleep(3)
        
        self.log("ERROR", "Timeout waiting for Streamlit to become healthy")
        return False
    
    def _wait_for_health_endpoint(self) -> bool:
        """Wait for health endpoint to respond"""
        deadline = time.time() + 30  # 30 second timeout for health endpoint
        last_status = None
        
        while time.time() < deadline:
            health = self.check_health_endpoint()
            status = health.get('status')
            
            if status != last_status:
                if status == 'healthy':
                    response_time = health.get('response_time', 0)
                    self.log("INFO", f"Health endpoint is responding (response time: {response_time:.3f}s)")
                    return True
                elif status == 'connecting':
                    self.log("DEBUG", "Health endpoint not yet available...")
                else:
                    self.log("DEBUG", f"Health endpoint status: {status}")
                
                last_status = status
            
            time.sleep(2)
        
        self.log("WARN", "Health endpoint not available (non-critical)")
        return True  # Health endpoint is optional
    
    def _verify_readiness(self) -> bool:
        """Verify application is fully ready"""
        try:
            # Final verification of Streamlit
            streamlit_health = self.check_streamlit_health()
            if streamlit_health.get('status') != 'healthy':
                self.log("ERROR", "Final Streamlit health check failed")
                return False
            
            # Check processes one more time
            processes = self.check_processes()
            if processes.get('streamlit_processes', 0) == 0:
                self.log("ERROR", "No Streamlit processes found during final check")
                return False
            
            # Try to get detailed health information
            try:
                response = requests.get(
                    f'http://localhost:{self.health_port}/health/detailed',
                    timeout=10
                )
                if response.status_code == 200:
                    health_data = response.json()
                    self.log("INFO", f"Detailed health check: {health_data.get('status', 'unknown')}")
            except Exception:
                pass  # Detailed health is optional
            
            return True
            
        except Exception as e:
            self.log("ERROR", f"Error during readiness verification: {str(e)}")
            return False
    
    def get_startup_summary(self) -> Dict[str, Any]:
        """Get startup summary information"""
        elapsed = time.time() - self.start_time
        
        return {
            'startup_time': elapsed,
            'streamlit_health': self.check_streamlit_health(),
            'health_endpoint': self.check_health_endpoint(),
            'processes': self.check_processes(),
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Main function for standalone execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor application startup')
    parser.add_argument('--streamlit-port', type=int, default=8501, help='Streamlit port')
    parser.add_argument('--health-port', type=int, default=8502, help='Health check port')
    parser.add_argument('--timeout', type=int, default=120, help='Startup timeout in seconds')
    parser.add_argument('--json', action='store_true', help='Output JSON summary')
    
    args = parser.parse_args()
    
    monitor = StartupMonitor(
        streamlit_port=args.streamlit_port,
        health_port=args.health_port,
        timeout=args.timeout
    )
    
    print("🚀 Application Startup Monitor")
    print("=" * 40)
    
    success = monitor.wait_for_startup()
    
    if args.json:
        summary = monitor.get_startup_summary()
        summary['startup_successful'] = success
        print("\n📄 Startup Summary (JSON):")
        print(json.dumps(summary, indent=2))
    
    print("=" * 40)
    if success:
        print("✅ Application startup completed successfully!")
        sys.exit(0)
    else:
        print("❌ Application startup failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()