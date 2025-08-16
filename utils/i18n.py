"""
国际化(i18n)支持模块
提供多语言界面支持
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
from utils.config_manager import config_manager


class I18nManager:
    """国际化管理器"""
    
    def __init__(self, language_dir: str = "languages"):
        self.language_dir = Path(language_dir)
        self.language_dir.mkdir(exist_ok=True)
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.current_language = "zh-CN"
        self._load_translations()
        self._update_current_language()
    
    def _load_translations(self):
        """加载所有语言翻译文件"""
        # 确保语言文件存在
        self._ensure_language_files()
        
        # 加载所有语言文件
        for lang_file in self.language_dir.glob("*.json"):
            lang_code = lang_file.stem
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
            except Exception as e:
                print(f"加载语言文件失败 {lang_file}: {e}")
    
    def _ensure_language_files(self):
        """确保语言文件存在"""
        # 中文语言文件
        zh_cn_file = self.language_dir / "zh-CN.json"
        if not zh_cn_file.exists():
            zh_cn_translations = {
                "app": {
                    "title": "用户行为分析智能体平台",
                    "navigation": "🚀 功能导航",
                    "select_module": "选择功能模块"
                },
                "navigation": {
                    "data_upload": "📁 数据上传",
                    "intelligent_analysis": "🚀 智能分析", 
                    "event_analysis": "📊 事件分析",
                    "retention_analysis": "📈 留存分析",
                    "conversion_analysis": "🔄 转化分析",
                    "user_segmentation": "👥 用户分群",
                    "path_analysis": "🛤️ 路径分析",
                    "comprehensive_report": "📋 综合报告",
                    "system_settings": "⚙️ 系统设置"
                },
                "data_upload": {
                    "title": "📁 GA4数据上传与处理",
                    "file_upload": "📤 文件上传",
                    "file_preview": "🔍 文件预览",
                    "processing_progress": "⚙️ 数据处理进度",
                    "processing_results": "📊 数据处理结果",
                    "upload_ga4_file": "请上传GA4导出的NDJSON格式文件",
                    "drag_drop_text": "拖拽文件到此处或点击浏览",
                    "file_size_limit": "文件大小限制: 100MB",
                    "supported_formats": "支持格式: .ndjson, .json"
                },
                "settings": {
                    "title": "⚙️ 系统设置与配置",
                    "system_config": "🔧 系统配置",
                    "analysis_config": "📊 分析参数配置",
                    "export_config": "📥 导出设置",
                    "config_management": "🔄 配置管理",
                    "interface_theme": "界面主题",
                    "interface_language": "界面语言",
                    "page_size": "页面大小",
                    "show_debug": "显示调试信息",
                    "save_config": "💾 保存系统配置",
                    "config_saved": "✅ 系统配置保存成功!",
                    "config_save_failed": "❌ 配置保存失败"
                },
                "analysis": {
                    "event_title": "📊 事件分析",
                    "retention_title": "📈 用户留存分析", 
                    "conversion_title": "🔄 转化漏斗分析",
                    "segmentation_title": "👥 智能用户分群",
                    "path_title": "🛤️ 用户行为路径分析",
                    "report_title": "📋 综合分析报告",
                    "intelligent_title": "🚀 智能分析 - 一键完整分析",
                    "analysis_results": "📊 分析结果",
                    "analysis_config": "📋 分析配置",
                    "execute_analysis": "🎯 执行分析"
                },
                "common": {
                    "loading": "加载中...",
                    "processing": "处理中...",
                    "completed": "已完成",
                    "failed": "失败",
                    "start": "开始",
                    "stop": "停止",
                    "export": "导出",
                    "save": "保存",
                    "cancel": "取消",
                    "confirm": "确认",
                    "warning": "警告",
                    "error": "错误",
                    "success": "成功"
                }
            }
            
            with open(zh_cn_file, 'w', encoding='utf-8') as f:
                json.dump(zh_cn_translations, f, ensure_ascii=False, indent=2)
        
        # 英文语言文件
        en_us_file = self.language_dir / "en-US.json"
        if not en_us_file.exists():
            en_us_translations = {
                "app": {
                    "title": "User Behavior Analytics Platform",
                    "navigation": "🚀 Navigation", 
                    "select_module": "Select Module"
                },
                "navigation": {
                    "data_upload": "📁 Data Upload",
                    "intelligent_analysis": "🚀 Intelligent Analysis",
                    "event_analysis": "📊 Event Analysis", 
                    "retention_analysis": "📈 Retention Analysis",
                    "conversion_analysis": "🔄 Conversion Analysis",
                    "user_segmentation": "👥 User Segmentation",
                    "path_analysis": "🛤️ Path Analysis",
                    "comprehensive_report": "📋 Comprehensive Report",
                    "system_settings": "⚙️ System Settings"
                },
                "data_upload": {
                    "title": "📁 GA4 Data Upload & Processing",
                    "file_upload": "📤 File Upload",
                    "file_preview": "🔍 File Preview", 
                    "processing_progress": "⚙️ Data Processing Progress",
                    "processing_results": "📊 Data Processing Results",
                    "upload_ga4_file": "Please upload GA4 exported NDJSON format file",
                    "drag_drop_text": "Drag and drop file here or click to browse",
                    "file_size_limit": "File size limit: 100MB",
                    "supported_formats": "Supported formats: .ndjson, .json"
                },
                "settings": {
                    "title": "⚙️ System Settings & Configuration",
                    "system_config": "🔧 System Configuration",
                    "analysis_config": "📊 Analysis Parameters Configuration",
                    "export_config": "📥 Export Settings",
                    "config_management": "🔄 Configuration Management",
                    "interface_theme": "Interface Theme",
                    "interface_language": "Interface Language",
                    "page_size": "Page Size",
                    "show_debug": "Show Debug Info",
                    "save_config": "💾 Save System Configuration", 
                    "config_saved": "✅ System configuration saved successfully!",
                    "config_save_failed": "❌ Configuration save failed"
                },
                "analysis": {
                    "event_title": "📊 Event Analysis",
                    "retention_title": "📈 User Retention Analysis",
                    "conversion_title": "🔄 Conversion Funnel Analysis", 
                    "segmentation_title": "👥 Intelligent User Segmentation",
                    "path_title": "🛤️ User Behavior Path Analysis",
                    "report_title": "📋 Comprehensive Analysis Report",
                    "intelligent_title": "🚀 Intelligent Analysis - One-Click Complete Analysis",
                    "analysis_results": "📊 Analysis Results",
                    "analysis_config": "📋 Analysis Configuration",
                    "execute_analysis": "🎯 Execute Analysis"
                },
                "common": {
                    "loading": "Loading...",
                    "processing": "Processing...", 
                    "completed": "Completed",
                    "failed": "Failed",
                    "start": "Start",
                    "stop": "Stop",
                    "export": "Export",
                    "save": "Save",
                    "cancel": "Cancel", 
                    "confirm": "Confirm",
                    "warning": "Warning",
                    "error": "Error",
                    "success": "Success"
                }
            }
            
            with open(en_us_file, 'w', encoding='utf-8') as f:
                json.dump(en_us_translations, f, ensure_ascii=False, indent=2)
    
    def _update_current_language(self):
        """更新当前语言设置"""
        try:
            # 优先使用环境变量设置
            env_lang = os.environ.get('FORCE_LANGUAGE')
            if env_lang:
                self.current_language = env_lang
                return
                
            system_config = config_manager.get_system_config()
            self.current_language = system_config.get('ui_settings', {}).get('language', 'zh-CN')
        except Exception as e:
            print(f"读取语言配置失败: {e}")
            self.current_language = 'zh-CN'
    
    def get_text(self, key: str, default: Optional[str] = None) -> str:
        """获取翻译文本
        
        Args:
            key: 翻译键，支持点分隔的嵌套键，如 'app.title'
            default: 默认文本，如果翻译不存在则返回此值
        
        Returns:
            翻译后的文本
        """
        self._update_current_language()
        
        if self.current_language not in self.translations:
            # 如果当前语言不存在，回退到中文
            self.current_language = 'zh-CN'
        
        translation_dict = self.translations.get(self.current_language, {})
        
        # 支持嵌套键查找
        keys = key.split('.')
        for k in keys:
            if isinstance(translation_dict, dict) and k in translation_dict:
                translation_dict = translation_dict[k]
            else:
                # 如果找不到翻译，返回默认值或键名
                return default or key
        
        return translation_dict if isinstance(translation_dict, str) else (default or key)
    
    def t(self, key: str, default: Optional[str] = None) -> str:
        """get_text的简化别名"""
        return self.get_text(key, default)
    
    def get_current_language(self) -> str:
        """获取当前语言"""
        self._update_current_language()
        return self.current_language
    
    def get_available_languages(self) -> Dict[str, str]:
        """获取可用语言列表"""
        return {
            'zh-CN': '中文',
            'en-US': 'English'
        }


# 创建全局i18n实例
i18n = I18nManager()

# 导出常用函数
def t(key: str, default: Optional[str] = None) -> str:
    """翻译函数的全局快捷方式"""
    # 每次调用时更新当前语言设置，确保语言切换后能立即生效
    i18n._update_current_language()
    return i18n.get_text(key, default)

def get_current_language() -> str:
    """获取当前语言"""
    return i18n.get_current_language()