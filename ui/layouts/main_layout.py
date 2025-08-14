"""
主布局组件
提供统一的页面布局和错误处理
"""

import streamlit as st
from contextlib import contextmanager

from ui.state import get_state_manager


@contextmanager
def render_main_layout():
    """渲染主布局"""
    # 主容器
    main_container = st.container()
    
    with main_container:
        # 错误容器
        error_container = st.container()
        
        # 内容容器
        content_container = st.container()
        
        # 检查和显示错误
        state_manager = get_state_manager()
        last_error = state_manager.get_last_error()
        
        if last_error:
            with error_container:
                st.error(f"❌ {last_error}")
                
                # 清除错误按钮
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("清除错误"):
                        state_manager.clear_errors()
                        st.rerun()
        
        # 返回内容容器给调用者
        with content_container:
            yield content_container


def render_page_header(title: str, subtitle: str = ""):
    """渲染页面标题"""
    st.header(title)
    if subtitle:
        st.markdown(subtitle)
    st.markdown("---")


def render_loading_state(message: str = "加载中..."):
    """渲染加载状态"""
    return st.spinner(message)


def render_error_boundary(error_message: str):
    """渲染错误边界"""
    st.error(f"❌ {error_message}")
    
    # 记录错误到状态管理器
    state_manager = get_state_manager()
    state_manager.add_error(error_message)


def render_success_message(message: str):
    """渲染成功消息"""
    st.success(f"✅ {message}")


def render_warning_message(message: str):
    """渲染警告消息"""
    st.warning(f"⚠️ {message}")


def render_info_message(message: str):
    """渲染信息消息"""
    st.info(f"ℹ️ {message}")


class LayoutManager:
    """布局管理器"""
    
    def __init__(self):
        self.state_manager = get_state_manager()
    
    def render_page_with_data_check(self, page_function, page_name: str):
        """渲染需要数据的页面"""
        if not self.state_manager.is_data_loaded():
            render_warning_message("请先上传 GA4数据文件")
            return
        
        try:
            page_function()
        except Exception as e:
            error_msg = f"页面 {page_name} 渲染失败: {str(e)}"
            render_error_boundary(error_msg)
    
    def render_page_safe(self, page_function, page_name: str):
        """安全渲染页面"""
        try:
            page_function()
        except Exception as e:
            error_msg = f"页面 {page_name} 渲染失败: {str(e)}"
            render_error_boundary(error_msg)
    
    def get_current_page(self) -> str:
        """获取当前页面"""
        return self.state_manager.get_current_page()
    
    def set_page_config(self, page: str, config: dict):
        """设置页面配置"""
        self.state_manager.update_page_config(page, config)
    
    def get_page_config(self, page: str) -> dict:
        """获取页面配置"""
        return self.state_manager.get_page_config(page)