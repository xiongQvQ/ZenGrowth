"""
用户行为分析智能体平台主入口
基于CrewAI和Streamlit的多智能体协作分析系统 - 模块化版本
"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings, validate_config
from utils.logger import setup_logger
from utils.i18n import t
from ui.state import get_state_manager
from ui.layouts.sidebar import render_sidebar
from ui.layouts.main_layout import render_main_layout
from ui.pages.data_upload import show_data_upload_page
from ui.pages.intelligent_analysis import show_intelligent_analysis_page
from ui.pages.event_analysis import show_event_analysis_page
from ui.pages.retention_analysis import show_retention_analysis_page
from ui.pages.conversion_analysis import show_conversion_analysis_page
from ui.pages.user_segmentation import show_user_segmentation_page
from ui.pages.path_analysis import show_path_analysis_page
from ui.pages.comprehensive_report import show_comprehensive_report_page
from ui.pages.system_settings import show_system_settings
from system.integration_manager_singleton import get_integration_manager, get_integration_manager_status
from config.llm_provider_manager import get_provider_manager

# 设置页面配置
st.set_page_config(
    page_title=settings.app_title,
    page_icon=settings.app_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)


def check_provider_health():
    """检查LLM提供商健康状态"""
    try:
        provider_manager = get_provider_manager()
        # 使用正确的方法名
        health_results = provider_manager.health_check_all()
        
        state_manager = get_state_manager()
        health_status = {}
        
        for provider, result in health_results.items():
            healthy = result.status == "available"
            status_info = {
                'healthy': healthy,
                'status': result.status,
                'response_time': result.response_time,
                'error_message': result.error_message,
                'last_check': result.last_check
            }
            state_manager.update_api_health(provider, healthy, status_info)
            health_status[provider] = status_info
        
        return health_status
    except Exception as e:
        st.error(f"健康检查失败: {str(e)}")
        return {}


def initialize_session_state():
    """初始化会话状态"""
    # 确保状态管理器正确初始化
    state_manager = get_state_manager()
    
    # 初始化集成管理器（使用单例模式和延迟加载）
    if not state_manager.is_initialized():
        try:
            # 使用延迟加载的单例管理器，避免页面切换时重复初始化
            integration_manager = get_integration_manager(lazy_loading=True)
            state_manager.set_integration_manager(integration_manager)
        except Exception as e:
            st.error(f"集成管理器初始化失败: {str(e)}")
            st.stop()


def render_page_router(selected_page: str):
    """页面路由器"""
    state_manager = get_state_manager()
    
    # 页面路由映射
    page_routes = {
        t("navigation.data_upload"): ("data_upload", show_data_upload_page),
        t("navigation.intelligent_analysis"): ("intelligent_analysis", show_intelligent_analysis_page),
        t("navigation.event_analysis"): ("event_analysis", show_event_analysis_page),
        t("navigation.retention_analysis"): ("retention_analysis", show_retention_analysis_page),
        t("navigation.conversion_analysis"): ("conversion_analysis", show_conversion_analysis_page),
        t("navigation.user_segmentation"): ("user_segmentation", show_user_segmentation_page),
        t("navigation.path_analysis"): ("path_analysis", show_path_analysis_page),
        t("navigation.comprehensive_report"): ("comprehensive_report", show_comprehensive_report_page),
        t("navigation.system_settings"): ("system_settings", show_system_settings)
    }
    
    if selected_page in page_routes:
        page_key, page_function = page_routes[selected_page]
        
        # 更新当前页面状态
        state_manager.set_current_page(page_key)
        
        try:
            # 渲染页面
            page_function()
        except Exception as e:
            st.error(f"页面渲染失败: {str(e)}")
            state_manager.add_error(f"页面 {page_key} 渲染失败", {
                'page': page_key,
                'error': str(e)
            })
    else:
        st.error(f"未知页面: {selected_page}")


def main():
    """主应用函数"""
    # 设置日志
    logger = setup_logger()
    
    # 验证配置
    if not validate_config():
        st.error(t("settings.system_config_incomplete"))
        st.stop()
    
    # 初始化会话状态（必须在健康检查之前）
    initialize_session_state()
    
    # 检查提供商健康状态
    check_provider_health()
    
    # 应用标题
    st.title(f"{settings.app_icon} {t('app.title', settings.app_title)}")
    st.markdown("---")
    
    # 渲染侧边栏并获取选中的页面
    selected_page = render_sidebar()
    
    # 渲染主布局
    with render_main_layout():
        render_page_router(selected_page)


if __name__ == "__main__":
    main()