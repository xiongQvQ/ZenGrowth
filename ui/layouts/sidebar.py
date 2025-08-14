"""
侧边栏组件
提供导航和数据状态显示
"""

import streamlit as st
from typing import List

from utils.i18n import t
from ui.state import get_state_manager


def show_data_status():
    """显示数据状态"""
    state_manager = get_state_manager()
    
    if state_manager.is_data_loaded():
        raw_data = state_manager.get_raw_data()
        if raw_data is not None:
            st.success(f"✅ {t('common.data_loaded')}")
            st.write(f"📊 {t('data_upload.total_records')}: {len(raw_data):,}")
        else:
            st.warning("⚠️ 数据状态异常")
    else:
        st.info(f"📊 {t('data_upload.please_upload_data')}")


def get_navigation_pages() -> List[str]:
    """获取导航页面列表"""
    return [
        t("navigation.data_upload"),
        t("navigation.intelligent_analysis"),
        t("navigation.event_analysis"), 
        t("navigation.retention_analysis"),
        t("navigation.conversion_analysis"),
        t("navigation.user_segmentation"),
        t("navigation.path_analysis"),
        t("navigation.comprehensive_report"),
        t("navigation.system_settings")
    ]


def render_sidebar() -> str:
    """渲染侧边栏并返回选中页面"""
    with st.sidebar:
        st.header(t("app.navigation"))
        
        # 显示数据状态
        show_data_status()
        
        # 导航选择
        pages = get_navigation_pages()
        selected_page = st.selectbox(
            t("app.select_module"),
            pages
        )
        
        # 分隔线
        st.markdown("---")
        
        # 显示系统状态
        state_manager = get_state_manager()
        
        # 显示性能优化状态
        try:
            from system.integration_manager_singleton import get_integration_manager_status
            status = get_integration_manager_status()
            if status.get('initialized'):
                st.success("⚡ 系统已优化")
            else:
                st.info("🔄 系统待启动")
        except:
            pass
        
        # 显示错误信息（如果有）
        if state_manager.get_last_error():
            st.error("⚠️ 系统错误")
            with st.expander("查看错误详情"):
                st.text(state_manager.get_last_error())
        
        return selected_page