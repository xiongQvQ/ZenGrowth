"""
转化分析页面
分析用户转化路径和效果
"""

import streamlit as st
from ui.components.common import render_data_status_check
from utils.i18n import t

@render_data_status_check
def show_conversion_analysis_page():
    """显示转化分析页面"""
    st.header("🎯 " + t("pages.conversion_analysis.title", "转化分析"))
    st.markdown("---")
    st.info("转化分析页面正在开发中...")
    st.write("这里将显示转化分析结果...")
