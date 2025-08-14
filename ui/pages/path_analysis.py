"""
路径分析页面
分析用户行为路径和流转
"""

import streamlit as st
from ui.components.common import render_data_status_check
from utils.i18n import t

@render_data_status_check
def show_path_analysis_page():
    """显示路径分析页面"""
    st.header("🛤️ " + t("pages.path_analysis.title", "路径分析"))
    st.markdown("---")
    st.info("路径分析页面正在开发中...")
    st.write("这里将显示路径分析结果...")
