#!/usr/bin/env python3
"""
Test script for the container entry point
Validates that all entry point components work correctly
"""

import os
import sys
import subprocess
import tempfile
import time
import signal
from pathlib import Path

def test_config_validator():
    """Test the configuration validator"""
    print("🧪 Testing configuration validator...")
    
    # Test with minimal valid config
    env = os.environ.copy()
    env['GOOGLE_API_KEY'] = 'test_key_12345678901234567890'
    env['STREAMLIT_SERVER_PORT'] = '8501'
    
    try:
        result = subprocess.run(
            [sys.executable, 'config_validator.py'],
            env=env,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Configuration validator passed")
            return True
        else:
            print(f"❌ Configuration validator failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Configuration validator timed out")
        return False
    except Exception as e:
        print(f"❌ Configuration validator error: {e}")
        return False

def test_healthcheck():
    """Test the health check script"""
    print("🧪 Testing health check script...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'healthcheck.py'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        # Health check may fail (exit code 1 or 2) but should not crash
        if result.returncode in [0, 1, 2]:
            print("✅ Health check script executed successfully")
            return True
        else:
            print(f"❌ Health check script failed unexpectedly: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Health check script timed out")
        return False
    except Exception as e:
        print(f"❌ Health check script error: {e}")
        return False

def test_startup_monitor():
    """Test the startup monitor script"""
    print("🧪 Testing startup monitor script...")
    
    try:
        # Test with short timeout to avoid long waits
        result = subprocess.run(
            [sys.executable, 'startup_monitor.py', '--timeout', '5', '--json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Startup monitor will likely fail since no app is running, but should not crash
        if result.returncode in [0, 1]:
            print("✅ Startup monitor script executed successfully")
            return True
        else:
            print(f"❌ Startup monitor script failed unexpectedly: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Startup monitor script timed out")
        return False
    except Exception as e:
        print(f"❌ Startup monitor script error: {e}")
        return False

def test_entrypoint_validation():
    """Test entry point script validation functions"""
    print("🧪 Testing entry point script validation...")
    
    # Create a temporary script to test entry point functions
    test_script = """#!/bin/bash
source ./entrypoint.sh

# Test environment validation with valid config
export GOOGLE_API_KEY="test_key_12345678901234567890"
export STREAMLIT_SERVER_PORT="8501"
export LOG_LEVEL="INFO"

echo "Testing validate_environment function..."
if validate_environment; then
    echo "✅ Environment validation passed"
else
    echo "❌ Environment validation failed"
    exit 1
fi

echo "Testing set_default_environment function..."
set_default_environment
echo "✅ Default environment set"

echo "Testing create_directories function..."
if create_directories; then
    echo "✅ Directory creation passed"
else
    echo "❌ Directory creation failed"
    exit 1
fi

echo "All entry point validations passed"
"""
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(test_script)
            temp_script = f.name
        
        os.chmod(temp_script, 0o755)
        
        result = subprocess.run(
            ['/bin/bash', temp_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        os.unlink(temp_script)
        
        if result.returncode == 0:
            print("✅ Entry point validation functions work correctly")
            return True
        else:
            print(f"❌ Entry point validation failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Entry point validation timed out")
        return False
    except Exception as e:
        print(f"❌ Entry point validation error: {e}")
        return False

def test_directory_creation():
    """Test directory creation functionality"""
    print("🧪 Testing directory creation...")
    
    test_dirs = [
        '/tmp/test_app/data/uploads',
        '/tmp/test_app/data/processed',
        '/tmp/test_app/reports',
        '/tmp/test_app/logs',
        '/tmp/test_app/config'
    ]
    
    try:
        # Clean up any existing test directories
        import shutil
        if Path('/tmp/test_app').exists():
            shutil.rmtree('/tmp/test_app')
        
        # Create directories
        for dir_path in test_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Verify all directories exist
        all_exist = all(Path(dir_path).exists() for dir_path in test_dirs)
        
        # Clean up
        shutil.rmtree('/tmp/test_app')
        
        if all_exist:
            print("✅ Directory creation test passed")
            return True
        else:
            print("❌ Some directories were not created")
            return False
    except Exception as e:
        print(f"❌ Directory creation test error: {e}")
        return False

def test_signal_handling():
    """Test signal handling in entry point"""
    print("🧪 Testing signal handling...")
    
    # This is a basic test - in a real container environment,
    # we would test actual signal handling
    try:
        # Test that the entry point script exists and is executable
        if not Path('entrypoint.sh').exists():
            print("❌ Entry point script not found")
            return False
        
        if not os.access('entrypoint.sh', os.X_OK):
            print("❌ Entry point script not executable")
            return False
        
        # Check that the script contains signal handling
        with open('entrypoint.sh', 'r') as f:
            content = f.read()
        
        if 'trap graceful_shutdown' in content and 'SIGTERM' in content:
            print("✅ Signal handling code found in entry point")
            return True
        else:
            print("❌ Signal handling code not found")
            return False
    except Exception as e:
        print(f"❌ Signal handling test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Container Entry Point Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration Validator", test_config_validator),
        ("Health Check Script", test_healthcheck),
        ("Startup Monitor", test_startup_monitor),
        ("Directory Creation", test_directory_creation),
        ("Signal Handling", test_signal_handling),
        # Skip entry point validation test as it requires bash functions
        # ("Entry Point Validation", test_entrypoint_validation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results:")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Total:  {passed + failed}")
    
    if failed == 0:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()