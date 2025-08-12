#!/usr/bin/env python3
"""
Secure Environment Variable Handler
User Behavior Analytics Platform
Handles secure loading and validation of environment variables and secrets
"""

import os
import sys
import json
import base64
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SecretConfig:
    """Configuration for secret handling"""
    name: str
    required: bool = True
    pattern: Optional[str] = None
    min_length: int = 8
    max_length: int = 512
    encoding: str = "utf-8"
    source: str = "env"  # env, file, vault
    validation_rules: List[str] = None

class SecureEnvironmentHandler:
    """Handles secure environment variable and secret management"""
    
    def __init__(self, secrets_dir: str = "/app/secrets"):
        self.secrets_dir = Path(secrets_dir)
        self.loaded_secrets: Dict[str, str] = {}
        self.validation_errors: List[str] = []
        self.security_warnings: List[str] = []
        
        # Define secret configurations
        self.secret_configs = {
            'GOOGLE_API_KEY': SecretConfig(
                name='GOOGLE_API_KEY',
                required=False,
                pattern=r'^[A-Za-z0-9_-]{20,}$',
                min_length=20,
                max_length=100
            ),
            'ARK_API_KEY': SecretConfig(
                name='ARK_API_KEY',
                required=False,
                pattern=r'^[A-Za-z0-9_-]{20,}$',
                min_length=20,
                max_length=100
            ),
            'SESSION_SECRET': SecretConfig(
                name='SESSION_SECRET',
                required=False,
                min_length=32,
                max_length=128
            ),
            'ENCRYPTION_KEY': SecretConfig(
                name='ENCRYPTION_KEY',
                required=False,
                min_length=32,
                max_length=64
            )
        }
        
        # Sensitive environment variable patterns
        self.sensitive_patterns = [
            r'.*_API_KEY$',
            r'.*_SECRET$',
            r'.*_TOKEN$',
            r'.*_PASSWORD$',
            r'.*_PRIVATE_KEY$',
            r'.*_CERT$'
        ]
    
    def load_secrets(self) -> bool:
        """Load secrets from various sources"""
        success = True
        
        # Load from environment variables
        success &= self._load_from_environment()
        
        # Load from Docker secrets (if available)
        success &= self._load_from_docker_secrets()
        
        # Load from Kubernetes secrets (if available)
        success &= self._load_from_k8s_secrets()
        
        # Load from files (if available)
        success &= self._load_from_files()
        
        # Validate all loaded secrets
        success &= self._validate_secrets()
        
        return success
    
    def _load_from_environment(self) -> bool:
        """Load secrets from environment variables"""
        logger.info("Loading secrets from environment variables...")
        
        for env_var, config in self.secret_configs.items():
            value = os.getenv(env_var)
            if value:
                self.loaded_secrets[env_var] = value
                logger.debug(f"Loaded {env_var} from environment")
            elif config.required:
                self.validation_errors.append(f"Required secret {env_var} not found in environment")
                return False
        
        # Check for other sensitive environment variables
        for key, value in os.environ.items():
            if self._is_sensitive_variable(key) and key not in self.loaded_secrets:
                self.loaded_secrets[key] = value
                logger.debug(f"Detected sensitive variable: {key}")
        
        return True
    
    def _load_from_docker_secrets(self) -> bool:
        """Load secrets from Docker secrets mount point"""
        docker_secrets_dir = Path("/run/secrets")
        
        if not docker_secrets_dir.exists():
            logger.debug("Docker secrets directory not found")
            return True
        
        logger.info("Loading secrets from Docker secrets...")
        
        for secret_file in docker_secrets_dir.iterdir():
            if secret_file.is_file():
                try:
                    secret_name = secret_file.name.upper()
                    with open(secret_file, 'r', encoding='utf-8') as f:
                        secret_value = f.read().strip()
                    
                    self.loaded_secrets[secret_name] = secret_value
                    logger.debug(f"Loaded {secret_name} from Docker secrets")
                    
                    # Set environment variable for application use
                    os.environ[secret_name] = secret_value
                    
                except Exception as e:
                    logger.error(f"Failed to load Docker secret {secret_file.name}: {e}")
                    return False
        
        return True
    
    def _load_from_k8s_secrets(self) -> bool:
        """Load secrets from Kubernetes secrets mount point"""
        k8s_secrets_dir = Path("/var/secrets")
        
        if not k8s_secrets_dir.exists():
            logger.debug("Kubernetes secrets directory not found")
            return True
        
        logger.info("Loading secrets from Kubernetes secrets...")
        
        for secret_file in k8s_secrets_dir.iterdir():
            if secret_file.is_file():
                try:
                    secret_name = secret_file.name.upper()
                    with open(secret_file, 'r', encoding='utf-8') as f:
                        secret_value = f.read().strip()
                    
                    self.loaded_secrets[secret_name] = secret_value
                    logger.debug(f"Loaded {secret_name} from Kubernetes secrets")
                    
                    # Set environment variable for application use
                    os.environ[secret_name] = secret_value
                    
                except Exception as e:
                    logger.error(f"Failed to load Kubernetes secret {secret_file.name}: {e}")
                    return False
        
        return True
    
    def _load_from_files(self) -> bool:
        """Load secrets from local files"""
        if not self.secrets_dir.exists():
            logger.debug(f"Secrets directory not found: {self.secrets_dir}")
            return True
        
        logger.info(f"Loading secrets from files in {self.secrets_dir}...")
        
        for secret_file in self.secrets_dir.iterdir():
            if secret_file.is_file() and not secret_file.name.startswith('.'):
                try:
                    secret_name = secret_file.stem.upper()
                    with open(secret_file, 'r', encoding='utf-8') as f:
                        secret_value = f.read().strip()
                    
                    self.loaded_secrets[secret_name] = secret_value
                    logger.debug(f"Loaded {secret_name} from file")
                    
                    # Set environment variable for application use
                    os.environ[secret_name] = secret_value
                    
                except Exception as e:
                    logger.error(f"Failed to load secret from file {secret_file}: {e}")
                    return False
        
        return True
    
    def _validate_secrets(self) -> bool:
        """Validate all loaded secrets"""
        logger.info("Validating loaded secrets...")
        
        validation_success = True
        
        for secret_name, secret_value in self.loaded_secrets.items():
            config = self.secret_configs.get(secret_name)
            
            if config:
                if not self._validate_secret(secret_name, secret_value, config):
                    validation_success = False
            else:
                # Generic validation for unknown secrets
                if not self._validate_generic_secret(secret_name, secret_value):
                    validation_success = False
        
        # Check for required secrets
        for secret_name, config in self.secret_configs.items():
            if config.required and secret_name not in self.loaded_secrets:
                self.validation_errors.append(f"Required secret {secret_name} not found")
                validation_success = False
        
        return validation_success
    
    def _validate_secret(self, name: str, value: str, config: SecretConfig) -> bool:
        """Validate a specific secret against its configuration"""
        if len(value) < config.min_length:
            self.validation_errors.append(f"Secret {name} is too short (min: {config.min_length})")
            return False
        
        if len(value) > config.max_length:
            self.validation_errors.append(f"Secret {name} is too long (max: {config.max_length})")
            return False
        
        if config.pattern and not re.match(config.pattern, value):
            self.validation_errors.append(f"Secret {name} does not match required pattern")
            return False
        
        return True
    
    def _validate_generic_secret(self, name: str, value: str) -> bool:
        """Generic validation for unknown secrets"""
        if len(value) < 8:
            self.security_warnings.append(f"Secret {name} is very short, consider using a longer value")
        
        if value.isdigit():
            self.security_warnings.append(f"Secret {name} contains only digits, consider using mixed characters")
        
        return True
    
    def _is_sensitive_variable(self, var_name: str) -> bool:
        """Check if a variable name matches sensitive patterns"""
        for pattern in self.sensitive_patterns:
            if re.match(pattern, var_name, re.IGNORECASE):
                return True
        return False
    
    def mask_sensitive_value(self, value: str, show_chars: int = 4) -> str:
        """Mask sensitive values for logging"""
        if len(value) <= show_chars * 2:
            return '*' * len(value)
        return value[:show_chars] + '*' * (len(value) - show_chars * 2) + value[-show_chars:]
    
    def get_security_report(self) -> Dict[str, Any]:
        """Get a security report of loaded secrets"""
        report = {
            'total_secrets': len(self.loaded_secrets),
            'validation_errors': self.validation_errors,
            'security_warnings': self.security_warnings,
            'secrets_summary': {}
        }
        
        for name, value in self.loaded_secrets.items():
            report['secrets_summary'][name] = {
                'length': len(value),
                'source': 'environment',  # Simplified for now
                'masked_value': self.mask_sensitive_value(value),
                'is_configured': True
            }
        
        return report
    
    def cleanup_environment(self):
        """Clean up sensitive environment variables from memory"""
        logger.info("Cleaning up sensitive environment variables...")
        
        for var_name in list(os.environ.keys()):
            if self._is_sensitive_variable(var_name):
                # Don't actually remove from os.environ as the app needs them
                # This is more for logging/auditing purposes
                logger.debug(f"Sensitive variable detected: {var_name}")

def load_secure_environment() -> SecureEnvironmentHandler:
    """Load and validate secure environment configuration"""
    handler = SecureEnvironmentHandler()
    
    if not handler.load_secrets():
        logger.error("Failed to load secrets securely")
        for error in handler.validation_errors:
            logger.error(f"Validation error: {error}")
        sys.exit(1)
    
    if handler.security_warnings:
        for warning in handler.security_warnings:
            logger.warning(f"Security warning: {warning}")
    
    return handler

def main():
    """Main function for standalone execution"""
    print("🔐 Secure Environment Handler")
    print("=" * 40)
    
    try:
        handler = load_secure_environment()
        report = handler.get_security_report()
        
        print(f"📊 Security Report:")
        print(f"   Total Secrets: {report['total_secrets']}")
        print(f"   Validation Errors: {len(report['validation_errors'])}")
        print(f"   Security Warnings: {len(report['security_warnings'])}")
        print()
        
        if report['validation_errors']:
            print("❌ Validation Errors:")
            for error in report['validation_errors']:
                print(f"   - {error}")
            print()
        
        if report['security_warnings']:
            print("⚠️  Security Warnings:")
            for warning in report['security_warnings']:
                print(f"   - {warning}")
            print()
        
        print("🔑 Loaded Secrets:")
        for name, info in report['secrets_summary'].items():
            print(f"   - {name}: {info['masked_value']} (length: {info['length']})")
        
        print()
        print("=" * 40)
        print("🎯 Secure environment loaded successfully!")
        
    except Exception as e:
        print(f"❌ Failed to load secure environment: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
