"""
状态管理器
统一管理Streamlit session state，提供类型安全和一致性
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class DataState:
    """数据状态类"""
    loaded: bool = False
    raw_data: Optional[pd.DataFrame] = None
    processed_data: Optional[pd.DataFrame] = None
    data_summary: Dict[str, Any] = field(default_factory=dict)
    upload_info: Dict[str, Any] = field(default_factory=dict)
    last_updated: Optional[datetime] = None


@dataclass
class AnalysisState:
    """分析状态类"""
    event_analysis_results: Dict[str, Any] = field(default_factory=dict)
    retention_results: Dict[str, Any] = field(default_factory=dict)
    conversion_results: Dict[str, Any] = field(default_factory=dict)
    segmentation_results: Dict[str, Any] = field(default_factory=dict)
    path_results: Dict[str, Any] = field(default_factory=dict)
    workflow_results: Dict[str, Any] = field(default_factory=dict)
    comprehensive_report: Dict[str, Any] = field(default_factory=dict)
    
    # 分析配置
    current_analysis_config: Dict[str, Any] = field(default_factory=dict)
    
    # 进度状态
    is_analyzing: bool = False
    analysis_progress: float = 0.0
    current_analysis_step: str = ""


@dataclass
class UIState:
    """UI状态类"""
    current_page: str = "data_upload"
    selected_analysis_type: str = ""
    show_advanced_options: bool = False
    page_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # 可视化状态
    chart_configs: Dict[str, Any] = field(default_factory=dict)
    export_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemState:
    """系统状态类"""
    initialized: bool = False
    integration_manager: Optional[Any] = None
    api_providers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # 健康状态
    api_health: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_health_check: Optional[datetime] = None


class StateManager:
    """状态管理器"""
    
    def __init__(self):
        self._initialize_states()
    
    def _initialize_states(self):
        """初始化所有状态"""
        if 'data_state' not in st.session_state:
            st.session_state.data_state = DataState()
        
        if 'analysis_state' not in st.session_state:
            st.session_state.analysis_state = AnalysisState()
        
        if 'ui_state' not in st.session_state:
            st.session_state.ui_state = UIState()
        
        if 'system_state' not in st.session_state:
            st.session_state.system_state = SystemState()
        
        self._maintain_backward_compatibility()
    
    def _maintain_backward_compatibility(self):
        """维护向后兼容性"""
        # 确保所有状态都已初始化
        if 'data_state' not in st.session_state:
            return
            
        data_state = st.session_state.data_state
        
        # 同步旧的session_state变量
        st.session_state.data_loaded = data_state.loaded
        st.session_state.raw_data = data_state.raw_data
        st.session_state.processed_data = data_state.processed_data
        
        # 分析结果的兼容性
        if 'analysis_state' in st.session_state:
            analysis_state = st.session_state.analysis_state
            st.session_state.event_analysis_results = analysis_state.event_analysis_results
            st.session_state.retention_results = analysis_state.retention_results
            st.session_state.conversion_results = analysis_state.conversion_results
            st.session_state.segmentation_results = analysis_state.segmentation_results
            st.session_state.path_results = analysis_state.path_results
            st.session_state.workflow_results = analysis_state.workflow_results
            st.session_state.comprehensive_report = analysis_state.comprehensive_report
        
        # UI状态兼容性
        if 'ui_state' in st.session_state:
            ui_state = st.session_state.ui_state
            st.session_state.current_page = ui_state.current_page
            st.session_state.selected_analysis_type = ui_state.selected_analysis_type
            st.session_state.show_advanced_options = ui_state.show_advanced_options
    
    # === 数据状态管理 ===
    def set_data_loaded(self, loaded: bool, raw_data: Optional[pd.DataFrame] = None):
        """设置数据加载状态"""
        data_state = st.session_state.data_state
        data_state.loaded = loaded
        data_state.last_updated = datetime.now()
        
        if raw_data is not None:
            data_state.raw_data = raw_data
        
        self._maintain_backward_compatibility()
    
    def is_data_loaded(self) -> bool:
        """检查数据是否已加载"""
        return st.session_state.data_state.loaded
    
    def get_raw_data(self) -> Optional[pd.DataFrame]:
        """获取原始数据"""
        return st.session_state.data_state.raw_data
    
    def set_processed_data(self, data: pd.DataFrame):
        """设置处理后的数据"""
        st.session_state.data_state.processed_data = data
        self._maintain_backward_compatibility()
    
    def get_processed_data(self) -> Optional[pd.DataFrame]:
        """获取处理后的数据"""
        return st.session_state.data_state.processed_data
    
    def update_data_summary(self, summary: Dict[str, Any]):
        """更新数据摘要"""
        st.session_state.data_state.data_summary.update(summary)
    
    def get_data_summary(self) -> Dict[str, Any]:
        """获取数据摘要"""
        return st.session_state.data_state.data_summary
    
    # === 分析状态管理 ===
    def set_analysis_results(self, analysis_type: str, results: Dict[str, Any]):
        """设置分析结果"""
        analysis_state = st.session_state.analysis_state
        
        if analysis_type == "event":
            analysis_state.event_analysis_results = results
        elif analysis_type == "retention":
            analysis_state.retention_results = results
        elif analysis_type == "conversion":
            analysis_state.conversion_results = results
        elif analysis_type == "segmentation":
            analysis_state.segmentation_results = results
        elif analysis_type == "user_segmentation":
            analysis_state.segmentation_results = results
        elif analysis_type == "path":
            analysis_state.path_results = results
        elif analysis_type == "workflow":
            analysis_state.workflow_results = results
        elif analysis_type == "comprehensive":
            analysis_state.comprehensive_report = results
        
        self._maintain_backward_compatibility()
    
    def get_analysis_results(self, analysis_type: str) -> Dict[str, Any]:
        """获取分析结果"""
        analysis_state = st.session_state.analysis_state
        
        if analysis_type == "event":
            return analysis_state.event_analysis_results
        elif analysis_type == "retention":
            return analysis_state.retention_results
        elif analysis_type == "conversion":
            return analysis_state.conversion_results
        elif analysis_type == "segmentation":
            return analysis_state.segmentation_results
        elif analysis_type == "user_segmentation":
            return analysis_state.segmentation_results
        elif analysis_type == "path":
            return analysis_state.path_results
        elif analysis_type == "workflow":
            return analysis_state.workflow_results
        elif analysis_type == "comprehensive":
            return analysis_state.comprehensive_report
        else:
            return {}
    
    def set_analysis_progress(self, progress: float, step: str = ""):
        """设置分析进度"""
        analysis_state = st.session_state.analysis_state
        analysis_state.analysis_progress = progress
        analysis_state.current_analysis_step = step
    
    def set_analyzing(self, is_analyzing: bool):
        """设置分析状态"""
        st.session_state.analysis_state.is_analyzing = is_analyzing
        if not is_analyzing:
            self.set_analysis_progress(0.0, "")
    
    def is_analyzing(self) -> bool:
        """检查是否正在分析"""
        return st.session_state.analysis_state.is_analyzing
    
    def get_analysis_progress(self) -> tuple[float, str]:
        """获取分析进度"""
        analysis_state = st.session_state.analysis_state
        return analysis_state.analysis_progress, analysis_state.current_analysis_step
    
    # === UI状态管理 ===
    def set_current_page(self, page: str):
        """设置当前页面"""
        st.session_state.ui_state.current_page = page
        self._maintain_backward_compatibility()
    
    def get_current_page(self) -> str:
        """获取当前页面"""
        return st.session_state.ui_state.current_page
    
    def set_selected_analysis_type(self, analysis_type: str):
        """设置选中的分析类型"""
        st.session_state.ui_state.selected_analysis_type = analysis_type
        self._maintain_backward_compatibility()
    
    def get_selected_analysis_type(self) -> str:
        """获取选中的分析类型"""
        return st.session_state.ui_state.selected_analysis_type
    
    def toggle_advanced_options(self):
        """切换高级选项显示"""
        ui_state = st.session_state.ui_state
        ui_state.show_advanced_options = not ui_state.show_advanced_options
        self._maintain_backward_compatibility()
    
    def show_advanced_options(self) -> bool:
        """是否显示高级选项"""
        return st.session_state.ui_state.show_advanced_options
    
    def update_page_config(self, page: str, config: Dict[str, Any]):
        """更新页面配置"""
        st.session_state.ui_state.page_configs[page] = config
    
    def get_page_config(self, page: str) -> Dict[str, Any]:
        """获取页面配置"""
        return st.session_state.ui_state.page_configs.get(page, {})
    
    # === 系统状态管理 ===
    def set_integration_manager(self, manager):
        """设置集成管理器（支持延迟加载）"""
        st.session_state.system_state.integration_manager = manager
        st.session_state.system_state.initialized = True
        
        # 记录管理器类型以支持延迟加载
        manager_type = type(manager).__name__
        logger.debug(f"设置集成管理器: {manager_type}")
    
    def get_integration_manager(self):
        """获取集成管理器"""
        # 确保system_state存在
        if 'system_state' not in st.session_state:
            self._initialize_states()
        return st.session_state.system_state.integration_manager
    
    def is_initialized(self) -> bool:
        """检查系统是否已初始化"""
        # 确保system_state存在
        if 'system_state' not in st.session_state:
            self._initialize_states()
        return st.session_state.system_state.initialized
    
    def add_error(self, message: str, context: Optional[Dict[str, Any]] = None):
        """添加错误信息"""
        # 确保system_state存在
        if 'system_state' not in st.session_state:
            self._initialize_states()
        error_info = {
            'message': message,
            'timestamp': datetime.now(),
            'context': context or {}
        }
        st.session_state.system_state.errors.append(error_info)
    
    def get_last_error(self) -> Optional[str]:
        """获取最后一个错误"""
        # 确保system_state存在
        if 'system_state' not in st.session_state:
            self._initialize_states()
        errors = st.session_state.system_state.errors
        if errors:
            return errors[-1]['message']
        return None
    
    def get_all_errors(self) -> List[Dict[str, Any]]:
        """获取所有错误"""
        return st.session_state.system_state.errors
    
    def clear_errors(self):
        """清除所有错误"""
        st.session_state.system_state.errors.clear()
    
    def add_warning(self, message: str):
        """添加警告信息"""
        st.session_state.system_state.warnings.append(message)
    
    def get_warnings(self) -> List[str]:
        """获取所有警告"""
        return st.session_state.system_state.warnings
    
    def clear_warnings(self):
        """清除所有警告"""
        st.session_state.system_state.warnings.clear()
    
    def update_api_health(self, provider: str, is_healthy: bool, details: Dict[str, Any]):
        """更新API健康状态"""
        st.session_state.system_state.api_health[provider] = {
            'healthy': is_healthy,
            'last_check': datetime.now(),
            'details': details
        }
        st.session_state.system_state.last_health_check = datetime.now()
    
    def get_api_health(self, provider: str = None) -> Union[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """获取API健康状态"""
        if provider:
            return st.session_state.system_state.api_health.get(provider, {})
        return st.session_state.system_state.api_health
    
    def reset_all_states(self):
        """重置所有状态"""
        st.session_state.data_state = DataState()
        st.session_state.analysis_state = AnalysisState()
        st.session_state.ui_state = UIState()
        st.session_state.system_state = SystemState()
        self._maintain_backward_compatibility()


# 全局状态管理器实例
_state_manager = None

def get_state_manager() -> StateManager:
    """获取状态管理器单例"""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager