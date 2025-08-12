#!/usr/bin/env python3
"""
Configuration validation script for User Behavior Analytics Platform
Validates environment variables and configuration files
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

class ConfigValidator:
    """Configuration validator for the analytics platform"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def validate_api_keys(self) -> bool:
        """Validate API key configuration"""
        google_key = os.getenv('GOOGLE_API_KEY')
        ark_key = os.getenv('ARK_API_KEY')
        
        if not google_key and not ark_key:
            self.errors.append("At least one API key must be provided (GOOGLE_API_KEY or ARK_API_KEY)")
            return False
        
        # Validate Google API key format
        if google_key:
            if len(google_key) < 20:
                self.warnings.append("Google API key seems too short, please verify")
            elif not re.match(r'^[A-Za-z0-9_-]+$', google_key):
                self.warnings.append("Google API key contains unexpected characters")
            else:
                self.info.append("Google API key configured and format looks valid")
        
        # Validate ARK API key format
        if ark_key:
            if len(ark_key) < 20:
                self.warnings.append("ARK API key seems too short, please verify")
            elif not re.match(r'^[A-Za-z0-9_-]+$', ark_key):
                self.warnings.append("ARK API key contains unexpected characters")
            else:
                self.info.append("ARK API key configured and format looks valid")
        
        return True
    
    def validate_streamlit_config(self) -> bool:
        """Validate Streamlit configuration"""
        valid = True
        
        # Validate port
        port_str = os.getenv('STREAMLIT_SERVER_PORT', '8501')
        try:
            port = int(port_str)
            if port < 1024 or port > 65535:
                self.errors.append(f"Streamlit port {port} is outside valid range (1024-65535)")
                valid = False
            elif port < 8000:
                self.warnings.append(f"Streamlit port {port} is below typical range (8000+)")
        except ValueError:
            self.errors.append(f"Invalid Streamlit port: {port_str}")
            valid = False
        
        # Validate address
        address = os.getenv('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')
        if address not in ['0.0.0.0', '127.0.0.1', 'localhost']:
            # Basic IP validation
            if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', address):
                self.warnings.append(f"Streamlit address {address} may not be valid")
        
        # Validate max upload size
        max_upload_str = os.getenv('STREAMLIT_SERVER_MAX_UPLOAD_SIZE', '100')
        try:
            max_upload = int(max_upload_str)
            if max_upload < 1:
                self.errors.append("Max upload size must be at least 1MB")
                valid = False
            elif max_upload > 1000:
                self.warnings.append(f"Max upload size {max_upload}MB is very large")
        except ValueError:
            self.errors.append(f"Invalid max upload size: {max_upload_str}")
            valid = False
        
        # Validate boolean settings
        boolean_settings = [
            ('STREAMLIT_SERVER_HEADLESS', 'true'),
            ('STREAMLIT_BROWSER_GATHER_USAGE_STATS', 'false'),
            ('ENABLE_FALLBACK', 'true'),
            ('ENABLE_MULTIMODAL', 'true')
        ]
        
        for setting, default in boolean_settings:
            value = os.getenv(setting, default).lower()
            if value not in ['true', 'false', '1', '0', 'yes', 'no']:
                self.warnings.append(f"{setting} should be a boolean value (true/false)")
        
        return valid
    
    def validate_llm_config(self) -> bool:
        """Validate LLM configuration"""
        valid = True
        
        # Validate default provider
        default_provider = os.getenv('DEFAULT_LLM_PROVIDER', 'volcano')  # 根据.env文件默认为volcano
        if default_provider not in ['google', 'volcano']:
            self.errors.append(f"Invalid default LLM provider: {default_provider}")
            valid = False
        else:
            self.info.append(f"Default LLM provider set to: {default_provider}")
        
        # Validate enabled providers
        enabled_providers_str = os.getenv('ENABLED_PROVIDERS', '["volcano", "google"]')  # 根据.env文件顺序
        try:
            enabled_providers = json.loads(enabled_providers_str)
            if not isinstance(enabled_providers, list):
                self.errors.append("ENABLED_PROVIDERS must be a JSON array")
                valid = False
            else:
                valid_providers = []
                for provider in enabled_providers:
                    if provider not in ['google', 'volcano']:
                        self.errors.append(f"Invalid provider in ENABLED_PROVIDERS: {provider}")
                        valid = False
                    else:
                        valid_providers.append(provider)
                
                if valid_providers:
                    self.info.append(f"Enabled providers: {', '.join(valid_providers)}")
        except json.JSONDecodeError:
            self.errors.append("ENABLED_PROVIDERS must be valid JSON array")
            valid = False
        
        # Validate temperature
        temp_str = os.getenv('LLM_TEMPERATURE', '0.1')
        try:
            temp = float(temp_str)
            if temp < 0 or temp > 2:
                self.warnings.append(f"LLM temperature {temp} is outside typical range (0-2)")
        except ValueError:
            self.errors.append(f"Invalid LLM temperature: {temp_str}")
            valid = False
        
        # Validate max tokens
        tokens_str = os.getenv('LLM_MAX_TOKENS', '4000')
        try:
            tokens = int(tokens_str)
            if tokens < 100:
                self.errors.append("LLM max tokens must be at least 100")
                valid = False
            elif tokens > 32000:
                self.warnings.append(f"LLM max tokens {tokens} is very high")
        except ValueError:
            self.errors.append(f"Invalid LLM max tokens: {tokens_str}")
            valid = False
        
        # Validate ARK base URL
        ark_url = os.getenv('ARK_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3')
        if not ark_url.startswith('http'):
            self.errors.append("ARK_BASE_URL must be a valid HTTP/HTTPS URL")
            valid = False
        
        # Validate ARK model
        ark_model = os.getenv('ARK_MODEL', 'doubao-seed-1-6-250615')
        if ark_model:
            self.info.append(f"ARK model configured: {ark_model}")
        
        # Validate fallback configuration
        enable_fallback = os.getenv('ENABLE_FALLBACK', 'true').lower()
        if enable_fallback in ['true', '1', 'yes']:
            fallback_order_str = os.getenv('FALLBACK_ORDER', '["volcano", "google"]')  # 根据.env文件顺序
            try:
                fallback_order = json.loads(fallback_order_str)
                if not isinstance(fallback_order, list):
                    self.errors.append("FALLBACK_ORDER must be a JSON array")
                    valid = False
                else:
                    valid_fallback = []
                    for provider in fallback_order:
                        if provider not in ['google', 'volcano']:
                            self.errors.append(f"Invalid provider in FALLBACK_ORDER: {provider}")
                            valid = False
                        else:
                            valid_fallback.append(provider)
                    
                    if valid_fallback:
                        self.info.append(f"Fallback enabled, order: {' -> '.join(valid_fallback)}")
            except json.JSONDecodeError:
                self.errors.append("FALLBACK_ORDER must be valid JSON array")
                valid = False
        else:
            self.info.append("Fallback mechanism disabled")
        
        return valid
    
    def validate_directories(self) -> bool:
        """Validate required directories"""
        required_dirs = [
            '/app/data',
            '/app/data/uploads',
            '/app/data/processed',
            '/app/reports',
            '/app/logs',
            '/app/config'
        ]
        
        valid = True
        for dir_path in required_dirs:
            path_obj = Path(dir_path)
            
            if not path_obj.exists():
                self.warnings.append(f"Directory does not exist: {dir_path} (will be created)")
            elif not path_obj.is_dir():
                self.errors.append(f"Path exists but is not a directory: {dir_path}")
                valid = False
            elif not os.access(dir_path, os.W_OK):
                self.warnings.append(f"Directory is not writable: {dir_path}")
        
        return valid
    
    def validate_log_level(self) -> bool:
        """Validate log level configuration"""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        valid_levels = ['DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'CRITICAL']
        
        if log_level not in valid_levels:
            self.warnings.append(f"Invalid log level: {log_level}, defaulting to INFO")
            return False
        
        return True
    
    def validate_multimodal_config(self) -> bool:
        """Validate multimodal configuration"""
        valid = True
        
        # Validate max image size
        max_size_str = os.getenv('MAX_IMAGE_SIZE_MB', '10')
        try:
            max_size = int(max_size_str)
            if max_size < 1:
                self.errors.append("Max image size must be at least 1MB")
                valid = False
            elif max_size > 100:
                self.warnings.append(f"Max image size {max_size}MB is very large")
        except ValueError:
            self.errors.append(f"Invalid max image size: {max_size_str}")
            valid = False
        
        # Validate supported formats
        formats_str = os.getenv('SUPPORTED_IMAGE_FORMATS', '["jpg", "jpeg", "png", "gif", "webp"]')
        try:
            formats = json.loads(formats_str)
            if not isinstance(formats, list):
                self.errors.append("SUPPORTED_IMAGE_FORMATS must be a JSON array")
                valid = False
            else:
                valid_formats = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff']
                for fmt in formats:
                    if fmt.lower() not in valid_formats:
                        self.warnings.append(f"Unsupported image format: {fmt}")
        except json.JSONDecodeError:
            self.errors.append("SUPPORTED_IMAGE_FORMATS must be valid JSON array")
            valid = False
        
        # Validate timeout
        timeout_str = os.getenv('IMAGE_ANALYSIS_TIMEOUT', '60')
        try:
            timeout = int(timeout_str)
            if timeout < 10:
                self.warnings.append("Image analysis timeout is very short")
            elif timeout > 300:
                self.warnings.append("Image analysis timeout is very long")
        except ValueError:
            self.errors.append(f"Invalid image analysis timeout: {timeout_str}")
            valid = False
        
        return valid
    
    def validate_all(self) -> Tuple[bool, Dict[str, Any]]:
        """Run all validations and return results"""
        self.errors.clear()
        self.warnings.clear()
        self.info.clear()
        
        validations = [
            ('API Keys', self.validate_api_keys),
            ('Streamlit Config', self.validate_streamlit_config),
            ('LLM Config', self.validate_llm_config),
            ('Directories', self.validate_directories),
            ('Log Level', self.validate_log_level),
            ('Multimodal Config', self.validate_multimodal_config)
        ]
        
        results = {}
        overall_valid = True
        
        for name, validator in validations:
            try:
                valid = validator()
                results[name] = {
                    'valid': valid,
                    'status': 'passed' if valid else 'failed'
                }
                if not valid:
                    overall_valid = False
            except Exception as e:
                results[name] = {
                    'valid': False,
                    'status': 'error',
                    'error': str(e)
                }
                overall_valid = False
                self.errors.append(f"Validation error in {name}: {str(e)}")
        
        return overall_valid, {
            'overall_valid': overall_valid,
            'validations': results,
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info,
            'summary': {
                'total_validations': len(validations),
                'passed': sum(1 for r in results.values() if r['valid']),
                'failed': sum(1 for r in results.values() if not r['valid']),
                'errors': len(self.errors),
                'warnings': len(self.warnings)
            }
        }

def main():
    """Main function for standalone execution"""
    print("🔧 Configuration Validation")
    print("=" * 40)
    
    validator = ConfigValidator()
    is_valid, report = validator.validate_all()
    
    # Print summary
    summary = report['summary']
    print(f"📊 Validation Summary:")
    print(f"   Total Checks: {summary['total_validations']}")
    print(f"   Passed: {summary['passed']}")
    print(f"   Failed: {summary['failed']}")
    print(f"   Errors: {summary['errors']}")
    print(f"   Warnings: {summary['warnings']}")
    print()
    
    # Print detailed results
    for name, result in report['validations'].items():
        status = result['status']
        if status == 'passed':
            print(f"✅ {name}: PASSED")
        elif status == 'failed':
            print(f"❌ {name}: FAILED")
        else:
            print(f"⚠️  {name}: ERROR")
            if 'error' in result:
                print(f"   Error: {result['error']}")
    
    print()
    
    # Print errors
    if report['errors']:
        print("❌ Errors:")
        for error in report['errors']:
            print(f"   - {error}")
        print()
    
    # Print warnings
    if report['warnings']:
        print("⚠️  Warnings:")
        for warning in report['warnings']:
            print(f"   - {warning}")
        print()
    
    # Print info messages
    if report['info']:
        print("ℹ️  Information:")
        for info in report['info']:
            print(f"   - {info}")
        print()
    
    print("=" * 40)
    print(f"🎯 Overall Status: {'VALID' if is_valid else 'INVALID'}")
    
    # Output JSON if requested
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        print("\n📄 JSON Output:")
        print(json.dumps(report, indent=2))
    
    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)

if __name__ == '__main__':
    main()