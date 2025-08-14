"""
UI状态管理模块

统一管理Streamlit应用的状态，提供类型安全和一致性保证
"""

from .state_manager import (
    StateManager,
    DataState,
    AnalysisState,
    UIState,
    SystemState,
    get_state_manager
)

__all__ = [
    'StateManager',
    'DataState', 
    'AnalysisState',
    'UIState',
    'SystemState',
    'get_state_manager'
]