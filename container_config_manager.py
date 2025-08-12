#!/usr/bin/env python3
"""
Container Configuration Manager for User Behavior Analytics Platform
Handles environment variable mapping, external configuration files, and validation
"""

import os
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from config_validator import ConfigValidator

@dataclass
class ContainerConfig:
    """Container configuration data model"""
    # Streamlit Configuration
    port: int = 8501
    host: str = "0.0.0.0"
    headless: bool = True
    max_upload_size: int = 100
    gather_usage_stats: bool = False
    
    # Application Configuration
    app_title: str = "用户行为分析智能体平台"
    log_level: str = "INFO"
    debug_mode: bool = False
    
    # Directory Configuration
    data_dir: str = "/app/data"
    config_dir: str = "/app/config"
    logs_dir: str = "/app/logs"
    reports_dir: str = "/app/reports"
    uploads_dir: str = "/app/data/uploads"
    processed_dir: str = "/app/data/processed"
    
    # API Configuration
    google_api_key: Optional[str] = None
    ark_api_key: Optional[str] = None
    ark_base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    ark_model: str = "doubao-seed-1-6-250615"
    
    # LLM Configuration
    default_llm_provider: str = "volcano"
    enabled_providers: List[str] = field(default_factory=lambda: ["volcano", "google"])
    enable_fallback: bool = True
    fallback_order: List[str] = field(default_factory=lambda: ["volcano", "google"])
    llm_model: str = "gemini-2.5-pro"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4000
    
    # Multimodal Configuration
    enable_multimodal: bool = True
    max_image_size_mb: int = 10
    supported_image_formats: List[str] = field(default_factory=lambda: ["jpg", "jpeg", "png", "gif", "webp"])
    image_analysis_timeout: int = 60
    
    # Security Configuration
    enable_cors: bool = False
    enable_xsrf_protection: bool = True
    session_timeout: int = 3600
    
    # Performance Configuration
    max_concurrent_requests: int = 10
    request_timeout: int = 300
    memory_limit: str = "4G"
    cpu_limit: float = 2.0
    cache_enabled: bool = True
    cache_ttl: int = 3600

class ContainerConfigManager:
    """Manages container configuration from multiple sources"""
    
    def __init__(self, config_dir: str = "/app/config"):
        self.config_dir = Path(config_dir)
        self.validator = ConfigValidator()
        self.config = ContainerConfig()
        self.loaded_sources: List[str] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def load_from_environment(self) -> bool:
        """Load configuration from environment variables"""
        try:
            # Streamlit Configuration
            self.config.port = int(os.getenv('STREAMLIT_SERVER_PORT', '8501'))
            self.config.host = os.getenv('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')
            self.config.headless = self._parse_bool(os.getenv('STREAMLIT_SERVER_HEADLESS', 'true'))
            self.config.max_upload_size = int(os.getenv('STREAMLIT_SERVER_MAX_UPLOAD_SIZE', '100'))
            self.config.gather_usage_stats = self._parse_bool(os.getenv('STREAMLIT_BROWSER_GATHER_USAGE_STATS', 'false'))
            
            # Application Configuration
            self.config.app_title = os.getenv('APP_TITLE', '用户行为分析智能体平台')
            self.config.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
            self.config.debug_mode = self._parse_bool(os.getenv('DEBUG_MODE', 'false'))
            
            # Directory Configuration
            self.config.data_dir = os.getenv('DATA_DIR', '/app/data')
            self.config.config_dir = os.getenv('CONFIG_DIR', '/app/config')
            self.config.logs_dir = os.getenv('LOGS_DIR', '/app/logs')
            self.config.reports_dir = os.getenv('REPORTS_DIR', '/app/reports')
            self.config.uploads_dir = os.getenv('UPLOADS_DIR', '/app/data/uploads')
            self.config.processed_dir = os.getenv('PROCESSED_DIR', '/app/data/processed')
            
            # API Configuration
            self.config.google_api_key = os.getenv('GOOGLE_API_KEY')
            self.config.ark_api_key = os.getenv('ARK_API_KEY')
            self.config.ark_base_url = os.getenv('ARK_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3')
            self.config.ark_model = os.getenv('ARK_MODEL', 'doubao-seed-1-6-250615')
            
            # LLM Configuration
            self.config.default_llm_provider = os.getenv('DEFAULT_LLM_PROVIDER', 'volcano')
            self.config.enabled_providers = self._parse_json_list(os.getenv('ENABLED_PROVIDERS', '["volcano", "google"]'))
            self.config.enable_fallback = self._parse_bool(os.getenv('ENABLE_FALLBACK', 'true'))
            self.config.fallback_order = self._parse_json_list(os.getenv('FALLBACK_ORDER', '["volcano", "google"]'))
            self.config.llm_model = os.getenv('LLM_MODEL', 'gemini-2.5-pro')
            self.config.llm_temperature = float(os.getenv('LLM_TEMPERATURE', '0.1'))
            self.config.llm_max_tokens = int(os.getenv('LLM_MAX_TOKENS', '4000'))
            
            # Multimodal Configuration
            self.config.enable_multimodal = self._parse_bool(os.getenv('ENABLE_MULTIMODAL', 'true'))
            self.config.max_image_size_mb = int(os.getenv('MAX_IMAGE_SIZE_MB', '10'))
            self.config.supported_image_formats = self._parse_json_list(os.getenv('SUPPORTED_IMAGE_FORMATS', '["jpg", "jpeg", "png", "gif", "webp"]'))
            self.config.image_analysis_timeout = int(os.getenv('IMAGE_ANALYSIS_TIMEOUT', '60'))
            
            # Security Configuration
            self.config.enable_cors = self._parse_bool(os.getenv('ENABLE_CORS', 'false'))
            self.config.enable_xsrf_protection = self._parse_bool(os.getenv('ENABLE_XSRF_PROTECTION', 'true'))
            self.config.session_timeout = int(os.getenv('SESSION_TIMEOUT', '3600'))
            
            # Performance Configuration
            self.config.max_concurrent_requests = int(os.getenv('MAX_CONCURRENT_REQUESTS', '10'))
            self.config.request_timeout = int(os.getenv('REQUEST_TIMEOUT', '300'))
            self.config.memory_limit = os.getenv('MEMORY_LIMIT', '4G')
            self.config.cpu_limit = float(os.getenv('CPU_LIMIT', '2.0'))
            self.config.cache_enabled = self._parse_bool(os.getenv('CACHE_ENABLED', 'true'))
            self.config.cache_ttl = int(os.getenv('CACHE_TTL', '3600'))
            
            self.loaded_sources.append("environment")
            return True
            
        except Exception as e:
            self.errors.append(f"Error loading environment configuration: {str(e)}")
            return False
    
    def load_from_file(self, config_file: Union[str, Path]) -> bool:
        """Load configuration from external file (JSON or YAML)"""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                self.warnings.append(f"Configuration file not found: {config_path}")
                return False
            
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yml', '.yaml']:
                    file_config = yaml.safe_load(f)
                else:
                    file_config = json.load(f)
            
            # Merge file configuration with current configuration
            self._merge_config(file_config)
            self.loaded_sources.append(str(config_path))
            return True
            
        except Exception as e:
            self.errors.append(f"Error loading configuration file {config_file}: {str(e)}")
            return False
    
    def load_from_directory(self, config_dir: Optional[str] = None) -> bool:
        """Load configuration from all files in config directory"""
        if config_dir:
            self.config_dir = Path(config_dir)
        
        if not self.config_dir.exists():
            self.warnings.append(f"Configuration directory not found: {self.config_dir}")
            return False
        
        success = True
        config_files = list(self.config_dir.glob("*.json")) + list(self.config_dir.glob("*.yml")) + list(self.config_dir.glob("*.yaml"))
        
        for config_file in sorted(config_files):
            if not self.load_from_file(config_file):
                success = False
        
        return success
    
    def validate_configuration(self) -> bool:
        """Validate the loaded configuration"""
        # Set environment variables for validator
        self._set_env_vars_for_validation()
        
        # Run validation
        is_valid, report = self.validator.validate_all()
        
        # Collect validation results
        if report['errors']:
            self.errors.extend(report['errors'])
        if report['warnings']:
            self.warnings.extend(report['warnings'])
        
        return is_valid
    
    def create_directories(self) -> bool:
        """Create required directories with proper permissions"""
        directories = [
            self.config.data_dir,
            self.config.uploads_dir,
            self.config.processed_dir,
            self.config.reports_dir,
            self.config.logs_dir,
            f"{self.config.logs_dir}/monitoring",
            self.config.config_dir
        ]
        
        success = True
        for dir_path in directories:
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                # Set appropriate permissions
                if any(subdir in dir_path for subdir in ['uploads', 'processed', 'reports', 'logs']):
                    os.chmod(dir_path, 0o775)
                else:
                    os.chmod(dir_path, 0o755)
            except Exception as e:
                self.errors.append(f"Failed to create directory {dir_path}: {str(e)}")
                success = False
        
        return success
    
    def export_environment_variables(self) -> Dict[str, str]:
        """Export configuration as environment variables"""
        env_vars = {
            # Streamlit Configuration
            'STREAMLIT_SERVER_PORT': str(self.config.port),
            'STREAMLIT_SERVER_ADDRESS': self.config.host,
            'STREAMLIT_SERVER_HEADLESS': str(self.config.headless).lower(),
            'STREAMLIT_SERVER_MAX_UPLOAD_SIZE': str(self.config.max_upload_size),
            'STREAMLIT_BROWSER_GATHER_USAGE_STATS': str(self.config.gather_usage_stats).lower(),
            
            # Application Configuration
            'APP_TITLE': self.config.app_title,
            'LOG_LEVEL': self.config.log_level,
            'DEBUG_MODE': str(self.config.debug_mode).lower(),
            
            # Directory Configuration
            'DATA_DIR': self.config.data_dir,
            'CONFIG_DIR': self.config.config_dir,
            'LOGS_DIR': self.config.logs_dir,
            'REPORTS_DIR': self.config.reports_dir,
            'UPLOADS_DIR': self.config.uploads_dir,
            'PROCESSED_DIR': self.config.processed_dir,
            
            # LLM Configuration
            'DEFAULT_LLM_PROVIDER': self.config.default_llm_provider,
            'ENABLED_PROVIDERS': json.dumps(self.config.enabled_providers),
            'ENABLE_FALLBACK': str(self.config.enable_fallback).lower(),
            'FALLBACK_ORDER': json.dumps(self.config.fallback_order),
            'LLM_MODEL': self.config.llm_model,
            'LLM_TEMPERATURE': str(self.config.llm_temperature),
            'LLM_MAX_TOKENS': str(self.config.llm_max_tokens),
            
            # Multimodal Configuration
            'ENABLE_MULTIMODAL': str(self.config.enable_multimodal).lower(),
            'MAX_IMAGE_SIZE_MB': str(self.config.max_image_size_mb),
            'SUPPORTED_IMAGE_FORMATS': json.dumps(self.config.supported_image_formats),
            'IMAGE_ANALYSIS_TIMEOUT': str(self.config.image_analysis_timeout),
            
            # Security Configuration
            'ENABLE_CORS': str(self.config.enable_cors).lower(),
            'ENABLE_XSRF_PROTECTION': str(self.config.enable_xsrf_protection).lower(),
            'SESSION_TIMEOUT': str(self.config.session_timeout),
            
            # Performance Configuration
            'MAX_CONCURRENT_REQUESTS': str(self.config.max_concurrent_requests),
            'REQUEST_TIMEOUT': str(self.config.request_timeout),
            'MEMORY_LIMIT': self.config.memory_limit,
            'CPU_LIMIT': str(self.config.cpu_limit),
            'CACHE_ENABLED': str(self.config.cache_enabled).lower(),
            'CACHE_TTL': str(self.config.cache_ttl),
        }
        
        # Add API keys if present
        if self.config.google_api_key:
            env_vars['GOOGLE_API_KEY'] = self.config.google_api_key
        if self.config.ark_api_key:
            env_vars['ARK_API_KEY'] = self.config.ark_api_key
            env_vars['ARK_BASE_URL'] = self.config.ark_base_url
            env_vars['ARK_MODEL'] = self.config.ark_model
        
        return env_vars
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the loaded configuration"""
        return {
            'loaded_sources': self.loaded_sources,
            'errors': self.errors,
            'warnings': self.warnings,
            'config': {
                'streamlit': {
                    'port': self.config.port,
                    'host': self.config.host,
                    'headless': self.config.headless,
                    'max_upload_size': self.config.max_upload_size
                },
                'application': {
                    'title': self.config.app_title,
                    'log_level': self.config.log_level,
                    'debug_mode': self.config.debug_mode
                },
                'llm': {
                    'default_provider': self.config.default_llm_provider,
                    'enabled_providers': self.config.enabled_providers,
                    'enable_fallback': self.config.enable_fallback,
                    'model': self.config.llm_model,
                    'temperature': self.config.llm_temperature,
                    'max_tokens': self.config.llm_max_tokens
                },
                'api_keys': {
                    'google_configured': bool(self.config.google_api_key),
                    'ark_configured': bool(self.config.ark_api_key)
                },
                'multimodal': {
                    'enabled': self.config.enable_multimodal,
                    'max_image_size_mb': self.config.max_image_size_mb,
                    'supported_formats': self.config.supported_image_formats
                }
            }
        }
    
    def _parse_bool(self, value: str) -> bool:
        """Parse boolean value from string"""
        return value.lower() in ['true', '1', 'yes', 'on']
    
    def _parse_json_list(self, value: str) -> List[str]:
        """Parse JSON list from string"""
        try:
            result = json.loads(value)
            return result if isinstance(result, list) else []
        except json.JSONDecodeError:
            return []
    
    def _merge_config(self, file_config: Dict[str, Any]) -> None:
        """Merge file configuration with current configuration"""
        # This is a simplified merge - in production, you might want more sophisticated merging
        for key, value in file_config.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def _set_env_vars_for_validation(self) -> None:
        """Set environment variables for validator"""
        env_vars = self.export_environment_variables()
        for key, value in env_vars.items():
            os.environ[key] = value

def load_container_configuration(config_dir: str = "/app/config") -> ContainerConfigManager:
    """Load and validate container configuration from all sources"""
    manager = ContainerConfigManager(config_dir)

    # Load from environment variables first
    manager.load_from_environment()

    # Load from configuration directory
    manager.load_from_directory()

    # Create required directories
    manager.create_directories()

    # Validate configuration
    is_valid = manager.validate_configuration()

    if not is_valid:
        print("❌ Configuration validation failed!")
        for error in manager.errors:
            print(f"   Error: {error}")
        sys.exit(1)

    if manager.warnings:
        print("⚠️  Configuration warnings:")
        for warning in manager.warnings:
            print(f"   Warning: {warning}")

    return manager

def main():
    """Main function for standalone execution"""
    print("🔧 Container Configuration Manager")
    print("=" * 50)

    # Load configuration
    try:
        config_manager = load_container_configuration()

        # Get configuration summary
        summary = config_manager.get_config_summary()

        print("📊 Configuration Summary:")
        print(f"   Sources: {', '.join(summary['loaded_sources'])}")
        print(f"   Errors: {len(summary['errors'])}")
        print(f"   Warnings: {len(summary['warnings'])}")
        print()

        # Print configuration details
        config = summary['config']
        print("🌐 Streamlit Configuration:")
        print(f"   Host: {config['streamlit']['host']}")
        print(f"   Port: {config['streamlit']['port']}")
        print(f"   Headless: {config['streamlit']['headless']}")
        print(f"   Max Upload: {config['streamlit']['max_upload_size']}MB")
        print()

        print("🤖 LLM Configuration:")
        print(f"   Default Provider: {config['llm']['default_provider']}")
        print(f"   Enabled Providers: {', '.join(config['llm']['enabled_providers'])}")
        print(f"   Fallback Enabled: {config['llm']['enable_fallback']}")
        print(f"   Model: {config['llm']['model']}")
        print(f"   Temperature: {config['llm']['temperature']}")
        print(f"   Max Tokens: {config['llm']['max_tokens']}")
        print()

        print("🔑 API Keys:")
        print(f"   Google API: {'✅ Configured' if config['api_keys']['google_configured'] else '❌ Not configured'}")
        print(f"   ARK API: {'✅ Configured' if config['api_keys']['ark_configured'] else '❌ Not configured'}")
        print()

        print("🖼️  Multimodal Configuration:")
        print(f"   Enabled: {config['multimodal']['enabled']}")
        print(f"   Max Image Size: {config['multimodal']['max_image_size_mb']}MB")
        print(f"   Supported Formats: {', '.join(config['multimodal']['supported_formats'])}")
        print()

        # Export environment variables if requested
        if len(sys.argv) > 1 and sys.argv[1] == '--export':
            print("📤 Environment Variables:")
            env_vars = config_manager.export_environment_variables()
            for key, value in sorted(env_vars.items()):
                # Mask sensitive values
                if 'API_KEY' in key and value:
                    masked_value = value[:8] + '*' * (len(value) - 8) if len(value) > 8 else '*' * len(value)
                    print(f"   {key}={masked_value}")
                else:
                    print(f"   {key}={value}")
            print()

        # Output JSON if requested
        if len(sys.argv) > 1 and sys.argv[1] == '--json':
            print("📄 JSON Output:")
            # Remove sensitive data for JSON output
            json_summary = summary.copy()
            if 'api_keys' in json_summary['config']:
                json_summary['config']['api_keys'] = {
                    'google_configured': config['api_keys']['google_configured'],
                    'ark_configured': config['api_keys']['ark_configured']
                }
            print(json.dumps(json_summary, indent=2, ensure_ascii=False))

        print("=" * 50)
        print("🎯 Configuration loaded successfully!")

    except Exception as e:
        print(f"❌ Failed to load configuration: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
