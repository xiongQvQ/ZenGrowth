"""
配置管理器
管理分析参数配置和系统设置
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class AnalysisConfig:
    """分析配置数据类"""
    # 事件分析配置
    event_analysis: Dict[str, Any] = None
    
    # 留存分析配置
    retention_analysis: Dict[str, Any] = None
    
    # 转化分析配置
    conversion_analysis: Dict[str, Any] = None
    
    # 用户分群配置
    user_segmentation: Dict[str, Any] = None
    
    # 路径分析配置
    path_analysis: Dict[str, Any] = None
    
    # 通用配置
    general: Dict[str, Any] = None
    
    def __post_init__(self):
        """初始化默认配置"""
        if self.event_analysis is None:
            self.event_analysis = {
                'time_granularity': 'day',  # day, week, month
                'top_events_limit': 10,
                'trend_analysis_days': 30,
                'correlation_threshold': 0.5
            }
        
        if self.retention_analysis is None:
            self.retention_analysis = {
                'retention_periods': [1, 7, 14, 30],  # 天数
                'cohort_type': 'weekly',  # daily, weekly, monthly
                'min_cohort_size': 100,
                'analysis_window_days': 90
            }
        
        if self.conversion_analysis is None:
            self.conversion_analysis = {
                'funnel_steps': [],  # 用户定义的漏斗步骤
                'conversion_window_hours': 24,
                'min_funnel_users': 50,
                'attribution_model': 'first_touch'  # first_touch, last_touch, linear
            }
        
        if self.user_segmentation is None:
            self.user_segmentation = {
                'clustering_method': 'kmeans',  # kmeans, dbscan
                'n_clusters': 5,
                'feature_types': ['behavioral', 'demographic', 'temporal'],
                'min_cluster_size': 100,
                'max_clusters': 10
            }
        
        if self.path_analysis is None:
            self.path_analysis = {
                'min_path_support': 0.01,  # 最小支持度
                'max_path_length': 10,
                'session_timeout_minutes': 30,
                'include_bounce_sessions': False
            }
        
        if self.general is None:
            self.general = {
                'date_range_days': 30,
                'timezone': 'UTC',
                'sample_rate': 1.0,  # 数据采样率
                'cache_results': True,
                'parallel_processing': True
            }


@dataclass
class SystemConfig:
    """系统配置数据类"""
    # API配置
    api_settings: Dict[str, Any] = None
    
    # LLM配置 (与JSON配置文件中的llm_settings对应)
    llm_settings: Dict[str, Any] = None
    
    # Google配置
    google_settings: Dict[str, Any] = None
    
    # Volcano配置  
    volcano_settings: Dict[str, Any] = None
    
    # 多模态配置
    multimodal_settings: Dict[str, Any] = None
    
    # 数据处理配置
    data_processing: Dict[str, Any] = None
    
    # 界面配置
    ui_settings: Dict[str, Any] = None
    
    # 导出配置
    export_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        """初始化默认配置"""
        if self.llm_settings is None:
            self.llm_settings = {
                'default_provider': getattr(settings, 'default_llm_provider', 'google'),
                'enabled_providers': getattr(settings, 'enabled_providers', ['google', 'volcano']),
                'enable_fallback': getattr(settings, 'enable_fallback', True),
                'fallback_order': getattr(settings, 'fallback_order', ['google', 'volcano'])
            }
            
        if self.google_settings is None:
            self.google_settings = {
                'model': getattr(settings, 'llm_model', 'gemini-1.5-pro'),
                'temperature': getattr(settings, 'llm_temperature', 0.7),
                'max_tokens': getattr(settings, 'llm_max_tokens', 4000),
                'timeout': 30,
                'retries': 3
            }
            
        if self.volcano_settings is None:
            self.volcano_settings = {
                'base_url': getattr(settings, 'ark_base_url', 'https://ark.cn-beijing.volces.com/api/v3'),
                'model': getattr(settings, 'ark_model', 'doubao-1.5-pro-32k'),
                'temperature': getattr(settings, 'llm_temperature', 0.7)
            }
            
        if self.multimodal_settings is None:
            self.multimodal_settings = {
                'enabled': getattr(settings, 'enable_multimodal', True),
                'max_image_size': getattr(settings, 'max_image_size_mb', 10),
                'image_timeout': getattr(settings, 'image_analysis_timeout', 60),
                'supported_formats': getattr(settings, 'supported_image_formats', ['jpg', 'jpeg', 'png'])
            }
            
        if self.api_settings is None:
            self.api_settings = {
                'google_api_key': settings.google_api_key or '',
                'ark_api_key': getattr(settings, 'ark_api_key', ''),
                'api_timeout': 30,
                'max_retries': 3
            }
        
        if self.data_processing is None:
            self.data_processing = {
                'max_file_size_mb': settings.max_file_size_mb,
                'chunk_size': settings.chunk_size,
                'memory_limit_gb': 4,
                'temp_dir': 'data/temp',
                'cleanup_temp_files': True
            }
        
        if self.ui_settings is None:
            self.ui_settings = {
                'theme': 'light',  # light, dark
                'language': 'zh-CN',
                'page_size': 20,
                'auto_refresh': False,
                'show_debug_info': False
            }
        
        if self.export_settings is None:
            self.export_settings = {
                'default_format': 'json',
                'include_raw_data': False,
                'compress_exports': True,
                'export_dir': 'reports',
                'filename_template': 'analysis_report_{timestamp}'
            }


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.analysis_config_file = self.config_dir / "analysis_config.json"
        self.system_config_file = self.config_dir / "system_config.json"
        
        # 加载配置
        self.analysis_config = self._load_analysis_config()
        self.system_config = self._load_system_config()
    
    def _load_analysis_config(self) -> AnalysisConfig:
        """加载分析配置"""
        try:
            if self.analysis_config_file.exists():
                with open(self.analysis_config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return AnalysisConfig(**config_data)
            else:
                # 创建默认配置
                config = AnalysisConfig()
                self._save_analysis_config(config)
                return config
        except Exception as e:
            logger.error(f"加载分析配置失败: {e}")
            return AnalysisConfig()
    
    def _load_system_config(self) -> SystemConfig:
        """加载系统配置"""
        try:
            if self.system_config_file.exists():
                with open(self.system_config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return SystemConfig(**config_data)
            else:
                # 创建默认配置
                config = SystemConfig()
                self._save_system_config(config)
                return config
        except Exception as e:
            logger.error(f"加载系统配置失败: {e}")
            return SystemConfig()
    
    def _save_analysis_config(self, config: AnalysisConfig):
        """保存分析配置"""
        try:
            with open(self.analysis_config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, ensure_ascii=False, indent=2)
            logger.info("分析配置保存成功")
        except Exception as e:
            logger.error(f"保存分析配置失败: {e}")
    
    def _save_system_config(self, config):
        """保存系统配置"""
        try:
            with open(self.system_config_file, 'w', encoding='utf-8') as f:
                if isinstance(config, dict):
                    json.dump(config, f, ensure_ascii=False, indent=2)
                else:
                    json.dump(asdict(config), f, ensure_ascii=False, indent=2)
            logger.info("系统配置保存成功")
        except Exception as e:
            logger.error(f"保存系统配置失败: {e}")
    
    def save_system_config(self, config):
        """公共方法：保存系统配置"""
        try:
            # 更新内存中的配置
            if isinstance(config, dict):
                self.system_config = config
            else:
                self.system_config = config
            
            # 保存到文件
            self._save_system_config(config)
            logger.info("系统配置保存成功")
        except Exception as e:
            logger.error(f"保存系统配置失败: {e}")
            raise e
    
    def get_analysis_config(self, analysis_type: Optional[str] = None) -> Dict[str, Any]:
        """获取分析配置"""
        if analysis_type:
            return getattr(self.analysis_config, analysis_type, {})
        return asdict(self.analysis_config)
    
    def update_analysis_config(self, analysis_type: str, config_updates: Dict[str, Any]) -> bool:
        """更新分析配置"""
        try:
            if hasattr(self.analysis_config, analysis_type):
                current_config = getattr(self.analysis_config, analysis_type)
                current_config.update(config_updates)
                setattr(self.analysis_config, analysis_type, current_config)
                self._save_analysis_config(self.analysis_config)
                return True
            else:
                logger.error(f"未知的分析类型: {analysis_type}")
                return False
        except Exception as e:
            logger.error(f"更新分析配置失败: {e}")
            return False
    
    def get_system_config(self, config_type: Optional[str] = None) -> Dict[str, Any]:
        """获取系统配置"""
        if config_type:
            if hasattr(self.system_config, config_type):
                return getattr(self.system_config, config_type, {})
            else:
                # 如果system_config是dict，直接返回对应的值
                if isinstance(self.system_config, dict):
                    return self.system_config.get(config_type, {})
                return {}
        
        # 返回完整配置
        if hasattr(self.system_config, '__dict__') or hasattr(self.system_config, '_asdict'):
            try:
                return asdict(self.system_config)
            except:
                # 如果asdict失败，system_config可能已经是dict
                if isinstance(self.system_config, dict):
                    return self.system_config
                return {}
        elif isinstance(self.system_config, dict):
            return self.system_config
        else:
            return {}
    
    def get_system_config_object(self) -> SystemConfig:
        """获取系统配置对象（返回SystemConfig实例）"""
        return self.system_config
    
    def update_system_config(self, config_type: str, config_updates: Dict[str, Any]) -> bool:
        """更新系统配置"""
        try:
            if hasattr(self.system_config, config_type):
                # 处理dataclass对象
                current_config = getattr(self.system_config, config_type)
                current_config.update(config_updates)
                setattr(self.system_config, config_type, current_config)
                self._save_system_config(self.system_config)
                return True
            elif isinstance(self.system_config, dict) and config_type in self.system_config:
                # 处理dict对象
                current_config = self.system_config[config_type]
                current_config.update(config_updates)
                self.system_config[config_type] = current_config
                
                # 保存为dict格式
                try:
                    with open(self.system_config_file, 'w', encoding='utf-8') as f:
                        json.dump(self.system_config, f, ensure_ascii=False, indent=2)
                    logger.info("系统配置保存成功")
                except Exception as e:
                    logger.error(f"保存系统配置失败: {e}")
                    return False
                return True
            else:
                logger.error(f"未知的配置类型: {config_type}")
                return False
        except Exception as e:
            logger.error(f"更新系统配置失败: {e}")
            return False
    
    def reset_analysis_config(self, analysis_type: Optional[str] = None) -> bool:
        """重置分析配置"""
        try:
            if analysis_type:
                # 重置特定分析类型的配置
                default_config = AnalysisConfig()
                setattr(self.analysis_config, analysis_type, getattr(default_config, analysis_type))
            else:
                # 重置所有分析配置
                self.analysis_config = AnalysisConfig()
            
            self._save_analysis_config(self.analysis_config)
            return True
        except Exception as e:
            logger.error(f"重置分析配置失败: {e}")
            return False
    
    def reset_system_config(self, config_type: Optional[str] = None) -> bool:
        """重置系统配置"""
        try:
            if config_type:
                # 重置特定配置类型
                default_config = SystemConfig()
                setattr(self.system_config, config_type, getattr(default_config, config_type))
            else:
                # 重置所有系统配置
                self.system_config = SystemConfig()
            
            self._save_system_config(self.system_config)
            return True
        except Exception as e:
            logger.error(f"重置系统配置失败: {e}")
            return False
    
    def export_config(self, output_path: str) -> bool:
        """导出配置到文件"""
        try:
            config_data = {
                'analysis_config': asdict(self.analysis_config),
                'system_config': asdict(self.system_config),
                'exported_at': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置导出成功: {output_path}")
            return True
        except Exception as e:
            logger.error(f"配置导出失败: {e}")
            return False
    
    def import_config(self, input_path: str) -> bool:
        """从文件导入配置"""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 验证配置格式
            if 'analysis_config' in config_data:
                self.analysis_config = AnalysisConfig(**config_data['analysis_config'])
                self._save_analysis_config(self.analysis_config)
            
            if 'system_config' in config_data:
                self.system_config = SystemConfig(**config_data['system_config'])
                self._save_system_config(self.system_config)
            
            logger.info(f"配置导入成功: {input_path}")
            return True
        except Exception as e:
            logger.error(f"配置导入失败: {e}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置有效性"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # 验证API配置
            api_config = self.system_config.api_settings
            default_provider = api_config.get('default_llm_provider', 'google')
            enabled_providers = api_config.get('enabled_providers', [])
            
            # 检查默认提供商的API密钥
            if default_provider == 'google' and not api_config.get('google_api_key'):
                validation_result['errors'].append('Google API密钥未配置')
                validation_result['valid'] = False
            elif default_provider == 'volcano' and not api_config.get('ark_api_key'):
                validation_result['errors'].append('Volcano ARK API密钥未配置')
                validation_result['valid'] = False
            
            # 检查启用的提供商配置
            for provider in enabled_providers:
                if provider == 'google' and not api_config.get('google_api_key'):
                    validation_result['warnings'].append('Google API密钥未配置，该提供商将不可用')
                elif provider == 'volcano' and not api_config.get('ark_api_key'):
                    validation_result['warnings'].append('Volcano ARK API密钥未配置，该提供商将不可用')
            
            # 验证数据处理配置
            data_config = self.system_config.data_processing
            if data_config.get('max_file_size_mb', 0) <= 0:
                validation_result['warnings'].append('文件大小限制配置异常')
            
            # 验证分析配置
            retention_config = self.analysis_config.retention_analysis
            if not retention_config.get('retention_periods'):
                validation_result['warnings'].append('留存分析周期未配置')
            
            # 验证导出配置
            export_config = self.system_config.export_settings
            export_dir = Path(export_config.get('export_dir', 'reports'))
            if not export_dir.exists():
                try:
                    export_dir.mkdir(parents=True, exist_ok=True)
                except Exception:
                    validation_result['warnings'].append(f'导出目录创建失败: {export_dir}')
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f'配置验证异常: {str(e)}')
        
        return validation_result
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        try:
            return {
                'analysis_config': {
                    'event_analysis_enabled': bool(self.analysis_config.event_analysis),
                    'retention_periods': len(self.analysis_config.retention_analysis.get('retention_periods', [])),
                    'clustering_method': self.analysis_config.user_segmentation.get('clustering_method'),
                    'funnel_steps_configured': len(self.analysis_config.conversion_analysis.get('funnel_steps', []))
                },
                'system_config': {
                    'api_configured': bool(self.system_config.api_settings.get('google_api_key')) or bool(self.system_config.api_settings.get('ark_api_key')),
                    'default_provider': self.system_config.api_settings.get('default_llm_provider'),
                    'enabled_providers': self.system_config.api_settings.get('enabled_providers', []),
                    'google_configured': bool(self.system_config.api_settings.get('google_api_key')),
                    'volcano_configured': bool(self.system_config.api_settings.get('ark_api_key')),
                    'multimodal_enabled': self.system_config.api_settings.get('enable_multimodal', False),
                    'max_file_size_mb': self.system_config.data_processing.get('max_file_size_mb'),
                    'default_export_format': self.system_config.export_settings.get('default_format'),
                    'ui_theme': self.system_config.ui_settings.get('theme')
                },
                'config_files': {
                    'analysis_config_exists': self.analysis_config_file.exists(),
                    'system_config_exists': self.system_config_file.exists(),
                    'last_modified': max(
                        self.analysis_config_file.stat().st_mtime if self.analysis_config_file.exists() else 0,
                        self.system_config_file.stat().st_mtime if self.system_config_file.exists() else 0
                    )
                }
            }
        except Exception as e:
            logger.error(f"获取配置摘要失败: {e}")
            return {}


# 全局配置管理器实例
config_manager = ConfigManager()