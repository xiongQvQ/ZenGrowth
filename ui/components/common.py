"""
通用UI组件
可复用的Streamlit界面组件
"""

import streamlit as st
from utils.i18n import t


def render_no_data_warning():
    """渲染无数据警告组件"""
    st.warning(f"⚠️ {t('common.warning')}: {t('data_upload.upload_ga4_file')}")


def render_data_status_check(func):
    """装饰器：检查数据状态，如果无数据则显示警告并返回"""
    def wrapper(*args, **kwargs):
        from ui.state import get_state_manager
        state_manager = get_state_manager()
        
        if not state_manager.is_data_loaded():
            render_no_data_warning()
            return
        return func(*args, **kwargs)
    return wrapper


def render_loading_spinner(message: str = None):
    """渲染加载状态组件"""
    if message is None:
        message = t('common.loading')
    return st.spinner(message)


def render_success_message(message: str):
    """渲染成功消息"""
    st.success(f"✅ {message}")


def render_error_message(message: str):
    """渲染错误消息"""
    st.error(f"❌ {message}")


def render_info_message(message: str):
    """渲染信息消息"""
    st.info(f"ℹ️ {message}")


def render_metric_card(label: str, value: str, delta: str = None):
    """渲染指标卡片"""
    return st.metric(label, value, delta)


def render_columns_layout(columns: list):
    """渲染多列布局"""
    return st.columns(columns)


def render_expander(title: str, expanded: bool = False):
    """渲染可展开容器"""
    return st.expander(title, expanded=expanded)