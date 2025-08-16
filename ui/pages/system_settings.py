"""
System Settings Page
Configure system parameters and options
"""

import streamlit as st
import json
from typing import Dict, Any
from utils.i18n import t
from utils.config_manager import config_manager
import os

def show_system_settings():
    """Display system settings page"""
    st.header("⚙️ " + t("settings.title"))
    st.markdown("---")
    
    # Load current configuration
    current_config = config_manager.get_system_config()
    
    # Create tabs for different configuration sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        t("settings.system_config"),
        t("settings.analysis_config"),
        t("settings.export_config"),
        t("settings.config_management"),
        "🔍 API Status"
    ])
    
    with tab1:
        st.subheader(t("settings.system_config"))
        
        # Interface settings
        col1, col2 = st.columns(2)
        with col1:
            theme = st.selectbox(
                t("settings.interface_theme"),
                ["light", "dark"],
                index=0 if current_config.get('ui_settings', {}).get('theme', 'light') == 'light' else 1
            )
            
            language = st.selectbox(
                t("settings.interface_language"),
                ["zh-CN", "en-US"],
                index=0 if current_config.get('ui_settings', {}).get('language', 'zh-CN') == 'zh-CN' else 1
            )
            
            page_size = st.number_input(
                t("settings.page_size"),
                min_value=10,
                max_value=1000,
                value=current_config.get('ui_settings', {}).get('page_size', 50)
            )
        
        with col2:
            show_debug = st.checkbox(
                t("settings.show_debug"),
                value=current_config.get('ui_settings', {}).get('show_debug', False)
            )
            
            auto_refresh = st.checkbox(
                t("settings.auto_refresh"),
                value=current_config.get('ui_settings', {}).get('auto_refresh', True)
            )
    
    with tab2:
        st.subheader(t("settings.analysis_config"))
        
        # LLM Provider Configuration
        st.markdown("### " + t("settings.llm_provider_config"))
        
        # Default LLM Provider
        available_providers = ["google", "volcano", "both"]
        default_provider = st.selectbox(
            t("settings.default_llm_provider_label"),
            available_providers,
            index=available_providers.index(
                current_config.get('llm_settings', {}).get('default_provider', 'google')
            )
        )
        
        # Enabled Providers
        enabled_providers = st.multiselect(
            t("settings.enabled_providers_label"),
            ["google", "volcano"],
            default=current_config.get('llm_settings', {}).get('enabled_providers', ["google", "volcano"])
        )
        
        # Fallback settings
        enable_fallback = st.checkbox(
            t("settings.enable_fallback_label"),
            value=current_config.get('llm_settings', {}).get('enable_fallback', True)
        )
        
        fallback_order = st.multiselect(
            t("settings.fallback_order_label"),
            ["google", "volcano"],
            default=current_config.get('llm_settings', {}).get('fallback_order', ["google", "volcano"])
        )
        
        # Google Gemini Configuration
        st.markdown("### " + t("settings.google_gemini_config"))
        col1, col2 = st.columns(2)
        with col1:
            google_api_key = st.text_input(
                t("settings.google_api_key_label"),
                value=os.getenv("GOOGLE_API_KEY", ""),
                type="password"
            )
            
            google_model = st.selectbox(
                t("settings.google_model_label"),
                ["gemini-1.5-pro", "gemini-1.5-flash"],
                index=0 if current_config.get('google_settings', {}).get('model', 'gemini-1.5-pro') == 'gemini-1.5-pro' else 1
            )
            
            google_temperature = st.slider(
                t("settings.google_temperature_label"),
                0.0, 2.0,
                float(current_config.get('google_settings', {}).get('temperature', 0.7))
            )
        
        with col2:
            google_max_tokens = st.number_input(
                t("settings.google_max_tokens_label"),
                min_value=100,
                max_value=10000,
                value=current_config.get('google_settings', {}).get('max_tokens', 4000)
            )
            
            google_timeout = st.number_input(
                "Google Timeout (seconds)",
                min_value=1,
                max_value=300,
                value=current_config.get('google_settings', {}).get('timeout', 30)
            )
            
            google_retries = st.number_input(
                "Google Retries",
                min_value=1,
                max_value=5,
                value=current_config.get('google_settings', {}).get('retries', 3)
            )
        
        # Volcano ARK Configuration
        st.markdown("### " + t("settings.volcano_ark_config"))
        col1, col2 = st.columns(2)
        with col1:
            volcano_api_key = st.text_input(
                t("settings.volcano_api_key_label"),
                value=os.getenv("ARK_API_KEY", ""),
                type="password"
            )
            
            volcano_base_url = st.text_input(
                t("settings.volcano_base_url_label"),
                value=current_config.get('volcano_settings', {}).get('base_url', 'https://ark.cn-beijing.volces.com/api/v3')
            )
            
            volcano_model = st.text_input(
                t("settings.volcano_model_label"),
                value=current_config.get('volcano_settings', {}).get('model', 'doubao-1.5-pro-32k')
            )
        
        with col2:
            volcano_temperature = st.slider(
                t("settings.volcano_temperature_label"),
                0.0, 2.0,
                float(current_config.get('volcano_settings', {}).get('temperature', 0.7))
            )
        
        # Multimodal Configuration
        st.markdown("### " + t("settings.multimodal_config"))
        enable_multimodal = st.checkbox(
            t("settings.enable_multimodal_label"),
            value=current_config.get('multimodal_settings', {}).get('enabled', True)
        )
        
        if enable_multimodal:
            max_image_size = st.number_input(
                t("settings.max_image_size_label"),
                min_value=1,
                max_value=50,
                value=current_config.get('multimodal_settings', {}).get('max_image_size', 10)
            )
            
            image_analysis_timeout = st.number_input(
                t("settings.image_analysis_timeout_label"),
                min_value=1,
                max_value=300,
                value=current_config.get('multimodal_settings', {}).get('image_timeout', 60)
            )
            
            supported_formats = st.multiselect(
                t("settings.supported_image_formats_label"),
                ["jpg", "jpeg", "png", "gif", "webp"],
                default=current_config.get('multimodal_settings', {}).get('supported_formats', ["jpg", "jpeg", "png"])
            )
    
    with tab3:
        st.subheader(t("settings.export_config"))
        
        # Data Processing Configuration
        st.markdown("### " + t("settings.data_processing_config"))
        max_file_size = st.number_input(
            t("settings.max_file_size_label"),
            min_value=1,
            max_value=500,
            value=current_config.get('data_processing', {}).get('max_file_size', 100)
        )
        
        chunk_size = st.number_input(
            t("settings.chunk_size_label"),
            min_value=1000,
            max_value=100000,
            value=current_config.get('data_processing', {}).get('chunk_size', 10000)
        )
        
        memory_limit = st.number_input(
            t("settings.memory_limit_label"),
            min_value=1,
            max_value=32,
            value=current_config.get('data_processing', {}).get('memory_limit', 4)
        )
        
        temp_dir = st.text_input(
            t("settings.temp_dir"),
            value=current_config.get('data_processing', {}).get('temp_dir', './temp')
        )
        
        cleanup_temp_files = st.checkbox(
            t("settings.cleanup_temp_files_label"),
            value=current_config.get('data_processing', {}).get('auto_cleanup', True)
        )
    
    with tab4:
        st.subheader(t("settings.config_management"))
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button(t("settings.save_config"), use_container_width=True):
                # Prepare new configuration
                new_config = {
                    'ui_settings': {
                        'theme': theme,
                        'language': language,
                        'page_size': page_size,
                        'show_debug': show_debug,
                        'auto_refresh': auto_refresh
                    },
                    'llm_settings': {
                        'default_provider': default_provider,
                        'enabled_providers': enabled_providers,
                        'enable_fallback': enable_fallback,
                        'fallback_order': fallback_order
                    },
                    'google_settings': {
                        'model': google_model,
                        'temperature': google_temperature,
                        'max_tokens': google_max_tokens,
                        'timeout': google_timeout,
                        'retries': google_retries
                    },
                    'volcano_settings': {
                        'base_url': volcano_base_url,
                        'model': volcano_model,
                        'temperature': volcano_temperature
                    },
                    'multimodal_settings': {
                        'enabled': enable_multimodal,
                        'max_image_size': max_image_size,
                        'image_timeout': image_analysis_timeout,
                        'supported_formats': supported_formats
                    },
                    'data_processing': {
                        'max_file_size': max_file_size,
                        'chunk_size': chunk_size,
                        'memory_limit': memory_limit,
                        'temp_dir': temp_dir,
                        'auto_cleanup': cleanup_temp_files
                    }
                }
                
                try:
                    config_manager.save_system_config(new_config)
                    st.success(t("settings.config_saved"))
                except Exception as e:
                    st.error(f"{t('settings.config_save_failed')}: {str(e)}")
        
        with col2:
            if st.button(t("settings.reset_analysis_config"), use_container_width=True):
                if st.warning(t("messages.reset_warning")):
                    try:
                        config_manager.reset_analysis_config()
                        st.success(t("messages.analysis_config_reset"))
                        st.rerun()
                    except Exception as e:
                        st.error(t("messages.analysis_config_reset_failed"))
        
        with col3:
            if st.button(t("settings.reset_system_config"), use_container_width=True):
                if st.warning(t("messages.reset_warning")):
                    try:
                        config_manager.reset_system_config()
                        st.success(t("messages.system_config_reset"))
                        st.rerun()
                    except Exception as e:
                        st.error(t("messages.system_config_reset_failed"))
        
        with col4:
            # Export configuration
            if st.button(t("settings.download_config"), use_container_width=True):
                try:
                    config_data = config_manager.get_system_config()
                    config_json = json.dumps(config_data, indent=2, ensure_ascii=False)
                    st.download_button(
                        label=t("settings.download_config"),
                        data=config_json,
                        file_name=f"system_config_{st.session_state.get('timestamp', 'default')}.json",
                        mime="application/json"
                    )
                except Exception as e:
                    st.error(t("messages.config_export_failed"))
        
        # Import configuration
        uploaded_file = st.file_uploader(t("settings.import_config"), type=['json'])
        if uploaded_file is not None:
            try:
                imported_config = json.load(uploaded_file)
                if st.button(t("settings.import_config"), use_container_width=True):
                    config_manager.save_system_config(imported_config)
                    st.success(t("messages.config_import_success"))
                    st.info(t("messages.refresh_page_notice"))
            except Exception as e:
                st.error(f"{t('messages.config_import_failed')}: {str(e)}")
    
    with tab5:
        st.subheader("🔍 API Status & Diagnostics")
        
        # API Key validation
        st.markdown("### 🔑 API Configuration Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Google API**")
            google_key = os.getenv("GOOGLE_API_KEY")
            if google_key and len(google_key) > 20:
                st.success("✅ Google API Key configured")
            else:
                st.error("❌ Google API Key not configured")
                st.info("Set GOOGLE_API_KEY in .env file")
        
        with col2:
            st.markdown("**Volcano ARK API**")
            volcano_key = os.getenv("ARK_API_KEY")
            if volcano_key and len(volcano_key) > 20:
                st.success("✅ Volcano ARK API Key configured")
            else:
                st.error("❌ Volcano ARK API Key not configured")
                st.info("Set ARK_API_KEY in .env file")
        
        # System information
        st.markdown("### 📊 System Information")
        
        system_info = {
            "Current Language": t("settings.interface_language"),
            "Theme": theme,
            "Memory Limit": f"{memory_limit} GB",
            "Max File Size": f"{max_file_size} MB",
            "Temp Directory": temp_dir,
            "Auto Cleanup": "Enabled" if cleanup_temp_files else "Disabled"
        }
        
        for key, value in system_info.items():
            st.text(f"{key}: {value}")
        
        # LLM Provider Status
        st.markdown("### 🤖 LLM Provider Status")
        
        provider_status = {
            "Default Provider": default_provider,
            "Enabled Providers": ", ".join(enabled_providers),
            "Fallback Enabled": "Yes" if enable_fallback else "No",
            "Fallback Order": " → ".join(fallback_order)
        }
        
        for key, value in provider_status.items():
            st.text(f"{key}: {value}")
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Clear Cache", use_container_width=True):
                st.cache_data.clear()
                st.success("✅ Cache cleared")
        
        with col2:
            if st.button("🧹 Clear Memory", use_container_width=True):
                import gc
                gc.collect()
                st.success("✅ Memory cleared")
        
        with col3:
            if st.button("🔄 Reset Execution", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.success("✅ Execution status reset")
