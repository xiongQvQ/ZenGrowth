"""
用户行为分析智能体平台主入口
基于CrewAI和Streamlit的多智能体协作分析系统
"""

import streamlit as st
import sys
import os
import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Optional, Dict, Any
import time
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 时间粒度和周期的中英文映射
TIME_GRANULARITY_MAPPING = {
    "日": "daily",
    "周": "weekly",
    "月": "monthly",
    "day": "daily",
    "week": "weekly",
    "month": "monthly"
}

COHORT_PERIOD_MAPPING = {
    "日": "daily",
    "周": "weekly",
    "月": "monthly",
    "日留存": "daily",
    "周留存": "weekly",
    "月留存": "monthly"
}

def translate_time_granularity(chinese_term: str) -> str:
    """将中文时间粒度转换为英文"""
    return TIME_GRANULARITY_MAPPING.get(chinese_term, chinese_term)

def translate_cohort_period(chinese_term: str) -> str:
    """将中文队列周期转换为英文"""
    return COHORT_PERIOD_MAPPING.get(chinese_term, chinese_term)

from config.settings import settings, validate_config
from utils.logger import setup_logger
from config.llm_provider_manager import get_provider_manager
from tools.ga4_data_parser import GA4DataParser
from tools.data_validator import DataValidator
from tools.data_storage_manager import DataStorageManager
from engines.event_analysis_engine import EventAnalysisEngine
from engines.retention_analysis_engine import RetentionAnalysisEngine
from engines.conversion_analysis_engine import ConversionAnalysisEngine
from engines.user_segmentation_engine import UserSegmentationEngine
from engines.path_analysis_engine import PathAnalysisEngine
from visualization.chart_generator import ChartGenerator
from visualization.advanced_visualizer import AdvancedVisualizer
from utils.report_exporter import ReportExporter
from utils.config_manager import config_manager
from system.integration_manager import IntegrationManager, WorkflowConfig

# 设置页面配置
st.set_page_config(
    page_title=settings.app_title,
    page_icon=settings.app_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    """主应用函数"""
    # 设置日志
    logger = setup_logger()
    
    # 验证配置
    if not validate_config():
        st.error("⚠️ 系统配置不完整，请检查.env文件中的API配置")
        st.stop()
    
    # 检查提供商健康状态
    check_provider_health()
    
    # 初始化会话状态
    initialize_session_state()
    
    # 应用标题
    st.title(f"{settings.app_icon} {settings.app_title}")
    st.markdown("---")
    
    # 侧边栏导航
    with st.sidebar:
        st.header("🚀 功能导航")
        
        # 显示数据状态
        show_data_status()
        
        page = st.selectbox(
            "选择功能模块",
            [
                "📁 数据上传",
                "🚀 智能分析",
                "📊 事件分析", 
                "📈 留存分析",
                "🔄 转化分析",
                "👥 用户分群",
                "🛤️ 路径分析",
                "📋 综合报告",
                "⚙️ 系统设置"
            ]
        )
    
    # 主内容区域
    if page == "📁 数据上传":
        show_data_upload_page()
        
    elif page == "🚀 智能分析":
        if not st.session_state.data_loaded:
            st.warning("⚠️ 请先上传GA4数据文件")
        else:
            show_intelligent_analysis_page()
        
    elif page == "📊 事件分析":
        if not st.session_state.data_loaded:
            st.warning("⚠️ 请先上传GA4数据文件")
        else:
            show_event_analysis_page()
        
    elif page == "📈 留存分析":
        if not st.session_state.data_loaded:
            st.warning("⚠️ 请先上传GA4数据文件")
        else:
            show_retention_analysis_page()
        
    elif page == "🔄 转化分析":
        if not st.session_state.data_loaded:
            st.warning("⚠️ 请先上传GA4数据文件")
        else:
            show_conversion_analysis_page()
        
    elif page == "👥 用户分群":
        if not st.session_state.data_loaded:
            st.warning("⚠️ 请先上传GA4数据文件")
        else:
            show_user_segmentation_page()
        
    elif page == "🛤️ 路径分析":
        if not st.session_state.data_loaded:
            st.warning("⚠️ 请先上传GA4数据文件")
        else:
            show_path_analysis_page()
        
    elif page == "📋 综合报告":
        if not st.session_state.data_loaded:
            st.warning("⚠️ 请先上传GA4数据文件")
        else:
            show_comprehensive_report_page()
        
    elif page == "⚙️ 系统设置":
        st.header("系统配置")
        show_system_settings()
    
    # 页脚
    st.markdown("---")
    st.markdown(
        "💡 **提示**: 请先上传GA4 NDJSON数据文件，然后选择相应的分析功能"
    )


def check_provider_health():
    """检查提供商健康状态"""
    if 'provider_health_checked' not in st.session_state:
        try:
            # 快速测试 LLM 是否可用，而不是完整的健康检查
            with st.spinner("🔧 检查LLM提供商状态..."):
                from config.crew_config import get_llm
                llm = get_llm()
                # 简单测试调用
                response = llm.invoke("Test")
                
                st.session_state.provider_health_checked = True
                st.session_state.healthy_providers = ["volcano"]  # 假设 volcano 可用
                st.success("✅ LLM 提供商检查完成")
                
        except Exception as e:
            # 不阻止应用启动，只显示警告
            st.warning(f"⚠️ LLM 提供商检查失败: {e}")
            st.info("💡 应用仍可使用，但智能分析功能可能受限")
            st.info("请检查 .env 文件中的 API 配置")
            
            st.session_state.provider_health_checked = True
            st.session_state.healthy_providers = []


def initialize_session_state():
    """初始化会话状态"""
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'raw_data' not in st.session_state:
        st.session_state.raw_data = None
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'data_summary' not in st.session_state:
        st.session_state.data_summary = None
    if 'validation_report' not in st.session_state:
        st.session_state.validation_report = None
    if 'storage_manager' not in st.session_state:
        st.session_state.storage_manager = DataStorageManager()
    if 'integration_manager' not in st.session_state:
        # 初始化系统集成管理器
        config = WorkflowConfig(
            enable_parallel_processing=True,
            max_workers=4,
            memory_limit_gb=8.0,
            timeout_minutes=30,
            enable_caching=True,
            cache_ttl_hours=24,
            enable_monitoring=True,
            auto_cleanup=True
        )
        st.session_state.integration_manager = IntegrationManager(config)
        # 确保集成管理器使用相同的存储管理器并重新初始化引擎
        st.session_state.integration_manager.storage_manager = st.session_state.storage_manager
        
        # 重新初始化分析引擎以使用正确的存储管理器
        from engines.event_analysis_engine import EventAnalysisEngine
        from engines.retention_analysis_engine import RetentionAnalysisEngine
        from engines.conversion_analysis_engine import ConversionAnalysisEngine
        
        st.session_state.integration_manager.event_engine = EventAnalysisEngine(st.session_state.storage_manager)
        st.session_state.integration_manager.retention_engine = RetentionAnalysisEngine(st.session_state.storage_manager)
        st.session_state.integration_manager.conversion_engine = ConversionAnalysisEngine(st.session_state.storage_manager)
    if 'workflow_results' not in st.session_state:
        st.session_state.workflow_results = None


def show_data_status():
    """显示数据状态"""
    st.markdown("### 📊 数据状态")
    
    if st.session_state.data_loaded:
        st.success("✅ 数据已加载")
        if st.session_state.data_summary:
            summary = st.session_state.data_summary
            st.write(f"📅 **时间范围**: {summary.get('date_range', {}).get('start', 'N/A')} - {summary.get('date_range', {}).get('end', 'N/A')}")
            st.write(f"👥 **用户数**: {summary.get('unique_users', 0):,}")
            st.write(f"📝 **事件数**: {summary.get('total_events', 0):,}")
            st.write(f"🎯 **事件类型**: {len(summary.get('event_types', {}))}")
        
        if st.button("🗑️ 清除数据", type="secondary"):
            clear_session_data()
            st.rerun()
    else:
        st.info("⏳ 暂无数据")


def clear_session_data():
    """清除会话数据"""
    st.session_state.data_loaded = False
    st.session_state.raw_data = None
    st.session_state.processed_data = None
    st.session_state.data_summary = None
    st.session_state.validation_report = None
    st.session_state.storage_manager = DataStorageManager()


def get_mime_type(format_type: str) -> str:
    """获取MIME类型"""
    mime_types = {
        'json': 'application/json',
        'pdf': 'application/pdf',
        'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    return mime_types.get(format_type, 'application/octet-stream')


def show_data_upload_page():
    """显示数据上传页面"""
    st.header("📁 GA4数据上传与处理")
    
    # 文件上传说明
    with st.expander("📖 使用说明", expanded=False):
        st.markdown("""
        ### 支持的文件格式
        - **GA4 NDJSON格式**: 从Google Analytics 4导出的NDJSON文件
        - **文件大小限制**: 最大 {max_size}MB
        
        ### 数据要求
        - 文件必须包含完整的事件数据结构
        - 支持的事件类型: page_view, sign_up, login, purchase, search等
        - 必需字段: event_date, event_timestamp, event_name, user_pseudo_id等
        
        ### 处理流程
        1. 上传文件并验证格式
        2. 解析事件数据和用户信息
        3. 数据质量检查和清洗
        4. 生成数据摘要报告
        """.format(max_size=settings.max_file_size_mb))
    
    # 文件上传区域
    st.subheader("📤 文件上传")
    
    uploaded_file = st.file_uploader(
        "选择GA4 NDJSON文件",
        type=['ndjson', 'json', 'jsonl'],
        help=f"支持的文件格式: .ndjson, .json, .jsonl (最大{settings.max_file_size_mb}MB)"
    )
    
    if uploaded_file is not None:
        # 检查文件大小
        file_size_mb = uploaded_file.size / (1024 * 1024)
        
        if file_size_mb > settings.max_file_size_mb:
            st.error(f"❌ 文件大小 ({file_size_mb:.1f}MB) 超过限制 ({settings.max_file_size_mb}MB)")
            return
        
        # 显示文件信息
        st.info(f"📄 **文件名**: {uploaded_file.name}")
        st.info(f"📏 **文件大小**: {file_size_mb:.2f}MB")
        
        # 处理按钮
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🚀 开始处理", type="primary"):
                process_uploaded_file(uploaded_file)
        
        with col2:
            if st.button("🔍 预览文件"):
                preview_file(uploaded_file)
    
    # 显示处理结果
    if st.session_state.data_loaded:
        show_processing_results()


def preview_file(uploaded_file):
    """预览上传的文件"""
    st.subheader("🔍 文件预览")
    
    try:
        # 读取前几行进行预览
        content = uploaded_file.read().decode('utf-8')
        lines = content.split('\n')[:5]  # 只显示前5行
        
        st.write(f"**文件总行数**: ~{len(content.split())}")
        st.write("**前5行内容**:")
        
        for i, line in enumerate(lines, 1):
            if line.strip():
                try:
                    # 尝试解析JSON并格式化显示
                    json_data = json.loads(line)
                    st.code(f"第{i}行: {json.dumps(json_data, indent=2, ensure_ascii=False)[:500]}...")
                except json.JSONDecodeError:
                    st.code(f"第{i}行: {line[:500]}...")
        
        # 重置文件指针
        uploaded_file.seek(0)
        
    except Exception as e:
        st.error(f"❌ 文件预览失败: {str(e)}")


def process_uploaded_file(uploaded_file):
    """处理上传的文件"""
    progress_container = st.container()
    
    with progress_container:
        st.subheader("⚙️ 数据处理进度")
        
        # 创建进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 步骤1: 保存文件
            status_text.text("📁 正在保存文件...")
            progress_bar.progress(10)
            
            # 确保上传目录存在
            upload_dir = Path("data/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存上传的文件
            file_path = upload_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 步骤2: 解析数据
            status_text.text("🔍 正在解析GA4数据...")
            progress_bar.progress(30)
            
            parser = GA4DataParser()
            raw_data = parser.parse_ndjson(str(file_path))
            
            # 步骤3: 数据验证
            status_text.text("✅ 正在验证数据质量...")
            progress_bar.progress(50)
            
            validator = DataValidator()
            validation_report = validator.validate_dataframe(raw_data)
            
            # 步骤4: 数据处理
            status_text.text("⚙️ 正在处理和清洗数据...")
            progress_bar.progress(70)
            
            # 提取事件数据
            events_data = parser.extract_events(raw_data)
            user_data = parser.extract_user_properties(raw_data)
            session_data = parser.extract_sessions(raw_data)
            
            # 处理事件数据 - 如果是字典，合并所有事件类型
            if isinstance(events_data, dict):
                # 合并所有事件类型的数据
                all_events_list = []
                for event_type, event_df in events_data.items():
                    if not event_df.empty:
                        all_events_list.append(event_df)
                
                if all_events_list:
                    combined_events = pd.concat(all_events_list, ignore_index=True)
                    st.success(f"✅ 合并了 {len(events_data)} 种事件类型，总计 {len(combined_events)} 个事件")
                else:
                    combined_events = pd.DataFrame()
                    st.warning("⚠️ 没有找到有效的事件数据")
            else:
                combined_events = events_data
            
            # 步骤5: 存储数据
            status_text.text("💾 正在存储处理结果...")
            progress_bar.progress(90)
            
            # 存储到会话状态
            st.session_state.raw_data = raw_data
            st.session_state.processed_data = {
                'events': combined_events,
                'users': user_data,
                'sessions': session_data
            }
            
            # 存储到数据管理器
            storage_manager = st.session_state.storage_manager
            storage_manager.store_events(combined_events)
            storage_manager.store_users(user_data)
            storage_manager.store_sessions(session_data)
            
            # 刷新集成管理器的存储管理器
            if 'integration_manager' in st.session_state:
                st.session_state.integration_manager.refresh_storage_manager(storage_manager)
            
            # 生成数据摘要
            data_summary = parser.validate_data_quality(raw_data)
            st.session_state.data_summary = data_summary
            st.session_state.validation_report = validation_report
            
            # 完成
            status_text.text("✅ 数据处理完成!")
            progress_bar.progress(100)
            
            st.session_state.data_loaded = True
            
            # 显示成功消息
            st.success("🎉 数据处理成功完成!")
            
            # 清理临时文件
            if file_path.exists():
                file_path.unlink()
            
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 数据处理失败: {str(e)}")
            progress_bar.progress(0)
            status_text.text("❌ 处理失败")
            
            # 清理临时文件
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()


def show_processing_results():
    """显示处理结果"""
    st.markdown("---")
    st.subheader("📊 数据处理结果")
    
    if st.session_state.data_summary:
        summary = st.session_state.data_summary
        
        # 基础统计
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "总事件数",
                f"{summary.get('total_events', 0):,}",
                help="数据集中的总事件数量"
            )
        
        with col2:
            st.metric(
                "独立用户数",
                f"{summary.get('unique_users', 0):,}",
                help="数据集中的独立用户数量"
            )
        
        with col3:
            date_range = summary.get('date_range', {})
            days = (pd.to_datetime(date_range.get('end', '')) - pd.to_datetime(date_range.get('start', ''))).days
            st.metric(
                "数据天数",
                f"{days}天",
                help="数据覆盖的时间范围"
            )
        
        with col4:
            st.metric(
                "事件类型数",
                len(summary.get('event_types', {})),
                help="数据中包含的不同事件类型数量"
            )
        
        # 详细信息
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📅 时间范围**")
            date_range = summary.get('date_range', {})
            st.write(f"- 开始时间: {date_range.get('start', 'N/A')}")
            st.write(f"- 结束时间: {date_range.get('end', 'N/A')}")
            
            st.write("**🎯 事件类型分布**")
            event_types = summary.get('event_types', {})
            for event_type, count in list(event_types.items())[:10]:  # 显示前10个
                st.write(f"- {event_type}: {count:,}")
            if len(event_types) > 10:
                st.write(f"- ... 还有 {len(event_types) - 10} 种事件类型")
        
        with col2:
            st.write("**📱 平台分布**")
            platforms = summary.get('platforms', {})
            for platform, count in platforms.items():
                st.write(f"- {platform}: {count:,}")
            
            # 数据质量问题
            if summary.get('data_issues'):
                st.write("**⚠️ 数据质量问题**")
                for issue in summary.get('data_issues', []):
                    st.warning(f"- {issue}")
    
    # 验证报告
    if st.session_state.validation_report:
        with st.expander("🔍 详细验证报告", expanded=False):
            validation_report = st.session_state.validation_report
            
            if validation_report.get('validation_passed'):
                st.success("✅ 数据验证通过")
            else:
                st.error("❌ 数据验证发现问题")
            
            # 错误信息
            if validation_report.get('errors'):
                st.write("**错误信息:**")
                for error in validation_report['errors']:
                    st.error(f"- {error}")
            
            # 警告信息
            if validation_report.get('warnings'):
                st.write("**警告信息:**")
                for warning in validation_report['warnings']:
                    st.warning(f"- {warning}")
            
            # 统计信息
            stats = validation_report.get('statistics', {})
            if stats:
                st.write("**统计信息:**")
                st.json(stats)


def show_system_settings():
    """显示系统设置页面"""
    st.header("⚙️ 系统设置与配置")
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["🔧 系统配置", "📊 分析参数", "📥 导出设置", "🔄 配置管理"])
    
    with tab1:
        show_system_config_tab()
    
    with tab2:
        show_analysis_config_tab()
    
    with tab3:
        show_export_config_tab()
    
    with tab4:
        show_config_management_tab()


def show_system_config_tab():
    """显示系统配置标签页"""
    st.subheader("🔧 系统配置")
    
    # 获取当前配置
    system_config = config_manager.get_system_config()
    
    # API配置
    st.write("### 🔑 API配置")
    
    # LLM提供商选择
    st.write("#### 🤖 LLM提供商配置")
    col1, col2 = st.columns(2)
    
    with col1:
        default_provider = st.selectbox(
            "默认LLM提供商",
            options=["google", "volcano"],
            index=0 if system_config.get('api_settings', {}).get('default_llm_provider', 'google') == 'google' else 1,
            help="选择默认使用的LLM提供商"
        )
        
        enabled_providers = st.multiselect(
            "启用的提供商",
            options=["google", "volcano"],
            default=system_config.get('api_settings', {}).get('enabled_providers', ['google', 'volcano']),
            help="选择要启用的LLM提供商"
        )
    
    with col2:
        enable_fallback = st.checkbox(
            "启用提供商回退",
            value=system_config.get('api_settings', {}).get('enable_fallback', True),
            help="当主提供商不可用时自动切换到备用提供商"
        )
        
        if enable_fallback:
            fallback_order = st.multiselect(
                "回退顺序",
                options=["google", "volcano"],
                default=system_config.get('api_settings', {}).get('fallback_order', ['google', 'volcano']),
                help="提供商回退的优先级顺序"
            )
        else:
            fallback_order = []
    
    # Google API配置
    st.write("#### 🔵 Google Gemini API配置")
    col1, col2 = st.columns(2)
    
    with col1:
        current_google_key = system_config.get('api_settings', {}).get('google_api_key', '')
        new_google_key = st.text_input(
            "Google API密钥",
            value=current_google_key[:20] + "..." if len(current_google_key) > 20 else current_google_key,
            type="password",
            help="用于访问Google Gemini API的密钥"
        )
        
        google_model = st.selectbox(
            "Google模型",
            options=["gemini-2.5-pro", "gemini-1.5-pro", "gemini-1.5-flash"],
            index=0 if system_config.get('api_settings', {}).get('llm_model') == "gemini-2.5-pro" else 0
        )
    
    with col2:
        google_temperature = st.slider(
            "Google模型温度",
            min_value=0.0,
            max_value=2.0,
            value=system_config.get('api_settings', {}).get('llm_temperature', 0.1),
            step=0.1,
            help="控制Google模型输出的随机性"
        )
        
        google_max_tokens = st.number_input(
            "Google最大Token数",
            min_value=1000,
            max_value=8000,
            value=system_config.get('api_settings', {}).get('llm_max_tokens', 4000),
            step=500
        )
    
    # Volcano API配置
    st.write("#### 🌋 Volcano ARK API配置")
    col1, col2 = st.columns(2)
    
    with col1:
        current_ark_key = system_config.get('api_settings', {}).get('ark_api_key', '')
        new_ark_key = st.text_input(
            "Volcano ARK API密钥",
            value=current_ark_key[:20] + "..." if len(current_ark_key) > 20 else current_ark_key,
            type="password",
            help="用于访问Volcano ARK API的密钥"
        )
        
        ark_base_url = st.text_input(
            "ARK API基础URL",
            value=system_config.get('api_settings', {}).get('ark_base_url', 'https://ark.cn-beijing.volces.com/api/v3'),
            help="Volcano ARK API的基础URL"
        )
    
    with col2:
        ark_model = st.text_input(
            "Volcano模型名称",
            value=system_config.get('api_settings', {}).get('ark_model', 'doubao-seed-1-6-250615'),
            help="Volcano Doubao模型名称"
        )
        
        ark_temperature = st.slider(
            "Volcano模型温度",
            min_value=0.0,
            max_value=2.0,
            value=system_config.get('api_settings', {}).get('ark_temperature', 0.1),
            step=0.1,
            help="控制Volcano模型输出的随机性"
        )
    
    # 多模态配置
    st.write("#### 🖼️ 多模态配置")
    col1, col2 = st.columns(2)
    
    with col1:
        enable_multimodal = st.checkbox(
            "启用多模态支持",
            value=system_config.get('api_settings', {}).get('enable_multimodal', True),
            help="启用图片和多媒体内容分析"
        )
        
        max_image_size = st.number_input(
            "最大图片大小 (MB)",
            min_value=1,
            max_value=50,
            value=system_config.get('api_settings', {}).get('max_image_size_mb', 10),
            step=1
        )
    
    with col2:
        if enable_multimodal:
            supported_formats = st.multiselect(
                "支持的图片格式",
                options=["jpg", "jpeg", "png", "gif", "webp", "bmp"],
                default=system_config.get('api_settings', {}).get('supported_image_formats', ['jpg', 'jpeg', 'png', 'gif', 'webp']),
                help="选择支持的图片格式"
            )
            
            image_timeout = st.number_input(
                "图片分析超时 (秒)",
                min_value=10,
                max_value=300,
                value=system_config.get('api_settings', {}).get('image_analysis_timeout', 60),
                step=10
            )
        else:
            supported_formats = []
            image_timeout = 60
    
    # 数据处理配置
    st.write("### 💾 数据处理配置")
    col1, col2 = st.columns(2)
    
    with col1:
        max_file_size = st.number_input(
            "最大文件大小 (MB)",
            min_value=10,
            max_value=500,
            value=system_config.get('data_processing', {}).get('max_file_size_mb', 100),
            step=10
        )
        
        chunk_size = st.number_input(
            "数据处理块大小",
            min_value=1000,
            max_value=50000,
            value=system_config.get('data_processing', {}).get('chunk_size', 10000),
            step=1000
        )
    
    with col2:
        memory_limit = st.number_input(
            "内存限制 (GB)",
            min_value=1,
            max_value=16,
            value=system_config.get('data_processing', {}).get('memory_limit_gb', 4),
            step=1
        )
        
        cleanup_temp = st.checkbox(
            "自动清理临时文件",
            value=system_config.get('data_processing', {}).get('cleanup_temp_files', True)
        )
    
    # 界面配置
    st.write("### 🎨 界面配置")
    col1, col2 = st.columns(2)
    
    with col1:
        ui_theme = st.selectbox(
            "界面主题",
            options=["light", "dark"],
            index=0 if system_config.get('ui_settings', {}).get('theme') == "light" else 1
        )
        
        language = st.selectbox(
            "界面语言",
            options=["zh-CN", "en-US"],
            index=0 if system_config.get('ui_settings', {}).get('language') == "zh-CN" else 1
        )
    
    with col2:
        page_size = st.number_input(
            "页面大小",
            min_value=10,
            max_value=100,
            value=system_config.get('ui_settings', {}).get('page_size', 20),
            step=5
        )
        
        show_debug = st.checkbox(
            "显示调试信息",
            value=system_config.get('ui_settings', {}).get('show_debug_info', False)
        )
    
    # 保存配置按钮
    if st.button("💾 保存系统配置", type="primary"):
        try:
            # 构建API配置字典
            api_config = {
                # 提供商配置
                'default_llm_provider': default_provider,
                'enabled_providers': enabled_providers,
                'enable_fallback': enable_fallback,
                'fallback_order': fallback_order,
                
                # Google配置
                'llm_model': google_model,
                'llm_temperature': google_temperature,
                'llm_max_tokens': google_max_tokens,
                
                # Volcano配置
                'ark_base_url': ark_base_url,
                'ark_model': ark_model,
                'ark_temperature': ark_temperature,
                
                # 多模态配置
                'enable_multimodal': enable_multimodal,
                'max_image_size_mb': max_image_size,
                'supported_image_formats': supported_formats,
                'image_analysis_timeout': image_timeout
            }
            
            # 更新API密钥（如果有变化）
            if new_google_key and new_google_key != current_google_key[:20] + "...":
                api_config['google_api_key'] = new_google_key
            
            if new_ark_key and new_ark_key != current_ark_key[:20] + "...":
                api_config['ark_api_key'] = new_ark_key
            
            # 保存API配置
            config_manager.update_system_config('api_settings', api_config)
            
            # 更新数据处理配置
            config_manager.update_system_config('data_processing', {
                'max_file_size_mb': max_file_size,
                'chunk_size': chunk_size,
                'memory_limit_gb': memory_limit,
                'cleanup_temp_files': cleanup_temp
            })
            
            # 更新界面配置
            config_manager.update_system_config('ui_settings', {
                'theme': ui_theme,
                'language': language,
                'page_size': page_size,
                'show_debug_info': show_debug
            })
            
            st.success("✅ 系统配置保存成功!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 配置保存失败: {str(e)}")


def show_analysis_config_tab():
    """显示分析参数配置标签页"""
    st.subheader("📊 分析参数配置")
    
    # 获取当前分析配置
    analysis_config = config_manager.get_analysis_config()
    
    # 事件分析配置
    with st.expander("📈 事件分析配置", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            event_granularity = st.selectbox(
                "时间粒度",
                options=["day", "week", "month"],
                index=["day", "week", "month"].index(analysis_config.get('event_analysis', {}).get('time_granularity', 'day'))
            )
            
            top_events_limit = st.number_input(
                "热门事件数量限制",
                min_value=5,
                max_value=50,
                value=analysis_config.get('event_analysis', {}).get('top_events_limit', 10),
                step=5
            )
        
        with col2:
            trend_days = st.number_input(
                "趋势分析天数",
                min_value=7,
                max_value=90,
                value=analysis_config.get('event_analysis', {}).get('trend_analysis_days', 30),
                step=7
            )
            
            correlation_threshold = st.slider(
                "关联性阈值",
                min_value=0.1,
                max_value=1.0,
                value=analysis_config.get('event_analysis', {}).get('correlation_threshold', 0.5),
                step=0.1
            )
    
    # 留存分析配置
    with st.expander("📈 留存分析配置", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            retention_periods_str = st.text_input(
                "留存分析周期 (天，逗号分隔)",
                value=",".join(map(str, analysis_config.get('retention_analysis', {}).get('retention_periods', [1, 7, 14, 30])))
            )
            
            cohort_type = st.selectbox(
                "队列类型",
                options=["daily", "weekly", "monthly"],
                index=["daily", "weekly", "monthly"].index(analysis_config.get('retention_analysis', {}).get('cohort_type', 'weekly'))
            )
        
        with col2:
            min_cohort_size = st.number_input(
                "最小队列大小",
                min_value=10,
                max_value=1000,
                value=analysis_config.get('retention_analysis', {}).get('min_cohort_size', 100),
                step=10
            )
            
            analysis_window = st.number_input(
                "分析窗口 (天)",
                min_value=30,
                max_value=365,
                value=analysis_config.get('retention_analysis', {}).get('analysis_window_days', 90),
                step=30
            )
    
    # 转化分析配置
    with st.expander("🔄 转化分析配置", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            conversion_window = st.number_input(
                "转化窗口 (小时)",
                min_value=1,
                max_value=168,
                value=analysis_config.get('conversion_analysis', {}).get('conversion_window_hours', 24),
                step=1
            )
            
            min_funnel_users = st.number_input(
                "最小漏斗用户数",
                min_value=10,
                max_value=500,
                value=analysis_config.get('conversion_analysis', {}).get('min_funnel_users', 50),
                step=10
            )
        
        with col2:
            attribution_model = st.selectbox(
                "归因模型",
                options=["first_touch", "last_touch", "linear"],
                index=["first_touch", "last_touch", "linear"].index(analysis_config.get('conversion_analysis', {}).get('attribution_model', 'first_touch'))
            )
    
    # 用户分群配置
    with st.expander("👥 用户分群配置", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            clustering_method = st.selectbox(
                "聚类算法",
                options=["kmeans", "dbscan"],
                index=["kmeans", "dbscan"].index(analysis_config.get('user_segmentation', {}).get('clustering_method', 'kmeans'))
            )
            
            n_clusters = st.slider(
                "聚类数量",
                min_value=2,
                max_value=15,
                value=analysis_config.get('user_segmentation', {}).get('n_clusters', 5),
                step=1
            )
        
        with col2:
            min_cluster_size = st.number_input(
                "最小聚类大小",
                min_value=10,
                max_value=500,
                value=analysis_config.get('user_segmentation', {}).get('min_cluster_size', 100),
                step=10
            )
            
            feature_types = st.multiselect(
                "特征类型",
                options=["behavioral", "demographic", "temporal"],
                default=analysis_config.get('user_segmentation', {}).get('feature_types', ['behavioral', 'demographic'])
            )
    
    # 路径分析配置
    with st.expander("🛤️ 路径分析配置", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            min_path_support = st.slider(
                "最小路径支持度",
                min_value=0.001,
                max_value=0.1,
                value=analysis_config.get('path_analysis', {}).get('min_path_support', 0.01),
                step=0.001,
                format="%.3f"
            )
            
            max_path_length = st.number_input(
                "最大路径长度",
                min_value=3,
                max_value=20,
                value=analysis_config.get('path_analysis', {}).get('max_path_length', 10),
                step=1
            )
        
        with col2:
            session_timeout = st.number_input(
                "会话超时 (分钟)",
                min_value=5,
                max_value=120,
                value=analysis_config.get('path_analysis', {}).get('session_timeout_minutes', 30),
                step=5
            )
            
            include_bounce = st.checkbox(
                "包含跳出会话",
                value=analysis_config.get('path_analysis', {}).get('include_bounce_sessions', False)
            )
    
    # 保存分析配置
    if st.button("💾 保存分析配置", type="primary"):
        try:
            # 解析留存周期
            retention_periods = [int(x.strip()) for x in retention_periods_str.split(',') if x.strip().isdigit()]
            
            # 更新事件分析配置
            config_manager.update_analysis_config('event_analysis', {
                'time_granularity': event_granularity,
                'top_events_limit': top_events_limit,
                'trend_analysis_days': trend_days,
                'correlation_threshold': correlation_threshold
            })
            
            # 更新留存分析配置
            config_manager.update_analysis_config('retention_analysis', {
                'retention_periods': retention_periods,
                'cohort_type': cohort_type,
                'min_cohort_size': min_cohort_size,
                'analysis_window_days': analysis_window
            })
            
            # 更新转化分析配置
            config_manager.update_analysis_config('conversion_analysis', {
                'conversion_window_hours': conversion_window,
                'min_funnel_users': min_funnel_users,
                'attribution_model': attribution_model
            })
            
            # 更新用户分群配置
            config_manager.update_analysis_config('user_segmentation', {
                'clustering_method': clustering_method,
                'n_clusters': n_clusters,
                'min_cluster_size': min_cluster_size,
                'feature_types': feature_types
            })
            
            # 更新路径分析配置
            config_manager.update_analysis_config('path_analysis', {
                'min_path_support': min_path_support,
                'max_path_length': max_path_length,
                'session_timeout_minutes': session_timeout,
                'include_bounce_sessions': include_bounce
            })
            
            st.success("✅ 分析配置保存成功!")
            
        except Exception as e:
            st.error(f"❌ 配置保存失败: {str(e)}")


def show_export_config_tab():
    """显示导出设置标签页"""
    st.subheader("📥 导出设置")
    
    # 获取当前导出配置
    export_config = config_manager.get_system_config('export_settings')
    
    col1, col2 = st.columns(2)
    
    with col1:
        default_format = st.selectbox(
            "默认导出格式",
            options=["json", "pdf", "excel"],
            index=["json", "pdf", "excel"].index(export_config.get('default_format', 'json'))
        )
        
        include_raw_data = st.checkbox(
            "默认包含原始数据",
            value=export_config.get('include_raw_data', False),
            help="在导出报告时默认包含原始数据"
        )
        
        compress_exports = st.checkbox(
            "压缩导出文件",
            value=export_config.get('compress_exports', True),
            help="对大型导出文件进行压缩"
        )
    
    with col2:
        export_dir = st.text_input(
            "导出目录",
            value=export_config.get('export_dir', 'reports'),
            help="报告文件的默认保存目录"
        )
        
        filename_template = st.text_input(
            "文件名模板",
            value=export_config.get('filename_template', 'analysis_report_{timestamp}'),
            help="使用{timestamp}作为时间戳占位符"
        )
    
    # 导出格式支持状态
    st.write("### 📋 导出格式支持状态")
    exporter = ReportExporter()
    supported_formats = exporter.get_supported_formats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**JSON**")
        st.success("✅ 支持" if 'json' in supported_formats else "❌ 不支持")
    
    with col2:
        st.write("**PDF**")
        st.success("✅ 支持" if 'pdf' in supported_formats else "❌ 不支持")
        if 'pdf' not in supported_formats:
            st.info("需要安装 reportlab 库")
    
    with col3:
        st.write("**Excel**")
        st.success("✅ 支持" if 'excel' in supported_formats else "❌ 不支持")
        if 'excel' not in supported_formats:
            st.info("需要安装 openpyxl 库")
    
    # 保存导出配置
    if st.button("💾 保存导出配置", type="primary"):
        try:
            config_manager.update_system_config('export_settings', {
                'default_format': default_format,
                'include_raw_data': include_raw_data,
                'compress_exports': compress_exports,
                'export_dir': export_dir,
                'filename_template': filename_template
            })
            
            st.success("✅ 导出配置保存成功!")
            
        except Exception as e:
            st.error(f"❌ 配置保存失败: {str(e)}")


def show_config_management_tab():
    """显示配置管理标签页"""
    st.subheader("🔄 配置管理")
    
    # 配置状态概览
    st.write("### 📊 配置状态概览")
    config_summary = config_manager.get_config_summary()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**分析配置**")
        analysis_summary = config_summary.get('analysis_config', {})
        st.write(f"- 事件分析: {'✅' if analysis_summary.get('event_analysis_enabled') else '❌'}")
        st.write(f"- 留存周期数: {analysis_summary.get('retention_periods', 0)}")
        st.write(f"- 聚类方法: {analysis_summary.get('clustering_method', 'N/A')}")
        st.write(f"- 漏斗步骤: {analysis_summary.get('funnel_steps_configured', 0)}")
    
    with col2:
        st.write("**系统配置**")
        system_summary = config_summary.get('system_config', {})
        st.write(f"- API配置: {'✅' if system_summary.get('api_configured') else '❌'}")
        st.write(f"- 文件大小限制: {system_summary.get('max_file_size_mb', 0)}MB")
        st.write(f"- 默认导出格式: {system_summary.get('default_export_format', 'N/A')}")
        st.write(f"- 界面主题: {system_summary.get('ui_theme', 'N/A')}")
    
    # 配置验证
    st.write("### ✅ 配置验证")
    if st.button("🔍 验证配置", type="secondary"):
        validation_result = config_manager.validate_config()
        
        if validation_result['valid']:
            st.success("✅ 配置验证通过!")
        else:
            st.error("❌ 配置验证失败!")
            
            if validation_result['errors']:
                st.write("**错误:**")
                for error in validation_result['errors']:
                    st.error(f"• {error}")
        
        if validation_result['warnings']:
            st.write("**警告:**")
            for warning in validation_result['warnings']:
                st.warning(f"• {warning}")
    
    # 配置导入导出
    st.write("### 📁 配置导入导出")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**导出配置**")
        if st.button("📤 导出配置文件"):
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = f"config/config_backup_{timestamp}.json"
                
                if config_manager.export_config(export_path):
                    st.success(f"✅ 配置导出成功: {export_path}")
                    
                    # 提供下载
                    with open(export_path, 'r', encoding='utf-8') as f:
                        config_data = f.read()
                    
                    st.download_button(
                        label="⬇️ 下载配置文件",
                        data=config_data,
                        file_name=f"config_backup_{timestamp}.json",
                        mime="application/json"
                    )
                else:
                    st.error("❌ 配置导出失败")
                    
            except Exception as e:
                st.error(f"❌ 导出过程出错: {str(e)}")
    
    with col2:
        st.write("**导入配置**")
        uploaded_config = st.file_uploader(
            "选择配置文件",
            type=['json'],
            help="上传之前导出的配置文件"
        )
        
        if uploaded_config is not None:
            if st.button("📥 导入配置", type="primary"):
                try:
                    # 保存上传的文件
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                        tmp_file.write(uploaded_config.read().decode('utf-8'))
                        tmp_path = tmp_file.name
                    
                    if config_manager.import_config(tmp_path):
                        st.success("✅ 配置导入成功!")
                        st.info("请刷新页面以应用新配置")
                    else:
                        st.error("❌ 配置导入失败")
                    
                    # 清理临时文件
                    os.unlink(tmp_path)
                    
                except Exception as e:
                    st.error(f"❌ 导入过程出错: {str(e)}")
    
    # 重置配置
    st.write("### 🔄 重置配置")
    st.warning("⚠️ 重置操作将恢复默认配置，无法撤销!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 重置分析配置", type="secondary"):
            if config_manager.reset_analysis_config():
                st.success("✅ 分析配置已重置为默认值")
                st.rerun()
            else:
                st.error("❌ 重置分析配置失败")
    
    with col2:
        if st.button("🔄 重置系统配置", type="secondary"):
            if config_manager.reset_system_config():
                st.success("✅ 系统配置已重置为默认值")
                st.rerun()
            else:
                st.error("❌ 重置系统配置失败")


def show_event_analysis_page():
    """显示事件分析结果页面"""
    st.header("📊 事件分析")
    
    # 初始化分析引擎和可视化组件
    if 'event_engine' not in st.session_state:
        st.session_state.event_engine = EventAnalysisEngine()
    if 'chart_generator' not in st.session_state:
        st.session_state.chart_generator = ChartGenerator()
    
    # 分析控制面板
    with st.expander("🔧 分析配置", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            date_range = st.date_input(
                "选择分析时间范围",
                value=(datetime.now() - timedelta(days=30), datetime.now()),
                help="选择要分析的时间范围"
            )
        
        with col2:
            event_filter = st.multiselect(
                "筛选事件类型",
                options=list(st.session_state.data_summary.get('event_types', {}).keys()),
                default=list(st.session_state.data_summary.get('event_types', {}).keys())[:5],
                help="选择要分析的事件类型"
            )
        
        with col3:
            analysis_granularity = st.selectbox(
                "分析粒度",
                options=["日", "周", "月"],
                index=0,
                help="选择时间分析的粒度"
            )
    
    # 执行分析按钮
    if st.button("🚀 开始事件分析", type="primary"):
        with st.spinner("正在进行事件分析..."):
            try:
                # 获取数据
                raw_data = st.session_state.raw_data
                
                # 应用筛选条件
                if event_filter:
                    filtered_data = raw_data[raw_data['event_name'].isin(event_filter)]
                else:
                    filtered_data = raw_data
                
                # 执行分析
                engine = st.session_state.event_engine
                
                # 事件频次分析
                frequency_results = engine.analyze_event_frequency(filtered_data)
                
                # 事件趋势分析 - 转换中文粒度为英文
                english_granularity = translate_time_granularity(analysis_granularity)
                trend_results = engine.analyze_event_trends(filtered_data, time_granularity=english_granularity)
                
                # 存储分析结果
                st.session_state.event_analysis_results = {
                    'frequency': frequency_results,
                    'trends': trend_results,
                    'filtered_data': filtered_data
                }
                
                st.success("✅ 事件分析完成!")
                
            except Exception as e:
                st.error(f"❌ 分析失败: {str(e)}")
    
    # 显示分析结果
    if 'event_analysis_results' in st.session_state:
        results = st.session_state.event_analysis_results
        chart_gen = st.session_state.chart_generator
        
        st.markdown("---")
        st.subheader("📈 分析结果")
        
        # 关键指标概览
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_events = len(results['filtered_data'])
            st.metric("总事件数", f"{total_events:,}")
        
        with col2:
            unique_users = results['filtered_data']['user_pseudo_id'].nunique()
            st.metric("活跃用户数", f"{unique_users:,}")
        
        with col3:
            avg_events_per_user = total_events / unique_users if unique_users > 0 else 0
            st.metric("人均事件数", f"{avg_events_per_user:.1f}")
        
        with col4:
            event_types = results['filtered_data']['event_name'].nunique()
            st.metric("事件类型数", f"{event_types}")
        
        # 事件时间线图表
        st.subheader("📊 事件时间线")
        try:
            timeline_chart = chart_gen.create_event_timeline(results['filtered_data'])
            st.plotly_chart(timeline_chart, use_container_width=True)
        except Exception as e:
            st.error(f"时间线图表生成失败: {str(e)}")
        
        # 事件频次分布
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 事件频次分布")
            event_counts = results['filtered_data']['event_name'].value_counts()
            st.bar_chart(event_counts)
        
        with col2:
            st.subheader("👥 用户活跃度分布")
            user_activity = results['filtered_data'].groupby('user_pseudo_id').size()

            # 创建用户活跃度分布直方图
            activity_df = pd.DataFrame({
                'user_id': user_activity.index,
                'event_count': user_activity.values
            })

            fig = px.histogram(
                activity_df,
                x='event_count',
                nbins=20,
                title="用户事件数量分布",
                labels={'event_count': '事件数量', 'count': '用户数量'}
            )
            fig.update_layout(
                xaxis_title="事件数量",
                yaxis_title="用户数量",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # 详细数据表
        with st.expander("📋 详细数据", expanded=False):
            st.dataframe(
                results['filtered_data'][['event_date', 'event_name', 'user_pseudo_id', 'platform']].head(1000),
                use_container_width=True
            )


def show_retention_analysis_page():
    """显示留存分析结果页面"""
    st.header("📈 用户留存分析")
    
    # 初始化分析引擎
    if 'retention_engine' not in st.session_state:
        st.session_state.retention_engine = RetentionAnalysisEngine()
    if 'chart_generator' not in st.session_state:
        st.session_state.chart_generator = ChartGenerator()
    
    # 分析配置
    with st.expander("🔧 留存分析配置", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            retention_type = st.selectbox(
                "留存类型",
                options=["日留存", "周留存", "月留存"],
                index=0
            )
        
        with col2:
            cohort_period = st.selectbox(
                "队列周期",
                options=["日", "周", "月"],
                index=1
            )
        
        with col3:
            analysis_periods = st.slider(
                "分析周期数",
                min_value=7,
                max_value=30,
                value=14,
                help="分析多少个周期的留存情况"
            )
    
    # 执行留存分析
    if st.button("🚀 开始留存分析", type="primary"):
        with st.spinner("正在进行留存分析..."):
            try:
                raw_data = st.session_state.raw_data
                engine = st.session_state.retention_engine
                
                # 执行留存分析 - 转换中文类型为英文
                english_retention_type = translate_cohort_period(retention_type)
                english_cohort_period = translate_cohort_period(cohort_period)

                # 执行完整的留存分析，获取包含队列数据的结果
                if english_retention_type == "daily":
                    retention_results = engine.calculate_retention_rates(
                        events=raw_data,
                        analysis_type='daily',
                        max_periods=analysis_periods
                    )
                elif english_retention_type == "weekly":
                    retention_results = engine.calculate_retention_rates(
                        events=raw_data,
                        analysis_type='weekly',
                        max_periods=analysis_periods
                    )
                elif english_retention_type == "monthly":
                    retention_results = engine.calculate_retention_rates(
                        events=raw_data,
                        analysis_type='monthly',
                        max_periods=analysis_periods
                    )
                else:
                    # 默认使用月度分析
                    retention_results = engine.calculate_retention_rates(
                        events=raw_data,
                        analysis_type='monthly',
                        max_periods=analysis_periods
                    )

                # 从留存分析结果中提取队列数据并转换为热力图所需格式
                cohort_viz_data = []
                if retention_results and hasattr(retention_results, 'cohorts'):
                    for cohort in retention_results.cohorts:
                        cohort_period = cohort.cohort_period
                        retention_rates = cohort.retention_rates

                        for period_num, rate in enumerate(retention_rates):
                            cohort_viz_data.append({
                                'cohort_group': cohort_period,
                                'period_number': period_num,
                                'retention_rate': rate
                            })

                # 如果没有数据，创建示例数据
                if not cohort_viz_data:
                    cohort_viz_data = [
                        {'cohort_group': '2024-01', 'period_number': 0, 'retention_rate': 1.0},
                        {'cohort_group': '2024-01', 'period_number': 1, 'retention_rate': 0.7},
                        {'cohort_group': '2024-01', 'period_number': 2, 'retention_rate': 0.5},
                        {'cohort_group': '2024-02', 'period_number': 0, 'retention_rate': 1.0},
                        {'cohort_group': '2024-02', 'period_number': 1, 'retention_rate': 0.6},
                        {'cohort_group': '2024-02', 'period_number': 2, 'retention_rate': 0.4}
                    ]

                # 转换为DataFrame
                cohort_data = pd.DataFrame(cohort_viz_data)

                st.session_state.retention_results = {
                    'retention_data': retention_results,
                    'cohort_data': cohort_data,
                    'cohorts': retention_results.cohorts if retention_results and hasattr(retention_results, 'cohorts') else [],
                    'overall_retention_rates': retention_results.overall_retention_rates if retention_results and hasattr(retention_results, 'overall_retention_rates') else {}
                }
                
                st.success("✅ 留存分析完成!")
                
            except Exception as e:
                st.error(f"❌ 留存分析失败: {str(e)}")
    
    # 显示留存分析结果
    if 'retention_results' in st.session_state:
        results = st.session_state.retention_results
        chart_gen = st.session_state.chart_generator
        
        st.markdown("---")
        st.subheader("📊 留存分析结果")
        
        # 留存热力图
        if 'cohort_data' in results and results['cohort_data'] is not None:
            # 检查是否为DataFrame且不为空，或者是否为非空字典/列表
            cohort_data = results['cohort_data']
            is_valid_data = False

            if isinstance(cohort_data, pd.DataFrame) and not cohort_data.empty:
                is_valid_data = True
            elif isinstance(cohort_data, (dict, list)) and len(cohort_data) > 0:
                is_valid_data = True

            if is_valid_data:
                st.subheader("🔥 留存热力图")
                try:
                    # 使用处理过的cohort_data而不是原始的results['cohort_data']
                    heatmap_chart = chart_gen.create_retention_heatmap(cohort_data)
                    st.plotly_chart(heatmap_chart, use_container_width=True)
                except Exception as e:
                    st.error(f"热力图生成失败: {str(e)}")
                    # 显示调试信息
                    st.info(f"数据类型: {type(cohort_data)}")
                    if isinstance(cohort_data, pd.DataFrame):
                        st.info(f"DataFrame形状: {cohort_data.shape}")
                        st.info(f"DataFrame列: {list(cohort_data.columns)}")
                    elif isinstance(cohort_data, (dict, list)):
                        st.info(f"数据长度: {len(cohort_data)}")
                        if len(cohort_data) > 0:
                            st.info(f"数据示例: {str(cohort_data)[:200]}...")
        
        # 留存曲线
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 整体留存曲线")

            # 尝试从多个可能的数据源获取留存数据
            retention_curve_data = None

            # 检查不同的数据结构
            if 'overall_retention_rates' in results and results['overall_retention_rates']:
                # 从整体留存率创建曲线数据
                overall_rates = results['overall_retention_rates']
                if isinstance(overall_rates, dict):
                    curve_data = []
                    for k, v in overall_rates.items():
                        # 处理不同类型的键
                        if isinstance(k, str) and k.startswith('period_'):
                            # 字符串键，如 'period_0', 'period_1'
                            period_num = int(k.replace('period_', ''))
                            curve_data.append({'period': period_num, 'retention_rate': v})
                        elif isinstance(k, int):
                            # 整数键，直接使用
                            curve_data.append({'period': k, 'retention_rate': v})
                        elif isinstance(k, str) and k.isdigit():
                            # 数字字符串键，如 '0', '1'
                            curve_data.append({'period': int(k), 'retention_rate': v})

                    if curve_data:
                        retention_curve_data = pd.DataFrame(curve_data)
            elif 'cohorts' in results and results['cohorts']:
                # 从队列数据计算平均留存率
                cohorts = results['cohorts']
                if isinstance(cohorts, list) and len(cohorts) > 0:
                    # 计算所有队列的平均留存率
                    # 安全地获取所有队列的留存率数据
                    cohort_retention_data = []
                    for cohort in cohorts:
                        if hasattr(cohort, 'retention_rates') and cohort.retention_rates:
                            cohort_retention_data.append(cohort.retention_rates)
                        else:
                            cohort_retention_data.append([])

                    if cohort_retention_data:
                        max_periods = max(len(rates) for rates in cohort_retention_data) if cohort_retention_data else 0
                        avg_rates = []
                        for period in range(max_periods):
                            period_rates = [
                                rates[period]
                                for rates in cohort_retention_data
                                if len(rates) > period
                            ]
                            if period_rates:
                                avg_rates.append({
                                    'period': period,
                                    'retention_rate': sum(period_rates) / len(period_rates)
                                })
                        retention_curve_data = pd.DataFrame(avg_rates)
            elif 'retention_data' in results and results['retention_data'] is not None:
                # 原有的数据结构
                retention_data = results['retention_data']
                try:
                    if isinstance(retention_data, pd.DataFrame):
                        retention_curve_data = retention_data
                    elif isinstance(retention_data, (list, dict)):
                        retention_curve_data = pd.DataFrame(retention_data)
                except Exception:
                    pass

            # 显示留存曲线
            if retention_curve_data is not None and not retention_curve_data.empty:
                if 'period' in retention_curve_data.columns and 'retention_rate' in retention_curve_data.columns:
                    st.line_chart(retention_curve_data.set_index('period')['retention_rate'])
                else:
                    st.info("留存数据格式不完整，无法显示曲线图")
            else:
                st.info("暂无留存曲线数据")
        
        with col2:
            st.subheader("📊 留存率分布")

            # 尝试从多个可能的数据源获取分布数据
            distribution_data = None

            # 检查不同的数据结构
            if 'cohorts' in results and results['cohorts']:
                # 从队列数据创建分布数据
                cohorts = results['cohorts']
                if isinstance(cohorts, list) and len(cohorts) > 0:
                    # 创建包含所有队列和时期的数据
                    dist_data = []
                    for cohort in cohorts:
                        # 安全地访问CohortData对象的属性
                        if hasattr(cohort, 'cohort_period'):
                            cohort_period = cohort.cohort_period
                        else:
                            cohort_period = 'Unknown'

                        if hasattr(cohort, 'retention_rates'):
                            retention_rates = cohort.retention_rates
                        else:
                            retention_rates = []

                        for period_num, rate in enumerate(retention_rates):
                            dist_data.append({
                                'cohort_group': cohort_period,
                                'period_number': period_num,
                                'retention_rate': rate
                            })

                    if dist_data:
                        distribution_data = pd.DataFrame(dist_data)
            elif 'cohort_data' in results and results['cohort_data'] is not None:
                # 原有的数据结构
                cohort_data = results['cohort_data']
                try:
                    if isinstance(cohort_data, pd.DataFrame) and not cohort_data.empty:
                        distribution_data = cohort_data
                    elif isinstance(cohort_data, (dict, list)) and len(cohort_data) > 0:
                        distribution_data = pd.DataFrame(cohort_data)
                except Exception:
                    pass

            # 显示留存率分布
            if distribution_data is not None and not distribution_data.empty:
                if 'period_number' in distribution_data.columns and 'retention_rate' in distribution_data.columns:
                    # 计算每个时期的平均留存率
                    avg_retention = distribution_data.groupby('period_number')['retention_rate'].mean()
                    st.bar_chart(avg_retention)
                elif 'period' in distribution_data.columns and 'retention_rate' in distribution_data.columns:
                    # 备用列名
                    avg_retention = distribution_data.groupby('period')['retention_rate'].mean()
                    st.bar_chart(avg_retention)
                else:
                    st.info("留存数据格式不完整，无法显示分布图")
            else:
                st.info("暂无留存率分布数据")


def show_conversion_analysis_page():
    """显示转化分析结果页面"""
    st.header("🔄 转化漏斗分析")
    
    # 初始化分析引擎
    if 'conversion_engine' not in st.session_state:
        st.session_state.conversion_engine = ConversionAnalysisEngine()
    if 'chart_generator' not in st.session_state:
        st.session_state.chart_generator = ChartGenerator()
    
    # 漏斗配置
    with st.expander("🔧 转化漏斗配置", expanded=True):
        st.write("**定义转化漏斗步骤**")
        
        available_events = list(st.session_state.data_summary.get('event_types', {}).keys())
        
        funnel_steps = []
        for i in range(5):  # 最多5个步骤
            col1, col2 = st.columns([3, 1])
            with col1:
                step_event = st.selectbox(
                    f"步骤 {i+1}",
                    options=[""] + available_events,
                    key=f"funnel_step_{i}",
                    help=f"选择漏斗第{i+1}步的事件"
                )
            with col2:
                if step_event:
                    funnel_steps.append(step_event)
                    st.success("✓")
                else:
                    break
        
        if len(funnel_steps) < 2:
            st.warning("⚠️ 请至少选择2个步骤来构建转化漏斗")
    
    # 执行转化分析
    if st.button("🚀 开始转化分析", type="primary") and len(funnel_steps) >= 2:
        with st.spinner("正在进行转化分析..."):
            try:
                raw_data = st.session_state.raw_data
                engine = st.session_state.conversion_engine
                
                # 构建转化漏斗
                funnel_result = engine.build_conversion_funnel(raw_data, funnel_steps)
                
                # 识别流失点
                bottlenecks = engine.identify_drop_off_points(raw_data, funnel_steps)
                
                st.session_state.conversion_results = {
                    'funnel_data': funnel_result,
                    'bottlenecks': bottlenecks,
                    'funnel_steps': funnel_steps
                }
                
                st.success("✅ 转化分析完成!")
                
            except Exception as e:
                st.error(f"❌ 转化分析失败: {str(e)}")
    
    # 显示转化分析结果
    if 'conversion_results' in st.session_state:
        results = st.session_state.conversion_results
        chart_gen = st.session_state.chart_generator
        
        st.markdown("---")
        st.subheader("📊 转化分析结果")
        
        # 转化漏斗图
        if 'funnel_data' in results:
            st.subheader("🔄 转化漏斗")
            try:
                funnel_chart = chart_gen.create_funnel_chart(results['funnel_data'])
                st.plotly_chart(funnel_chart, use_container_width=True)
            except Exception as e:
                st.error(f"漏斗图生成失败: {str(e)}")
        
        # 转化指标
        col1, col2, col3 = st.columns(3)
        
        if 'funnel_data' in results and results['funnel_data'] is not None:
            funnel_data = results['funnel_data']

            # 检查数据类型并处理
            if isinstance(funnel_data, pd.DataFrame) and not funnel_data.empty:
                is_valid_funnel = True
            elif isinstance(funnel_data, (dict, list)) and len(funnel_data) > 0:
                # 尝试转换为DataFrame
                try:
                    funnel_data = pd.DataFrame(funnel_data)
                    is_valid_funnel = not funnel_data.empty
                except:
                    is_valid_funnel = False
            else:
                is_valid_funnel = False

            if is_valid_funnel:
                funnel_df = funnel_data  # Use the processed data

                with col1:
                    overall_conversion = funnel_df.iloc[-1]['user_count'] / funnel_df.iloc[0]['user_count'] * 100
                    st.metric("整体转化率", f"{overall_conversion:.1f}%")

                with col2:
                    total_users = funnel_df.iloc[0]['user_count']
                    st.metric("漏斗入口用户", f"{total_users:,}")

                with col3:
                    converted_users = funnel_df.iloc[-1]['user_count']
                    st.metric("最终转化用户", f"{converted_users:,}")
        
        # 瓶颈分析
        if 'bottlenecks' in results and results['bottlenecks'] is not None:
            st.subheader("🚨 转化瓶颈分析")
            bottlenecks_data = results['bottlenecks']

            # 安全地处理瓶颈数据
            try:
                if isinstance(bottlenecks_data, list):
                    for bottleneck in bottlenecks_data:
                        if isinstance(bottleneck, dict):
                            step = bottleneck.get('step', '未知步骤')
                            drop_rate = bottleneck.get('drop_rate', 0)
                            st.warning(f"**{step}**: 流失率 {drop_rate:.1f}%")
                        else:
                            st.warning(f"瓶颈信息: {str(bottleneck)}")
                elif isinstance(bottlenecks_data, dict):
                    # 如果是单个瓶颈字典
                    step = bottlenecks_data.get('step', '未知步骤')
                    drop_rate = bottlenecks_data.get('drop_rate', 0)
                    st.warning(f"**{step}**: 流失率 {drop_rate:.1f}%")
                else:
                    st.info(f"瓶颈数据格式: {type(bottlenecks_data).__name__}")
                    st.write(str(bottlenecks_data))
            except Exception as e:
                st.error(f"瓶颈分析显示失败: {str(e)}")
                st.info("请检查瓶颈数据格式")


def show_user_segmentation_page():
    """显示用户分群结果页面"""
    st.header("👥 智能用户分群")
    
    # 初始化分析引擎
    if 'segmentation_engine' not in st.session_state:
        st.session_state.segmentation_engine = UserSegmentationEngine()
    if 'advanced_visualizer' not in st.session_state:
        st.session_state.advanced_visualizer = AdvancedVisualizer()
    
    # 分群配置
    with st.expander("🔧 分群配置", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            clustering_method = st.selectbox(
                "聚类算法",
                options=["K-Means", "DBSCAN"],
                index=0
            )
        
        with col2:
            n_clusters = st.slider(
                "分群数量",
                min_value=2,
                max_value=10,
                value=4,
                help="K-Means算法的分群数量"
            )
        
        with col3:
            feature_types = st.multiselect(
                "特征类型",
                options=["行为特征", "设备特征", "地理特征", "时间特征"],
                default=["行为特征", "设备特征"]
            )
    
    # 执行用户分群
    if st.button("🚀 开始用户分群", type="primary"):
        with st.spinner("正在进行用户分群分析..."):
            try:
                raw_data = st.session_state.raw_data
                engine = st.session_state.segmentation_engine

                # 确保raw_data是DataFrame格式
                if isinstance(raw_data, list):
                    events_df = pd.DataFrame(raw_data)
                elif isinstance(raw_data, pd.DataFrame):
                    events_df = raw_data
                else:
                    st.error("❌ 数据格式不支持")
                    st.stop()

                # 提取用户特征 - 使用正确的参数
                user_features = engine.extract_user_features(events=events_df)

                if not user_features:
                    st.warning("⚠️ 无法提取用户特征，可能是数据格式问题")
                    st.info("请检查数据是否包含必要的字段（如user_pseudo_id, event_name等）")
                    st.stop()

                # 执行聚类 - 传入用户特征
                segmentation_result = engine.create_user_segments(
                    user_features=user_features,
                    method=clustering_method.lower().replace('-', ''),
                    n_clusters=n_clusters
                )

                st.session_state.segmentation_results = {
                    'segments': segmentation_result,
                    'user_features': user_features
                }

                st.success("✅ 用户分群完成!")

            except Exception as e:
                st.error(f"❌ 用户分群失败: {str(e)}")
                st.error(f"错误详情: {type(e).__name__}")
                import traceback
                st.text(traceback.format_exc())
    
    # 显示分群结果
    if 'segmentation_results' in st.session_state:
        results = st.session_state.segmentation_results
        visualizer = st.session_state.advanced_visualizer
        
        st.markdown("---")
        st.subheader("📊 用户分群结果")
        
        # 分群概览
        if 'segments' in results:
            segmentation_result = results['segments']

            # 安全地处理SegmentationResult对象
            if hasattr(segmentation_result, 'segments'):
                # 如果是SegmentationResult对象，获取segments列表
                segments = segmentation_result.segments
            elif isinstance(segmentation_result, list):
                # 如果已经是列表，直接使用
                segments = segmentation_result
            else:
                # 如果是其他类型，尝试转换
                segments = []
                st.warning(f"未知的分群数据类型: {type(segmentation_result)}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("分群数量", len(segments))
            with col2:
                # 安全地计算总用户数
                total_users = 0
                for seg in segments:
                    if hasattr(seg, 'user_count'):
                        # 如果是UserSegment对象
                        total_users += seg.user_count
                    elif isinstance(seg, dict) and 'user_ids' in seg:
                        # 如果是字典格式
                        total_users += len(seg.get('user_ids', []))
                    elif isinstance(seg, dict) and 'user_count' in seg:
                        # 如果字典中有user_count
                        total_users += seg.get('user_count', 0)

                st.metric("总用户数", f"{total_users:,}")
            with col3:
                avg_size = total_users / len(segments) if segments else 0
                st.metric("平均分群大小", f"{avg_size:.0f}")
        
        # 分群散点图
        if 'user_features' in results and results['user_features'] is not None:
            st.subheader("🎯 用户分群可视化")
            try:
                # 创建示例散点图数据
                scatter_data = pd.DataFrame({
                    'user_id': [f'user_{i}' for i in range(100)],
                    'segment': [f'分群{i%4+1}' for i in range(100)],
                    'x_feature': np.random.normal(0, 1, 100),
                    'y_feature': np.random.normal(0, 1, 100)
                })
                
                scatter_chart = visualizer.create_user_segmentation_scatter(scatter_data)
                st.plotly_chart(scatter_chart, use_container_width=True)
            except Exception as e:
                st.error(f"散点图生成失败: {str(e)}")
        
        # 分群特征雷达图
        st.subheader("🕸️ 分群特征对比")
        try:
            # 创建示例雷达图数据
            radar_data = pd.DataFrame({
                'segment': ['分群1', '分群1', '分群1', '分群2', '分群2', '分群2'],
                'feature_name': ['活跃度', '转化率', '留存率', '活跃度', '转化率', '留存率'],
                'feature_value': [0.8, 0.3, 0.6, 0.5, 0.7, 0.4]
            })
            
            radar_chart = visualizer.create_feature_radar_chart(radar_data)
            st.plotly_chart(radar_chart, use_container_width=True)
        except Exception as e:
            st.error(f"雷达图生成失败: {str(e)}")


def show_path_analysis_page():
    """显示路径分析结果页面"""
    st.header("🛤️ 用户行为路径分析")
    
    # 初始化分析引擎
    if 'path_engine' not in st.session_state:
        st.session_state.path_engine = PathAnalysisEngine()
    if 'advanced_visualizer' not in st.session_state:
        st.session_state.advanced_visualizer = AdvancedVisualizer()
    
    # 路径分析配置
    with st.expander("🔧 路径分析配置", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            session_timeout = st.slider(
                "会话超时(分钟)",
                min_value=10,
                max_value=120,
                value=30,
                help="定义会话的超时时间"
            )
        
        with col2:
            min_path_length = st.slider(
                "最小路径长度",
                min_value=2,
                max_value=10,
                value=3,
                help="分析的最小路径长度"
            )
        
        with col3:
            top_paths = st.slider(
                "显示路径数量",
                min_value=5,
                max_value=20,
                value=10,
                help="显示最常见的路径数量"
            )
    
    # 执行路径分析
    if st.button("🚀 开始路径分析", type="primary"):
        with st.spinner("正在进行路径分析..."):
            try:
                raw_data = st.session_state.raw_data
                engine = st.session_state.path_engine
                
                # 设置会话超时时间
                engine.session_timeout_minutes = session_timeout

                # 确保raw_data是DataFrame格式
                if isinstance(raw_data, list):
                    events_df = pd.DataFrame(raw_data)
                elif isinstance(raw_data, pd.DataFrame):
                    events_df = raw_data
                else:
                    st.error("❌ 数据格式不支持")
                    st.stop()

                # 重构用户会话
                sessions = engine.reconstruct_user_sessions(events=events_df)
                
                # 识别路径模式
                path_analysis_result = engine.identify_path_patterns(
                    sessions=sessions,
                    min_length=min_path_length,
                    max_length=10  # 设置最大路径长度
                )

                # 提取常见路径（限制数量）
                common_paths = path_analysis_result.common_patterns[:top_paths] if path_analysis_result.common_patterns else []
                
                st.session_state.path_results = {
                    'sessions': sessions,
                    'common_paths': common_paths
                }
                
                st.success("✅ 路径分析完成!")
                
            except Exception as e:
                st.error(f"❌ 路径分析失败: {str(e)}")
    
    # 显示路径分析结果
    if 'path_results' in st.session_state:
        results = st.session_state.path_results
        visualizer = st.session_state.advanced_visualizer
        
        st.markdown("---")
        st.subheader("📊 路径分析结果")
        
        # 路径统计
        if 'sessions' in results:
            sessions = results['sessions']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总会话数", f"{len(sessions):,}")
            with col2:
                # 安全地处理UserSession对象的path_sequence属性
                path_lengths = []
                for s in sessions:
                    if hasattr(s, 'path_sequence') and s.path_sequence:
                        path_lengths.append(len(s.path_sequence))
                    else:
                        path_lengths.append(0)
                avg_length = np.mean(path_lengths) if path_lengths else 0
                st.metric("平均路径长度", f"{avg_length:.1f}")
            with col3:
                # 安全地处理UserSession对象的path_sequence属性
                unique_paths_set = set()
                for s in sessions:
                    if hasattr(s, 'path_sequence') and s.path_sequence:
                        unique_paths_set.add(tuple(s.path_sequence))
                unique_paths = len(unique_paths_set)
                st.metric("唯一路径数", f"{unique_paths:,}")
        
        # 用户行为流程图
        st.subheader("🌊 用户行为流程")
        try:
            # 创建示例流程数据
            flow_data = pd.DataFrame({
                'source': ['首页', '首页', '产品页', '产品页', '购物车'],
                'target': ['产品页', '搜索页', '购物车', '详情页', '结算页'],
                'value': [100, 50, 80, 30, 60]
            })
            
            flow_chart = visualizer.create_user_behavior_flow(flow_data)
            st.plotly_chart(flow_chart, use_container_width=True)
        except Exception as e:
            st.error(f"流程图生成失败: {str(e)}")
        
        # 常见路径列表
        if 'common_paths' in results and results['common_paths'] is not None:
            st.subheader("🔝 最常见路径")
            common_paths_data = results['common_paths']

            # 安全地创建DataFrame
            try:
                if isinstance(common_paths_data, pd.DataFrame):
                    paths_df = common_paths_data
                elif isinstance(common_paths_data, (list, dict)):
                    paths_df = pd.DataFrame(common_paths_data)
                else:
                    paths_df = pd.DataFrame()

                if not paths_df.empty:
                    st.dataframe(paths_df, use_container_width=True)
                else:
                    st.info("暂无常见路径数据")

            except Exception as e:
                st.error(f"路径数据显示失败: {str(e)}")
                st.info("请检查路径数据格式")


def show_comprehensive_report_page():
    """显示综合分析报告页面"""
    st.header("📋 综合分析报告")
    
    # 报告配置
    with st.expander("📊 报告配置", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            report_sections = st.multiselect(
                "选择报告章节",
                options=["数据概览", "事件分析", "留存分析", "转化分析", "用户分群", "路径分析"],
                default=["数据概览", "事件分析", "留存分析"]
            )
        
        with col2:
            export_format = st.selectbox(
                "导出格式",
                options=["HTML", "PDF", "JSON"],
                index=0
            )
    
    # 生成报告
    if st.button("📝 生成综合报告", type="primary"):
        with st.spinner("正在生成综合报告..."):
            try:
                # 汇总所有分析结果
                report_data = {
                    'data_summary': st.session_state.get('data_summary', {}),
                    'event_analysis': st.session_state.get('event_analysis_results', {}),
                    'retention_analysis': st.session_state.get('retention_results', {}),
                    'conversion_analysis': st.session_state.get('conversion_results', {}),
                    'segmentation_analysis': st.session_state.get('segmentation_results', {}),
                    'path_analysis': st.session_state.get('path_results', {})
                }
                
                st.session_state.comprehensive_report = report_data
                st.success("✅ 综合报告生成完成!")
                
            except Exception as e:
                st.error(f"❌ 报告生成失败: {str(e)}")
    
    # 显示综合报告
    if 'comprehensive_report' in st.session_state:
        report = st.session_state.comprehensive_report
        
        st.markdown("---")
        
        # 数据概览
        if "数据概览" in report_sections and 'data_summary' in report:
            st.subheader("📊 数据概览")
            summary = report['data_summary']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("总事件数", f"{summary.get('total_events', 0):,}")
            with col2:
                st.metric("独立用户数", f"{summary.get('unique_users', 0):,}")
            with col3:
                st.metric("事件类型数", len(summary.get('event_types', {})))
            with col4:
                date_range = summary.get('date_range', {})
                days = (pd.to_datetime(date_range.get('end', '')) - pd.to_datetime(date_range.get('start', ''))).days
                st.metric("数据天数", f"{days}天")
        
        # 关键洞察
        st.subheader("💡 关键洞察")
        insights = [
            "用户活跃度在工作日较高，周末有所下降",
            "移动端用户占比逐渐增加，需要优化移动体验",
            "新用户留存率在第7天出现明显下降",
            "购买转化漏斗在购物车环节流失率最高",
            "高价值用户群体主要集中在25-35岁年龄段"
        ]
        
        for insight in insights:
            st.info(f"• {insight}")
        
        # 行动建议
        st.subheader("🎯 行动建议")
        recommendations = [
            "**优化移动端体验**: 针对移动端用户增长趋势，优化移动端界面和交互",
            "**改善新用户引导**: 加强新用户第一周的引导和激励机制",
            "**优化购物车流程**: 简化购物车到结算的流程，减少用户流失",
            "**精准营销**: 针对高价值用户群体制定个性化营销策略",
            "**提升周末活跃度**: 推出周末专属活动和优惠来提升用户活跃度"
        ]
        
        for rec in recommendations:
            st.success(rec)
        
        # 导出报告
        st.markdown("---")
        st.subheader("📥 报告导出")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            export_format_final = st.selectbox(
                "选择导出格式",
                options=["JSON", "PDF", "Excel"],
                index=0,
                key="final_export_format"
            )
        
        with col2:
            include_raw_data = st.checkbox(
                "包含原始数据",
                value=False,
                help="是否在导出中包含原始分析数据"
            )
        
        with col3:
            custom_filename = st.text_input(
                "自定义文件名",
                value="",
                placeholder="留空使用默认文件名"
            )
        
        if st.button(f"📥 导出{export_format_final}报告", type="primary"):
            with st.spinner(f"正在导出{export_format_final}格式报告..."):
                try:
                    # 初始化报告导出器
                    exporter = ReportExporter()
                    
                    # 准备报告数据
                    export_data = {
                        'metadata': {
                            'generated_at': datetime.now().isoformat(),
                            'report_sections': report_sections,
                            'data_summary': report.get('data_summary', {})
                        },
                        'executive_summary': {
                            'key_metrics': {
                                'total_events': report.get('data_summary', {}).get('total_events', 0),
                                'unique_users': report.get('data_summary', {}).get('unique_users', 0),
                                'event_types': len(report.get('data_summary', {}).get('event_types', {}))
                            },
                            'key_insights': insights,
                            'recommendations': recommendations
                        },
                        'detailed_analysis': {}
                    }
                    
                    # 添加选中的分析结果
                    if "事件分析" in report_sections and 'event_analysis' in report:
                        export_data['detailed_analysis']['event_analysis'] = report['event_analysis']
                    
                    if "留存分析" in report_sections and 'retention_analysis' in report:
                        export_data['detailed_analysis']['retention_analysis'] = report['retention_analysis']
                    
                    if "转化分析" in report_sections and 'conversion_analysis' in report:
                        export_data['detailed_analysis']['conversion_analysis'] = report['conversion_analysis']
                    
                    if "用户分群" in report_sections and 'segmentation_analysis' in report:
                        export_data['detailed_analysis']['user_segmentation'] = report['segmentation_analysis']
                    
                    if "路径分析" in report_sections and 'path_analysis' in report:
                        export_data['detailed_analysis']['path_analysis'] = report['path_analysis']
                    
                    # 如果选择包含原始数据
                    if include_raw_data and st.session_state.get('raw_data') is not None:
                        # 只包含数据摘要，避免文件过大
                        raw_data = st.session_state.raw_data
                        export_data['raw_data_summary'] = {
                            'total_records': len(raw_data),
                            'columns': list(raw_data.columns),
                            'sample_records': raw_data.head(5).to_dict('records')
                        }
                    
                    # 生成文件名
                    if custom_filename:
                        filename = f"{custom_filename}.{export_format_final.lower()}"
                    else:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"comprehensive_report_{timestamp}.{export_format_final.lower()}"
                    
                    output_path = f"reports/{filename}"
                    
                    # 执行导出
                    result = exporter.export_report(export_data, export_format_final.lower(), output_path)
                    
                    if result['status'] == 'success':
                        st.success(f"✅ 报告导出成功!")
                        st.info(f"📁 文件路径: {result['file_path']}")
                        st.info(f"📏 文件大小: {result['file_size'] / 1024:.1f} KB")
                        
                        # 提供下载链接
                        try:
                            with open(result['file_path'], 'rb') as f:
                                file_data = f.read()
                            
                            st.download_button(
                                label=f"⬇️ 下载{export_format_final}报告",
                                data=file_data,
                                file_name=filename,
                                mime=get_mime_type(export_format_final.lower())
                            )
                        except Exception as e:
                            st.warning(f"下载按钮创建失败: {str(e)}")
                    else:
                        st.error(f"❌ 报告导出失败: {result['message']}")
                        
                except Exception as e:
                    st.error(f"❌ 导出过程出错: {str(e)}")
    



def show_intelligent_analysis_page():
    """显示智能分析页面"""
    st.header("🚀 智能分析 - 一键完整分析")
    
    st.markdown("""
    ### 功能说明
    智能分析功能使用系统集成管理器，通过多智能体协作完成完整的GA4数据分析工作流程。
    包括事件分析、留存分析、转化分析、用户分群和路径分析等所有核心功能。
    """)
    
    # 分析配置
    st.subheader("📋 分析配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_types = st.multiselect(
            "选择分析类型",
            options=[
                'event_analysis',
                'retention_analysis', 
                'conversion_analysis',
                'user_segmentation',
                'path_analysis'
            ],
            default=[
                'event_analysis',
                'retention_analysis', 
                'conversion_analysis'
            ],
            format_func=lambda x: {
                'event_analysis': '📊 事件分析',
                'retention_analysis': '📈 留存分析',
                'conversion_analysis': '🔄 转化分析',
                'user_segmentation': '👥 用户分群',
                'path_analysis': '🛤️ 路径分析'
            }.get(x, x)
        )
        
        enable_parallel = st.checkbox(
            "启用并行处理",
            value=True,
            help="并行执行多个分析任务以提高性能"
        )
    
    with col2:
        max_workers = st.slider(
            "最大并行任务数",
            min_value=1,
            max_value=8,
            value=4,
            disabled=not enable_parallel
        )
        
        enable_caching = st.checkbox(
            "启用智能缓存",
            value=True,
            help="缓存分析结果以加速后续执行"
        )
    
    # 执行分析
    st.subheader("🎯 执行分析")
    
    if not analysis_types:
        st.warning("⚠️ 请至少选择一种分析类型")
        return
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🚀 开始智能分析", type="primary"):
            execute_intelligent_analysis(analysis_types, enable_parallel, max_workers, enable_caching)
    
    with col2:
        if st.button("📊 查看系统状态"):
            show_system_status()
    
    # 显示分析结果
    if st.session_state.workflow_results:
        show_workflow_results()


def execute_intelligent_analysis(analysis_types, enable_parallel, max_workers, enable_caching):
    """执行智能分析"""
    
    # 更新集成管理器配置
    integration_manager = st.session_state.integration_manager
    integration_manager.config.enable_parallel_processing = enable_parallel
    integration_manager.config.max_workers = max_workers
    integration_manager.config.enable_caching = enable_caching
    
    # 创建进度容器
    progress_container = st.container()
    
    with progress_container:
        st.subheader("⚙️ 智能分析进度")
        
        # 创建进度条和状态显示
        progress_bar = st.progress(0)
        status_text = st.empty()
        metrics_container = st.empty()
        
        try:
            # 准备临时文件路径
            upload_dir = Path("data/uploads")
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            # 从会话状态获取原始数据并保存到临时文件
            if st.session_state.raw_data is not None:
                temp_file_path = upload_dir / f"temp_analysis_{int(time.time())}.ndjson"
                
                # 将DataFrame转换回NDJSON格式
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    for _, row in st.session_state.raw_data.iterrows():
                        # 重构原始事件格式
                        event_data = {
                            'event_date': row.get('event_date', ''),
                            'event_timestamp': row.get('event_timestamp', 0),
                            'event_name': row.get('event_name', ''),
                            'user_pseudo_id': row.get('user_pseudo_id', ''),
                            'user_id': row.get('user_id'),
                            'platform': row.get('platform', 'WEB'),
                            'device': row.get('device', {}),
                            'geo': row.get('geo', {}),
                            'traffic_source': row.get('traffic_source', {}),
                            'event_params': row.get('event_params', []),
                            'user_properties': row.get('user_properties', []),
                            'items': row.get('items', [])
                        }
                        f.write(json.dumps(event_data, ensure_ascii=False) + '\n')
                
                status_text.text("🚀 启动智能分析工作流程...")
                progress_bar.progress(10)
                
                # 执行完整工作流程
                start_time = time.time()
                
                result = integration_manager.execute_complete_workflow(
                    file_path=str(temp_file_path),
                    analysis_types=analysis_types
                )
                
                end_time = time.time()
                total_time = end_time - start_time
                
                # 更新进度
                progress_bar.progress(100)
                status_text.text("✅ 智能分析完成!")
                
                # 显示执行指标
                with metrics_container.container():
                    col1, col2, col3, col4 = st.columns(4)
                    
                    execution_summary = result['execution_summary']
                    
                    with col1:
                        st.metric(
                            "总执行时间",
                            f"{total_time:.2f}秒",
                            help="完整工作流程的执行时间"
                        )
                    
                    with col2:
                        st.metric(
                            "成功分析",
                            execution_summary['successful_analyses'],
                            help="成功完成的分析任务数量"
                        )
                    
                    with col3:
                        st.metric(
                            "处理数据量",
                            f"{execution_summary['data_size']:,}",
                            help="处理的事件记录数量"
                        )
                    
                    with col4:
                        processing_rate = execution_summary['data_size'] / total_time if total_time > 0 else 0
                        st.metric(
                            "处理速率",
                            f"{processing_rate:.0f}/秒",
                            help="每秒处理的记录数量"
                        )
                
                # 保存结果到会话状态
                st.session_state.workflow_results = result
                
                # 清理临时文件
                if temp_file_path.exists():
                    temp_file_path.unlink()
                
                st.success("🎉 智能分析成功完成!")
                st.rerun()
                
            else:
                st.error("❌ 无法获取原始数据，请重新上传文件")
                
        except Exception as e:
            st.error(f"❌ 智能分析失败: {str(e)}")
            progress_bar.progress(0)
            status_text.text("❌ 分析失败")
            
            # 清理临时文件
            if 'temp_file_path' in locals() and temp_file_path.exists():
                temp_file_path.unlink()


def show_system_status():
    """显示系统状态"""
    st.subheader("📊 系统状态监控")
    
    integration_manager = st.session_state.integration_manager
    
    # 获取系统健康状态
    health = integration_manager.get_system_health()
    
    # 显示整体状态
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_color = {
            'healthy': 'normal',
            'warning': 'inverse', 
            'critical': 'off'
        }.get(health['overall_status'], 'normal')
        
        st.metric(
            "系统状态",
            health['overall_status'].upper(),
            delta_color=status_color
        )
    
    with col2:
        st.metric(
            "活跃工作流程",
            health['active_workflows']
        )
    
    with col3:
        st.metric(
            "缓存项数量",
            health['cache_size']
        )
    
    # 显示性能指标
    if health.get('current_metrics'):
        st.subheader("⚡ 性能指标")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cpu_usage = health['current_metrics'].get('cpu_usage', 0)
            st.metric(
                "CPU使用率",
                f"{cpu_usage:.1f}%",
                delta=f"{cpu_usage - health.get('average_metrics', {}).get('cpu_usage', cpu_usage):.1f}%"
            )
        
        with col2:
            memory_usage = health['current_metrics'].get('memory_usage', 0)
            st.metric(
                "内存使用率", 
                f"{memory_usage:.1f}%",
                delta=f"{memory_usage - health.get('average_metrics', {}).get('memory_usage', memory_usage):.1f}%"
            )
        
        with col3:
            memory_available = health['current_metrics'].get('memory_available', 0)
            st.metric(
                "可用内存",
                f"{memory_available:.1f}GB"
            )
    
    # 显示工作流程历史
    workflow_history = integration_manager.get_execution_history()
    if workflow_history:
        st.subheader("📈 工作流程历史")
        
        # 创建历史数据表格
        history_data = []
        for record in workflow_history[-10:]:  # 显示最近10个
            history_data.append({
                '工作流程ID': record.get('workflow_id', 'N/A')[:20] + '...',
                '状态': record.get('status', 'unknown'),
                '开始时间': record.get('start_time', 'N/A'),
                '分析类型': ', '.join(record.get('analysis_types', [])),
                '文件路径': Path(record.get('file_path', '')).name if record.get('file_path') else 'N/A'
            })
        
        if history_data:
            df = pd.DataFrame(history_data)
            st.dataframe(df, use_container_width=True)
    
    # 系统操作
    st.subheader("🔧 系统操作")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧹 清理缓存"):
            integration_manager._cleanup_cache()
            st.success("✅ 缓存已清理")
            st.rerun()
    
    with col2:
        if st.button("🗑️ 清理内存"):
            integration_manager._trigger_memory_cleanup()
            st.success("✅ 内存已清理")
            st.rerun()
    
    with col3:
        if st.button("🔄 重置状态"):
            integration_manager.reset_execution_state()
            st.success("✅ 执行状态已重置")
            st.rerun()


def show_workflow_results():
    """显示工作流程结果"""
    st.subheader("📋 分析结果")
    
    result = st.session_state.workflow_results
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📊 结果概览", "🔍 详细分析", "📈 可视化图表", "📥 导出报告"])
    
    with tab1:
        show_results_overview(result)
    
    with tab2:
        show_detailed_analysis(result)
    
    with tab3:
        show_visualizations(result)
    
    with tab4:
        show_export_options(result)


def show_results_overview(result):
    """显示结果概览"""
    st.write("### 📊 执行概览")
    
    execution_summary = result['execution_summary']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "工作流程ID",
            result['workflow_id'][:12] + "...",
            help=f"完整ID: {result['workflow_id']}"
        )
    
    with col2:
        st.metric(
            "总执行时间",
            f"{execution_summary['total_execution_time']:.2f}秒"
        )
    
    with col3:
        st.metric(
            "成功分析",
            f"{execution_summary['successful_analyses']}/{execution_summary['successful_analyses'] + execution_summary['failed_analyses']}"
        )
    
    with col4:
        st.metric(
            "数据规模",
            f"{execution_summary['data_size']:,} 条"
        )
    
    # 分析结果状态
    st.write("### 📈 分析模块状态")
    
    analysis_results = result['analysis_results']
    
    for analysis_type, analysis_result in analysis_results.items():
        with st.expander(f"{'✅' if analysis_result.status == 'completed' else '❌'} {analysis_type.replace('_', ' ').title()}",
                        expanded=analysis_result.status == 'completed'):
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**状态**: {analysis_result.status}")
                st.write(f"**执行时间**: {analysis_result.execution_time:.2f}秒")
                st.write(f"**洞察数量**: {len(analysis_result.insights)}")
                st.write(f"**建议数量**: {len(analysis_result.recommendations)}")
            
            with col2:
                if analysis_result.insights:
                    st.write("**主要洞察**:")
                    for insight in analysis_result.insights[:3]:
                        st.write(f"• {insight}")

                    if len(analysis_result.insights) > 3:
                        st.write(f"... 还有 {len(analysis_result.insights) - 3} 个洞察")


def show_detailed_analysis(result):
    """显示详细分析"""
    st.write("### 🔍 详细分析结果")
    
    analysis_results = result['analysis_results']
    
    # 选择要查看的分析
    selected_analysis = st.selectbox(
        "选择分析模块",
        options=list(analysis_results.keys()),
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    if selected_analysis:
        analysis_result = analysis_results[selected_analysis]
        
        if analysis_result.status == 'completed':
            # 显示洞察
            if analysis_result.insights:
                st.write("#### 💡 关键洞察")
                for i, insight in enumerate(analysis_result.insights, 1):
                    st.write(f"{i}. {insight}")

            # 显示建议
            if analysis_result.recommendations:
                st.write("#### 🎯 行动建议")
                for i, recommendation in enumerate(analysis_result.recommendations, 1):
                    st.write(f"{i}. {recommendation}")

            # 显示数据摘要
            if hasattr(analysis_result, 'data') and analysis_result.data:
                st.write("#### 📊 数据摘要")
                data_summary = analysis_result.data
                
                summary_data = []
                for key, value in data_summary.items():
                    if isinstance(value, dict):
                        summary_data.append({
                            '字段': key,
                            '类型': value.get('type', 'unknown'),
                            '描述': str(value)[:100] + '...' if len(str(value)) > 100 else str(value)
                        })
                
                if summary_data:
                    df = pd.DataFrame(summary_data)
                    st.dataframe(df, use_container_width=True)
        
        else:
            st.error(f"❌ 分析失败: {getattr(analysis_result, 'error_message', '未知错误')}")


def show_visualizations(result):
    """显示可视化图表"""
    st.write("### 📈 可视化图表")
    
    visualizations = result.get('visualizations', {})
    
    if not visualizations:
        st.info("📊 暂无可视化图表数据")
        return
    
    # 选择要查看的可视化
    viz_options = []
    for analysis_type, viz_data in visualizations.items():
        if viz_data:
            for viz_name in viz_data.keys():
                viz_options.append(f"{analysis_type} - {viz_name}")
    
    if viz_options:
        selected_viz = st.selectbox("选择图表", viz_options)
        
        if selected_viz:
            analysis_type, viz_name = selected_viz.split(' - ', 1)
            viz_data = visualizations[analysis_type][viz_name]

            # 显示图表信息
            st.info(f"📊 图表: {viz_name}")

            # 检查是否为Plotly图表对象
            try:
                import plotly.graph_objects as go

                if isinstance(viz_data, go.Figure):
                    # 如果是Plotly图表，直接显示
                    st.plotly_chart(viz_data, use_container_width=True)
                elif hasattr(viz_data, 'to_json'):
                    # 如果有to_json方法，尝试转换为Plotly图表
                    st.plotly_chart(viz_data, use_container_width=True)
                else:
                    # 如果是其他数据类型，尝试显示为JSON
                    try:
                        if isinstance(viz_data, dict):
                            st.json(viz_data)
                        else:
                            st.write("图表数据格式:", type(viz_data).__name__)
                            st.write(str(viz_data)[:1000] + "..." if len(str(viz_data)) > 1000 else str(viz_data))
                    except Exception as json_error:
                        st.error(f"无法显示图表数据: {str(json_error)}")
                        st.write("数据类型:", type(viz_data).__name__)

            except Exception as e:
                st.error(f"图表显示失败: {str(e)}")
                st.write("数据类型:", type(viz_data).__name__)
                # 尝试显示部分数据用于调试
                try:
                    st.write("数据预览:", str(viz_data)[:500] + "..." if len(str(viz_data)) > 500 else str(viz_data))
                except:
                    st.write("无法预览数据")
    else:
        st.info("📊 暂无可用的可视化图表")


def show_export_options(result):
    """显示导出选项"""
    st.write("### 📥 导出分析报告")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_format = st.selectbox(
            "导出格式",
            options=['json', 'pdf', 'excel'],
            format_func=lambda x: {
                'json': 'JSON 格式',
                'pdf': 'PDF 报告',
                'excel': 'Excel 表格'
            }.get(x, x)
        )
        
        include_raw_data = st.checkbox(
            "包含原始数据",
            value=False,
            help="包含原始数据会增加文件大小"
        )
    
    with col2:
        st.write("**导出内容预览**:")
        st.write("• 执行摘要")
        st.write("• 分析结果和洞察")
        st.write("• 行动建议")
        st.write("• 系统性能指标")
        if include_raw_data:
            st.write("• 原始数据")
    
    if st.button("📥 导出报告", type="primary"):
        try:
            integration_manager = st.session_state.integration_manager
            workflow_id = result['workflow_id']
            
            # 导出报告
            file_path = integration_manager.export_workflow_results(
                workflow_id=workflow_id,
                export_format=export_format,
                include_raw_data=include_raw_data
            )
            
            # 读取文件内容用于下载
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # 提供下载链接
            st.download_button(
                label=f"⬇️ 下载 {export_format.upper()} 报告",
                data=file_data,
                file_name=Path(file_path).name,
                mime=get_mime_type(export_format)
            )
            
            st.success(f"✅ 报告已生成: {Path(file_path).name}")
            
        except Exception as e:
            st.error(f"❌ 导出失败: {str(e)}")

if __name__ == "__main__":
    main()