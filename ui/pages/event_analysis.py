"""
事件分析页面组件
处理用户事件数据的分析和可视化
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from engines.event_analysis_engine import EventAnalysisEngine
from visualization.chart_generator import ChartGenerator
from utils.i18n import t
from ui.components.common import render_no_data_warning


# 时间粒度映射（与main.py保持一致）
TIME_GRANULARITY_MAPPING = {
    "日": "daily",
    "周": "weekly", 
    "月": "monthly",
    "Daily": "daily",
    "Weekly": "weekly",
    "Monthly": "monthly",
    "day": "daily",
    "week": "weekly",
    "month": "monthly"
}


def translate_time_granularity(chinese_term: str) -> str:
    """将中文时间粒度转换为英文"""
    return TIME_GRANULARITY_MAPPING.get(chinese_term, chinese_term)


class EventAnalysisPage:
    """事件分析页面类"""
    
    def __init__(self):
        self._initialize_engines()
    
    def _initialize_engines(self):
        """初始化分析引擎和可视化组件"""
        if 'event_engine' not in st.session_state:
            st.session_state.event_engine = EventAnalysisEngine()
        if 'chart_generator' not in st.session_state:
            st.session_state.chart_generator = ChartGenerator()
    
    def render(self):
        """渲染事件分析页面"""
        from ui.state import get_state_manager
        
        # 检查数据状态
        state_manager = get_state_manager()
        if not state_manager.is_data_loaded():
            render_no_data_warning()
            return
        
        st.header(t('analysis.event_title'))
        
        # 分析控制面板
        config = self._render_analysis_config()
        
        # 执行分析按钮
        if st.button(t('analysis.start_event_analysis'), type="primary"):
            self._execute_analysis(config)
        
        # 显示分析结果
        if 'event_analysis_results' in st.session_state:
            self._render_analysis_results()
    
    def _render_analysis_config(self) -> Dict[str, Any]:
        """渲染分析配置面板"""
        from ui.state import get_state_manager
        
        with st.expander(t('analysis.analysis_config_expander'), expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                date_range = st.date_input(
                    t('analysis.time_range_label'),
                    value=(datetime.now() - timedelta(days=30), datetime.now()),
                    help=t('analysis.time_range_help')
                )
            
            with col2:
                state_manager = get_state_manager()
                data_summary = state_manager.get_data_summary()
                event_types = list(data_summary.get('event_types', {}).keys()) if data_summary else []
                event_filter = st.multiselect(
                    t('analysis.event_filter_label'),
                    options=event_types,
                    default=event_types[:5] if event_types else [],
                    help=t('analysis.event_filter_help')
                )
            
            with col3:
                analysis_granularity = st.selectbox(
                    t('analysis.analysis_granularity_label'),
                    options=[t('analysis.daily'), t('analysis.weekly'), t('analysis.monthly')],
                    index=0,
                    help=t('analysis.analysis_granularity_help')
                )
        
        return {
            'date_range': date_range,
            'event_filter': event_filter,
            'analysis_granularity': analysis_granularity
        }
    
    def _execute_analysis(self, config: Dict[str, Any]):
        """执行事件分析"""
        from ui.state import get_state_manager
        
        with st.spinner(t('analysis.event_analysis_processing')):
            try:
                # 获取数据
                state_manager = get_state_manager()
                raw_data = state_manager.get_raw_data()
                
                # 应用筛选条件
                filtered_data = self._filter_data(raw_data, config)
                
                # 执行分析
                engine = st.session_state.event_engine
                
                # 事件频次分析
                frequency_results = engine.analyze_event_frequency(filtered_data)
                
                # 事件趋势分析 - 转换中文粒度为英文
                english_granularity = translate_time_granularity(config['analysis_granularity'])
                trend_results = engine.analyze_event_trends(filtered_data, time_granularity=english_granularity)
                
                # 存储分析结果
                st.session_state.event_analysis_results = {
                    'frequency': frequency_results,
                    'trends': trend_results,
                    'filtered_data': filtered_data,
                    'config': config
                }
                
                st.success(t('analysis.event_analysis_complete'))
                
            except Exception as e:
                st.error(f"{t('analysis.analysis_failed')}: {str(e)}")
    
    def _filter_data(self, raw_data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """根据配置筛选数据"""
        filtered_data = raw_data.copy()
        
        # 事件类型筛选
        if config['event_filter']:
            filtered_data = filtered_data[filtered_data['event_name'].isin(config['event_filter'])]
        
        # 时间范围筛选（如需要）
        # 这里可以添加时间范围筛选逻辑
        
        return filtered_data
    
    def _render_analysis_results(self):
        """渲染分析结果"""
        if 'event_analysis_results' not in st.session_state:
            st.warning("没有找到分析结果，请先执行事件分析")
            return
            
        results = st.session_state.event_analysis_results
        chart_gen = st.session_state.chart_generator
        
        # 验证results结构
        if not isinstance(results, dict):
            st.error("分析结果格式错误，请重新执行分析")
            return
        
        st.markdown("---")
        st.subheader(t('analysis.analysis_results_header'))
        
        # 关键指标概览
        self._render_key_metrics(results)
        
        # 事件时间线图表
        self._render_timeline_chart(results, chart_gen)
        
        # 事件频次分布和用户活跃度分布
        self._render_distribution_charts(results)
        
        # 详细数据表
        self._render_detailed_data(results)
    
    def _render_key_metrics(self, results: Dict[str, Any]):
        """渲染关键指标"""
        col1, col2, col3, col4 = st.columns(4)
        
        # 防御性检查，确保filtered_data存在
        if 'filtered_data' not in results:
            st.error("分析结果中缺少过滤数据，请重新执行分析")
            return
            
        filtered_data = results['filtered_data']
        
        with col1:
            total_events = len(filtered_data)
            st.metric(t('analysis.total_events'), f"{total_events:,}")
        
        with col2:
            unique_users = filtered_data['user_pseudo_id'].nunique()
            st.metric(t('analysis.active_users'), f"{unique_users:,}")
        
        with col3:
            avg_events_per_user = total_events / unique_users if unique_users > 0 else 0
            st.metric(t('analysis.avg_events_per_user'), f"{avg_events_per_user:.1f}")
        
        with col4:
            event_types = filtered_data['event_name'].nunique()
            st.metric(t('analysis.event_types_count'), f"{event_types}")
    
    def _render_timeline_chart(self, results: Dict[str, Any], chart_gen: ChartGenerator):
        """渲染时间线图表"""
        st.subheader(t('analysis.event_timeline'))
        
        # 防御性检查，确保filtered_data存在
        if 'filtered_data' not in results:
            st.error("分析结果中缺少过滤数据，无法生成时间线图表")
            return
            
        try:
            timeline_chart = chart_gen.create_event_timeline(results['filtered_data'])
            st.plotly_chart(timeline_chart, use_container_width=True)
        except Exception as e:
            st.error(f"{t('analysis.timeline_chart_failed')}: {str(e)}")
    
    def _render_distribution_charts(self, results: Dict[str, Any]):
        """渲染分布图表"""
        col1, col2 = st.columns(2)
        
        # 防御性检查，确保filtered_data存在
        if 'filtered_data' not in results:
            st.error("分析结果中缺少过滤数据，无法生成分布图表")
            return
            
        filtered_data = results['filtered_data']
        
        with col1:
            st.subheader(t('analysis.event_frequency_distribution'))
            event_counts = filtered_data['event_name'].value_counts()
            st.bar_chart(event_counts)
        
        with col2:
            st.subheader(t('analysis.user_activity_distribution'))
            self._render_user_activity_histogram(filtered_data)
    
    def _render_user_activity_histogram(self, filtered_data: pd.DataFrame):
        """渲染用户活跃度直方图"""
        user_activity = filtered_data.groupby('user_pseudo_id').size()
        
        # 创建用户活跃度分布直方图
        activity_df = pd.DataFrame({
            'user_id': user_activity.index,
            'event_count': user_activity.values
        })
        
        fig = px.histogram(
            activity_df,
            x='event_count',
            nbins=20,
            title=t('analysis.user_event_count_distribution'),
            labels={'event_count': t('analysis.event_count'), 'count': t('analysis.user_count')}
        )
        fig.update_layout(
            xaxis_title=t('analysis.event_count'),
            yaxis_title=t('analysis.user_count'),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_detailed_data(self, results: Dict[str, Any]):
        """渲染详细数据表"""
        with st.expander(t('analysis.detailed_data'), expanded=False):
            # 防御性检查，确保filtered_data存在
            if 'filtered_data' not in results:
                st.error("分析结果中缺少过滤数据，无法显示详细数据表")
                return
                
            filtered_data = results['filtered_data']
            display_columns = ['event_date', 'event_name', 'user_pseudo_id', 'platform']
            
            # 确保列存在
            available_columns = [col for col in display_columns if col in filtered_data.columns]
            
            st.dataframe(
                filtered_data[available_columns].head(1000),
                use_container_width=True
            )


def show_event_analysis_page():
    """事件分析页面入口函数 - 保持向后兼容"""
    page = EventAnalysisPage()
    page.render()