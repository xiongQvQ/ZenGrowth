"""
数据上传页面组件
处理GA4数据文件的上传、验证和处理
"""

import streamlit as st
import pandas as pd
import json
import time
from pathlib import Path
from typing import Optional

from config.settings import settings
from tools.ga4_data_parser import GA4DataParser
from tools.data_validator import DataValidator
from utils.i18n import t
from utils.cached_components import get_cached_ga4_parser, get_cached_data_validator


class DataUploadPage:
    """数据上传页面类"""
    
    def __init__(self):
        self.parser = get_cached_ga4_parser()
        self.validator = get_cached_data_validator()
    
    def render(self):
        """渲染数据上传页面"""
        from ui.state import get_state_manager
        
        st.header(t("data_upload.title"))
        
        # 文件上传说明
        self._render_instructions()
        
        # 文件上传区域
        self._render_file_upload()
        
        # 显示处理结果
        state_manager = get_state_manager()
        if state_manager.is_data_loaded():
            self._render_processing_results()
    
    def _render_instructions(self):
        """渲染使用说明"""
        with st.expander(t("data_upload.usage_instructions"), expanded=False):
            st.markdown(t("data_upload.supported_file_formats_title"))
            st.markdown(t("data_upload.ga4_ndjson_format"))
            st.markdown(t("data_upload.file_size_limit_desc").format(max_size=settings.max_file_size_mb))
            
            st.markdown(t("data_upload.data_requirements_title"))
            st.markdown(t("data_upload.data_structure_requirement"))
            st.markdown(t("data_upload.supported_event_types"))
            st.markdown(t("data_upload.required_fields"))
            
            st.markdown(t("data_upload.processing_flow_title"))
            st.markdown(t("data_upload.processing_step_1"))
            st.markdown(t("data_upload.processing_step_2"))
            st.markdown(t("data_upload.processing_step_3"))
            st.markdown(t("data_upload.processing_step_4"))
    
    def _render_file_upload(self):
        """渲染文件上传区域"""
        st.subheader(t("data_upload.file_upload"))
        
        uploaded_file = st.file_uploader(
            t("data_upload.upload_ga4_file"),
            type=['ndjson', 'json', 'jsonl'],
            help=f"{t('data_upload.supported_formats')} (最大{settings.max_file_size_mb}MB)"
        )
        
        if uploaded_file is not None:
            self._handle_uploaded_file(uploaded_file)
    
    def _handle_uploaded_file(self, uploaded_file):
        """处理上传的文件"""
        # 检查文件大小
        file_size_mb = uploaded_file.size / (1024 * 1024)
        
        if file_size_mb > settings.max_file_size_mb:
            st.error(t("data_upload.file_size_exceeded").format(
                size=f"{file_size_mb:.1f}", 
                limit=settings.max_file_size_mb
            ))
            return
        
        # 显示文件信息
        st.info(f"{t('data_upload.file_name')}: {uploaded_file.name}")
        st.info(f"{t('data_upload.file_size')}: {file_size_mb:.2f}MB")
        
        # 处理按钮
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button(t("data_upload.start_processing"), type="primary"):
                self._process_file(uploaded_file)
        
        with col2:
            if st.button(t("data_upload.preview_file")):
                self._preview_file(uploaded_file)
    
    def _preview_file(self, uploaded_file):
        """预览上传的文件"""
        st.subheader(t("data_upload.file_preview"))
        
        try:
            # 读取前几行进行预览
            content = uploaded_file.read().decode('utf-8')
            lines = content.split('\n')[:5]  # 只显示前5行
            
            st.write(f"**{t('data_upload.file_lines')}**: ~{len(content.split())}")
            st.write(f"**{t('data_upload.first_lines')}**:")
            
            for i, line in enumerate(lines, 1):
                if line.strip():
                    try:
                        # 尝试解析JSON并格式化显示
                        json_data = json.loads(line)
                        st.code(f"{t('data_upload.line_number').format(number=i)}: {json.dumps(json_data, indent=2, ensure_ascii=False)[:500]}...")
                    except json.JSONDecodeError:
                        st.code(f"{t('data_upload.line_number').format(number=i)}: {line[:500]}...")
            
            # 重置文件指针
            uploaded_file.seek(0)
            
        except Exception as e:
            st.error(f"{t('data_upload.file_preview_failed')}: {str(e)}")
    
    def _process_file(self, uploaded_file):
        """处理上传的文件"""
        progress_container = st.container()
        
        with progress_container:
            st.subheader(t("data_upload.processing_progress"))
            
            # 创建进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: Save file
                status_text.text(t("data_upload.step_saving_file"))
                progress_bar.progress(10)
                
                file_path = self._save_uploaded_file(uploaded_file)
                
                # Step 2: Parse data
                status_text.text(t("data_upload.step_parsing_data"))
                progress_bar.progress(30)
                
                raw_data = self.parser.parse_ndjson(str(file_path))
                
                # Step 3: Data validation
                status_text.text(t("data_upload.step_validating_data"))
                progress_bar.progress(50)
                
                validation_report = self.validator.validate_dataframe(raw_data)
                
                # Step 4: Data processing
                status_text.text(t("data_upload.step_processing_data"))
                progress_bar.progress(70)
                
                processed_data = self._process_data(raw_data)
                
                # Step 5: Store data
                status_text.text(t("data_upload.step_storing_data"))
                progress_bar.progress(90)
                
                self._store_data(raw_data, processed_data, validation_report)
                
                # Complete
                status_text.text(t("data_upload.step_completed"))
                progress_bar.progress(100)
                
                st.success(t("data_upload.processing_success"))
                
                # 清理临时文件
                if file_path.exists():
                    file_path.unlink()
                
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"{t('data_upload.processing_failed')}: {str(e)}")
                progress_bar.progress(0)
                status_text.text(t("data_upload.step_failed"))
                
                # 清理临时文件
                if 'file_path' in locals() and file_path.exists():
                    file_path.unlink()
    
    def _save_uploaded_file(self, uploaded_file) -> Path:
        """保存上传的文件"""
        # 确保上传目录存在
        upload_dir = Path("data/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存上传的文件
        file_path = upload_dir / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return file_path
    
    def _process_data(self, raw_data):
        """处理数据"""
        # 提取事件数据
        events_data = self.parser.extract_events(raw_data)
        user_data = self.parser.extract_user_properties(raw_data)
        session_data = self.parser.extract_sessions(raw_data)
        
        # 处理事件数据 - 如果是字典，合并所有事件类型
        if isinstance(events_data, dict):
            # 合并所有事件类型的数据
            all_events_list = []
            for event_type, event_df in events_data.items():
                if not event_df.empty:
                    all_events_list.append(event_df)
            
            if all_events_list:
                combined_events = pd.concat(all_events_list, ignore_index=True)
                st.success(t("data_upload.merged_events").format(
                    types=len(events_data), 
                    events=len(combined_events)
                ))
            else:
                combined_events = pd.DataFrame()
                st.warning(t("data_upload.no_valid_events"))
        else:
            combined_events = events_data
        
        return {
            'events': combined_events,
            'users': user_data,
            'sessions': session_data
        }
    
    def _store_data(self, raw_data, processed_data, validation_report):
        """存储数据到会话状态和存储管理器"""
        from ui.state import get_state_manager
        
        # 获取状态管理器
        state_manager = get_state_manager()
        
        # 通过状态管理器正确设置数据状态
        state_manager.set_data_loaded(True, raw_data)
        state_manager.set_processed_data(processed_data)
        
        # 存储到数据管理器
        if hasattr(st.session_state, 'storage_manager'):
            storage_manager = st.session_state.storage_manager
            storage_manager.store_events(processed_data['events'])
            storage_manager.store_users(processed_data['users'])
            storage_manager.store_sessions(processed_data['sessions'])
            
            # 刷新集成管理器的存储管理器
            if 'integration_manager' in st.session_state:
                st.session_state.integration_manager.refresh_storage_manager(storage_manager)
        
        # 生成数据摘要并通过状态管理器存储
        data_summary = self.parser.validate_data_quality(raw_data)
        state_manager.update_data_summary(data_summary)
        st.session_state.validation_report = validation_report
    
    def _render_processing_results(self):
        """显示处理结果"""
        from ui.state import get_state_manager
        state_manager = get_state_manager()
        
        st.markdown("---")
        st.subheader(t("data_upload.processing_results"))
        
        data_summary = state_manager.get_data_summary()
        if data_summary:
            self._render_data_summary()
        
        # 验证报告
        if st.session_state.validation_report:
            self._render_validation_report()
    
    def _render_data_summary(self):
        """渲染数据摘要"""
        from ui.state import get_state_manager
        state_manager = get_state_manager()
        summary = state_manager.get_data_summary()
        
        # 基础统计
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                t("metrics.total_events"),
                f"{summary.get('total_events', 0):,}",
                help=t("metrics.total_events_help")
            )
        
        with col2:
            st.metric(
                t("metrics.unique_users"),
                f"{summary.get('unique_users', 0):,}",
                help=t("metrics.unique_users_help")
            )
        
        with col3:
            date_range = summary.get('date_range', {})
            days = (pd.to_datetime(date_range.get('end', '')) - pd.to_datetime(date_range.get('start', ''))).days
            st.metric(
                t("metrics.data_days"),
                f"{days}{t('common.day')}",
                help=t("metrics.time_range_help")
            )
        
        with col4:
            st.metric(
                t("metrics.event_types_data"),
                len(summary.get('event_types', {})),
                help=t("metrics.event_types_help")
            )
        
        # 详细信息
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**📅 {t('metrics.time_range_data')}**")
            date_range = summary.get('date_range', {})
            st.write(f"- {t('metrics.start_time')}: {date_range.get('start', 'N/A')}")
            st.write(f"- {t('metrics.end_time')}: {date_range.get('end', 'N/A')}")
            
            st.write(f"**🎯 {t('metrics.event_types_data')}**")
            event_types = summary.get('event_types', {})
            for event_type, count in list(event_types.items())[:10]:  # 显示前10个
                st.write(f"- {event_type}: {count:,}")
            if len(event_types) > 10:
                st.write(f"- ... 还有 {len(event_types) - 10} 种事件类型")
        
        with col2:
            st.write(f"**📱 {t('metrics.platform_distribution')}**")
            platforms = summary.get('platforms', {})
            for platform, count in platforms.items():
                st.write(f"- {platform}: {count:,}")
            
            # 数据质量问题
            if summary.get('data_issues'):
                st.write(f"**{t('metrics.data_quality_issues')}**")
                for issue in summary.get('data_issues', []):
                    st.warning(f"- {issue}")
    
    def _render_validation_report(self):
        """渲染验证报告"""
        with st.expander("🔍 详细验证报告", expanded=False):
            validation_report = st.session_state.validation_report
            
            if validation_report.get('validation_passed'):
                st.success(t("metrics.data_validation_passed"))
            else:
                st.error(t("metrics.data_validation_failed"))
            
            # 错误信息
            if validation_report.get('errors'):
                st.write(f"**{t('metrics.error_messages')}**")
                for error in validation_report['errors']:
                    st.error(f"- {error}")
            
            # 警告信息
            if validation_report.get('warnings'):
                st.write(f"**{t('metrics.warning_messages')}**")
                for warning in validation_report['warnings']:
                    st.warning(f"- {warning}")
            
            # 统计信息
            stats = validation_report.get('statistics', {})
            if stats:
                st.write(f"**{t('metrics.statistics')}**")
                st.json(stats)


def show_data_upload_page():
    """数据上传页面入口函数 - 保持向后兼容"""
    page = DataUploadPage()
    page.render()