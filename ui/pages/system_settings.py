"""
系统设置页面
配置系统参数和选项
"""

import streamlit as st
from utils.i18n import t

def show_system_settings():
    """显示系统设置页面"""
    st.header("⚙️ " + t("pages.system_settings.title", "系统设置"))
    st.markdown("---")
    
    # API设置
    st.subheader("API配置")
    with st.expander("LLM提供商设置"):
        st.text_input("Google API Key", type="password")
        st.text_input("Volcano ARK API Key", type="password")
    
    # 分析设置
    st.subheader("分析配置")
    st.slider("默认分析深度", 1, 5, 3)
    st.checkbox("启用高级分析")
    
    st.info("系统设置页面功能正在开发中...")
