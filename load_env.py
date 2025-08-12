#!/usr/bin/env python3
"""
Environment variable loader for .env file
Handles JSON arrays and special characters properly
"""

import os
import sys
from pathlib import Path

def load_env_file(env_file_path: str = '.env'):
    """Load environment variables from .env file"""
    env_file = Path(env_file_path)
    
    if not env_file.exists():
        print(f"Warning: {env_file_path} not found")
        return {}
    
    env_vars = {}
    
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    env_vars[key] = value
                else:
                    print(f"Warning: Invalid line {line_num} in {env_file_path}: {line}")
    
    except Exception as e:
        print(f"Error reading {env_file_path}: {e}")
        return {}
    
    return env_vars

def set_environment_variables(env_vars: dict):
    """Set environment variables from dictionary"""
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"Set {key}={value[:20]}{'...' if len(value) > 20 else ''}")

def main():
    """Main function for standalone execution"""
    env_file = sys.argv[1] if len(sys.argv) > 1 else '.env'
    
    print(f"Loading environment variables from {env_file}")
    print("=" * 50)
    
    env_vars = load_env_file(env_file)
    
    if env_vars:
        set_environment_variables(env_vars)
        print("=" * 50)
        print(f"Loaded {len(env_vars)} environment variables")
    else:
        print("No environment variables loaded")
        sys.exit(1)

if __name__ == '__main__':
    main()