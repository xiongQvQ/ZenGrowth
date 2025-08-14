"""
用户分群页面
进行用户细分和特征分析
"""

import streamlit as st
from ui.components.common import render_data_status_check
from utils.i18n import t

@render_data_status_check
def show_user_segmentation_page():
    """显示用户分群页面"""
    st.header("👥 " + t("pages.user_segmentation.title", "用户分群"))
    st.markdown("---")
    st.info("用户分群页面正在开发中...")
    st.write("这里将显示用户分群结果...")
