"""
路径分析页面
分析用户行为路径和流转
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import numpy as np

from engines.path_analysis_engine import PathAnalysisEngine
from visualization.chart_generator import ChartGenerator
from visualization.advanced_visualizer import AdvancedVisualizer
from utils.i18n import t
from ui.components.common import render_no_data_warning, render_data_status_check

class PathAnalysisPage:
    """路径分析页面类"""
    
    def __init__(self):
        self._initialize_engines()
    
    def _initialize_engines(self):
        """初始化分析引擎和可视化组件"""
        if 'path_engine' not in st.session_state:
            st.session_state.path_engine = PathAnalysisEngine()
        if 'chart_generator' not in st.session_state:
            st.session_state.chart_generator = ChartGenerator()
        if 'advanced_visualizer' not in st.session_state:
            st.session_state.advanced_visualizer = AdvancedVisualizer()
    
    def render(self):
        """渲染路径分析页面"""
        from ui.state import get_state_manager
        
        # 检查数据状态
        state_manager = get_state_manager()
        if not state_manager.is_data_loaded():
            render_no_data_warning()
            return
        
        st.header("🛤️ " + t("pages.path_analysis.title", "路径分析"))
        st.markdown("---")
        
        # 分析配置面板
        config = self._render_analysis_config()
        
        # 执行分析按钮
        if st.button(t('analysis.start_path_analysis', '开始路径分析'), type="primary"):
            self._execute_path_analysis(config)
        
        # 显示分析结果
        if 'path_analysis_results' in st.session_state:
            self._render_analysis_results()
    
    def _render_analysis_config(self) -> Dict[str, Any]:
        """渲染分析配置面板"""
        with st.expander(t('analysis.path_config', '路径分析配置'), expanded=False):
            
            # 基础配置
            col1, col2, col3 = st.columns(3)
            
            with col1:
                date_range = st.date_input(
                    t('analysis.time_range_label', '时间范围'),
                    value=(datetime.now() - timedelta(days=30), datetime.now()),
                    help=t('analysis.time_range_help', '选择分析的时间范围')
                )
            
            with col2:
                analysis_type = st.selectbox(
                    t('analysis.path_analysis_type', '分析类型'),
                    options=[
                        t('analysis.session_reconstruction', '会话重构'),
                        t('analysis.pattern_mining', '模式挖掘'),
                        t('analysis.flow_analysis', '流程分析'),
                        t('analysis.comprehensive_path', '综合路径分析')
                    ],
                    index=3,
                    help=t('analysis.path_type_help', '选择路径分析的类型')
                )
            
            with col3:
                session_timeout = st.slider(
                    t('analysis.session_timeout', '会话超时(分钟)'),
                    min_value=5,
                    max_value=120,
                    value=30,
                    help=t('analysis.session_timeout_help', '会话间隔超过此时间视为新会话')
                )
            
            # 高级配置
            with st.expander(t('analysis.advanced_config', '高级配置'), expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    min_path_length = st.slider(
                        t('analysis.min_path_length', '最小路径长度'),
                        min_value=1,
                        max_value=20,
                        value=2,
                        help=t('analysis.min_path_help', '分析的最小路径步数')
                    )
                    
                    max_path_length = st.slider(
                        t('analysis.max_path_length', '最大路径长度'),
                        min_value=3,
                        max_value=50,
                        value=15,
                        help=t('analysis.max_path_help', '分析的最大路径步数')
                    )
                
                with col2:
                    min_pattern_frequency = st.slider(
                        t('analysis.min_pattern_freq', '最小模式频次'),
                        min_value=1,
                        max_value=100,
                        value=5,
                        help=t('analysis.pattern_freq_help', '模式出现的最小次数')
                    )
                    
                    include_anomalies = st.checkbox(
                        t('analysis.include_anomalies', '包含异常路径'),
                        value=True,
                        help=t('analysis.anomalies_help', '识别和分析异常用户路径')
                    )
            
            # 特定路径分析配置
            specific_paths = []
            if analysis_type in [t('analysis.flow_analysis', '流程分析'), t('analysis.comprehensive_path', '综合路径分析')]:
                st.subheader(t('analysis.specific_path_config', '特定路径配置'))
                
                # 获取可用事件类型
                from ui.state import get_state_manager
                state_manager = get_state_manager()
                data_summary = state_manager.get_data_summary()
                event_types = list(data_summary.get('event_types', {}).keys()) if data_summary else []
                
                if event_types:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        start_events = st.multiselect(
                            t('analysis.start_events', '起始事件'),
                            options=event_types,
                            default=[],
                            help=t('analysis.start_events_help', '选择路径分析的起始事件')
                        )
                    
                    with col2:
                        end_events = st.multiselect(
                            t('analysis.end_events', '结束事件'),
                            options=event_types,
                            default=[],
                            help=t('analysis.end_events_help', '选择路径分析的结束事件')
                        )
                    
                    specific_paths = start_events + end_events
                else:
                    st.warning(t('analysis.no_event_types', '暂无可用的事件类型'))
        
        return {
            'date_range': date_range,
            'analysis_type': analysis_type,
            'session_timeout': session_timeout,
            'min_path_length': min_path_length,
            'max_path_length': max_path_length,
            'min_pattern_frequency': min_pattern_frequency,
            'include_anomalies': include_anomalies,
            'specific_paths': specific_paths
        }
    
    def _execute_path_analysis(self, config: Dict[str, Any]):
        """执行路径分析"""
        from ui.state import get_state_manager
        
        with st.spinner(t('analysis.path_processing', '正在执行路径分析...')):
            try:
                # 获取数据
                state_manager = get_state_manager()
                raw_data = state_manager.get_raw_data()
                
                if raw_data.empty:
                    st.error(t('analysis.no_data', '没有可用的数据进行分析'))
                    return
                
                # 初始化引擎
                engine = st.session_state.path_engine
                engine.session_timeout_minutes = config.get('session_timeout', 30)
                engine.min_pattern_frequency = config.get('min_pattern_frequency', 5)
                
                # 应用时间筛选
                filtered_data = self._filter_data_by_time(raw_data, config['date_range'])
                
                # 执行路径分析
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 步骤1: 会话重构
                status_text.text(t('analysis.step_session_reconstruction', '重构用户会话...'))
                progress_bar.progress(20)
                
                sessions = engine.reconstruct_user_sessions(filtered_data)
                
                # 步骤2: 路径模式识别
                status_text.text(t('analysis.step_pattern_identification', '识别路径模式...'))
                progress_bar.progress(50)
                
                path_patterns = engine.identify_path_patterns(sessions)
                
                # 步骤3: 路径挖掘
                status_text.text(t('analysis.step_path_mining', '挖掘用户路径...'))
                progress_bar.progress(70)
                
                mined_paths = engine.mine_user_paths(
                    filtered_data, 
                    min_length=config.get('min_path_length', 2),
                    max_length=config.get('max_path_length', 15)
                )
                
                # 步骤4: 生成洞察
                status_text.text(t('analysis.step_generating_insights', '生成分析洞察...'))
                progress_bar.progress(90)
                
                insights = self._generate_path_insights(sessions, path_patterns, mined_paths)
                
                # 完成分析
                status_text.text(t('analysis.step_completed', '分析完成'))
                progress_bar.progress(100)
                
                # 存储分析结果
                results = {
                    'sessions': sessions,
                    'path_patterns': path_patterns,
                    'mined_paths': mined_paths,
                    'insights': insights,
                    'config': config,
                    'data_size': len(filtered_data),
                    'analysis_time': datetime.now().isoformat()
                }
                
                # 使用StateManager存储结果
                state_manager.set_analysis_results('path', results)
                st.session_state.path_analysis_results = results
                
                st.success(t('analysis.path_complete', '✅ 路径分析完成!'))
                
            except Exception as e:
                st.error(f"{t('analysis.analysis_failed', '路径分析失败')}: {str(e)}")
                import traceback
                st.text(t('common.detailed_error', 'Detailed error information:'))
                st.text(traceback.format_exc())
    
    def _filter_data_by_time(self, data: pd.DataFrame, date_range) -> pd.DataFrame:
        """根据时间范围筛选数据"""
        try:
            if not hasattr(date_range, '__len__') or len(date_range) != 2:
                return data
            
            start_date, end_date = date_range
            
            # 确保有时间列
            if 'event_datetime' not in data.columns:
                if 'event_timestamp' in data.columns:
                    data['event_datetime'] = pd.to_datetime(data['event_timestamp'], unit='us')
                else:
                    return data
            
            # 筛选时间范围
            filtered_data = data[
                (data['event_datetime'].dt.date >= start_date) &
                (data['event_datetime'].dt.date <= end_date)
            ].copy()
            
            return filtered_data
            
        except Exception as e:
            st.warning(f"{t('common.filter_failed', 'Filter failed')}: {e}")
            return data
    
    def _generate_path_insights(self, sessions, path_patterns, mined_paths):
        """生成路径分析洞察"""
        insights = {
            'basic_stats': {},
            'pattern_insights': [],
            'flow_insights': [],
            'recommendations': []
        }
        
        # 基本统计
        if sessions:
            total_sessions = len(sessions)
            avg_path_length = np.mean([len(s.path_sequence) for s in sessions])
            max_path_length = max([len(s.path_sequence) for s in sessions])
            
            # 处理 PathAnalysisResult 对象
            total_patterns = 0
            if path_patterns and hasattr(path_patterns, 'common_patterns'):
                total_patterns = (
                    len(path_patterns.common_patterns) + 
                    len(path_patterns.anomalous_patterns) + 
                    len(path_patterns.conversion_paths) + 
                    len(path_patterns.exit_patterns)
                )
            
            insights['basic_stats'] = {
                'total_sessions': total_sessions,
                'avg_path_length': avg_path_length,
                'max_path_length': max_path_length,
                'total_patterns': total_patterns
            }
        
        # 模式洞察
        if path_patterns and hasattr(path_patterns, 'common_patterns'):
            common_patterns = path_patterns.common_patterns
            conversion_patterns = path_patterns.conversion_paths
            
            if common_patterns:
                top_pattern = max(common_patterns, key=lambda x: x.frequency)
                insights['pattern_insights'].append(f"{t('analysis.most_common_path', 'Most common path')}: {' → '.join(top_pattern.path_sequence)}")
                insights['pattern_insights'].append(f"{t('analysis.frequency', 'Frequency')}: {top_pattern.frequency} {t('common.times', 'times')}")
            
            if conversion_patterns:
                insights['pattern_insights'].append(f"{t('analysis.found_conversion_patterns', 'Found {count} conversion path patterns').format(count=len(conversion_patterns))}")
        
        # 推荐
        insights['recommendations'] = [
            t('analysis.recommendation_optimize_paths', 'Optimize the most common user paths to improve user experience'),
            t('analysis.recommendation_analyze_anomalies', 'Analyze anomalous path patterns to discover potential user confusion points'),
            t('analysis.recommendation_focus_conversion', 'Focus on conversion path patterns to improve conversion efficiency')
        ]
        
        return insights
    
    def _render_analysis_results(self):
        """渲染分析结果"""
        results = st.session_state.path_analysis_results
        
        if not results:
            st.warning(t('analysis.no_results', '没有分析结果可显示'))
            return
        
        st.markdown("---")
        st.subheader("🛤️ " + t('analysis.path_results', '路径分析结果'))
        
        # 创建标签页
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 " + t('analysis.overview', '概览'),
            "🗺️ " + t('analysis.path_patterns', '路径模式'),
            "📈 " + t('analysis.visualizations', '可视化'),
            "🔍 " + t('analysis.sessions', '会话详情'),
            "💡 " + t('analysis.insights', '洞察与建议')
        ])
        
        with tab1:
            self._render_overview(results)
        
        with tab2:
            self._render_path_patterns(results)
        
        with tab3:
            self._render_visualizations(results)
        
        with tab4:
            self._render_session_details(results)
        
        with tab5:
            self._render_insights_and_recommendations(results)
    
    def _render_overview(self, results: Dict[str, Any]):
        """渲染概览标签页"""
        st.subheader("📊 " + t('analysis.key_metrics', '关键指标'))
        
        sessions = results.get('sessions', [])
        path_patterns = results.get('path_patterns', [])
        insights = results.get('insights', {})
        
        if not sessions:
            st.info(t('analysis.no_session_data', '暂无会话数据'))
            return
        
        # 关键指标
        col1, col2, col3, col4 = st.columns(4)
        
        basic_stats = insights.get('basic_stats', {})
        
        with col1:
            st.metric(
                t('analysis.total_sessions', '总会话数'),
                f"{basic_stats.get('total_sessions', 0):,}",
                help=t('analysis.sessions_help', '分析的用户会话总数')
            )
        
        with col2:
            st.metric(
                t('analysis.avg_path_length', '平均路径长度'),
                f"{basic_stats.get('avg_path_length', 0):.1f}",
                help=t('analysis.path_length_help', '用户路径的平均步数')
            )
        
        with col3:
            st.metric(
                t('analysis.max_path_length', '最大路径长度'),
                f"{basic_stats.get('max_path_length', 0)}",
                help=t('analysis.max_path_help', '用户路径的最大步数')
            )
        
        with col4:
            st.metric(
                t('analysis.total_patterns', '识别模式数'),
                f"{basic_stats.get('total_patterns', 0)}",
                help=t('analysis.patterns_help', '识别的路径模式总数')
            )
        
        # 路径长度分布
        st.subheader("📏 " + t('analysis.path_length_distribution', '路径长度分布'))
        
        path_lengths = [len(s.path_sequence) for s in sessions if hasattr(s, 'path_sequence') and s.path_sequence]
        
        if path_lengths:
            fig = px.histogram(
                x=path_lengths,
                nbins=min(20, max(path_lengths)),
                title=t('analysis.path_length_hist', '用户路径长度分布'),
                labels={'x': t('analysis.path_length', '路径长度'), 'y': t('analysis.session_count', '会话数量')}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # 会话持续时间分布
        st.subheader("⏱️ " + t('analysis.session_duration_distribution', '会话时长分布'))
        
        durations = [s.duration_seconds / 60 for s in sessions if hasattr(s, 'duration_seconds') and s.duration_seconds and s.duration_seconds > 0]  # 转换为分钟
        
        if durations:
            fig = px.histogram(
                x=durations,
                nbins=20,
                title=t('analysis.session_duration_hist', '会话持续时间分布'),
                labels={'x': t('analysis.duration_minutes', '持续时间(分钟)'), 'y': t('analysis.session_count', '会话数量')}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_path_patterns(self, results: Dict[str, Any]):
        """渲染路径模式标签页"""
        st.subheader("🗺️ " + t('analysis.identified_patterns', '识别的路径模式'))
        
        path_patterns = results.get('path_patterns')
        
        if not path_patterns or not hasattr(path_patterns, 'common_patterns'):
            st.info(t('analysis.no_patterns', '暂无路径模式'))
            return
        
        # 获取各类型模式
        pattern_types = {
            'common': path_patterns.common_patterns,
            'conversion': path_patterns.conversion_paths,
            'anomalous': path_patterns.anomalous_patterns,
            'exit': path_patterns.exit_patterns
        }
        
        # 显示各类型模式
        for pattern_type, patterns in pattern_types.items():
            if not patterns:
                continue
                
            if pattern_type == 'common':
                st.subheader("🔥 " + t('analysis.common_patterns', '常见路径模式'))
            elif pattern_type == 'conversion':
                st.subheader("🎯 " + t('analysis.conversion_patterns', '转化路径模式'))
            elif pattern_type == 'anomalous':
                st.subheader("⚠️ " + t('analysis.anomalous_patterns', '异常路径模式'))
            elif pattern_type == 'exit':
                st.subheader("🚪 " + t('analysis.exit_patterns', '退出路径模式'))
            
            # 显示模式表格
            pattern_data = []
            for pattern in patterns[:10]:  # 显示前10个模式
                pattern_data.append({
                    t('analysis.path_pattern', 'Path Pattern'): ' → '.join(pattern.path_sequence),
                    t('analysis.frequency', 'Frequency'): pattern.frequency,
                    t('analysis.user_count', 'User Count'): pattern.user_count,
                    t('analysis.avg_duration_minutes', 'Avg Duration (minutes)'): f"{pattern.avg_duration/60:.1f}" if pattern.avg_duration else 'N/A',
                    t('analysis.conversion_rate', 'Conversion Rate'): f"{pattern.conversion_rate:.1%}" if pattern.conversion_rate else 'N/A'
                })
            
            if pattern_data:
                df = pd.DataFrame(pattern_data)
                st.dataframe(df, use_container_width=True)
                
                if len(patterns) > 10:
                    st.info(t('analysis.showing_top_patterns', 'Showing top 10 patterns, found {count} {type} patterns').format(count=len(patterns), type=pattern_type))
    
    def _render_visualizations(self, results: Dict[str, Any]):
        """渲染可视化标签页"""
        st.subheader("📈 " + t('analysis.path_visualizations', '路径可视化'))
        
        sessions = results.get('sessions', [])
        path_patterns = results.get('path_patterns', [])
        
        if not sessions:
            st.info(t('analysis.no_visualization_data', '暂无可视化数据'))
            return
        
        # 路径流向图
        self._create_path_flow_chart(sessions)
        
        # 模式频次图
        if path_patterns:
            self._create_pattern_frequency_chart(path_patterns)
        
        # 路径桑基图
        self._create_path_sankey_diagram(sessions)
    
    def _create_path_flow_chart(self, sessions):
        """创建路径流向图"""
        st.subheader("🌊 " + t('analysis.path_flow_chart', '路径流向图'))
        
        # 统计事件转换
        transitions = {}
        
        for session in sessions:
            if hasattr(session, 'path_sequence') and session.path_sequence:
                path = session.path_sequence
                for i in range(len(path) - 1):
                    current = path[i]
                    next_event = path[i + 1]
                    transition = f"{current} → {next_event}"
                    transitions[transition] = transitions.get(transition, 0) + 1
        
        if transitions:
            # 取前20个最常见的转换
            top_transitions = sorted(transitions.items(), key=lambda x: x[1], reverse=True)[:20]
            
            transition_names = [item[0] for item in top_transitions]
            transition_counts = [item[1] for item in top_transitions]
            
            fig = px.bar(
                x=transition_counts,
                y=transition_names,
                orientation='h',
                title=t('analysis.top_transitions', '最常见的路径转换'),
                labels={'x': t('analysis.transition_count', '转换次数'), 'y': t('analysis.transition', '转换')}
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
    
    def _create_pattern_frequency_chart(self, path_patterns):
        """创建模式频次图"""
        st.subheader("📊 " + t('analysis.pattern_frequency_chart', '模式频次图'))
        
        if not path_patterns or not hasattr(path_patterns, 'common_patterns'):
            st.info(t('analysis.no_pattern_data', '暂无模式数据'))
            return
        
        # 按类型分组统计
        pattern_type_counts = {
            'common': len(path_patterns.common_patterns),
            'conversion': len(path_patterns.conversion_paths),
            'anomalous': len(path_patterns.anomalous_patterns),
            'exit': len(path_patterns.exit_patterns)
        }
        
        # 过滤掉计数为0的类型
        pattern_type_counts = {k: v for k, v in pattern_type_counts.items() if v > 0}
        
        if pattern_type_counts:
            type_names = list(pattern_type_counts.keys())
            type_counts = list(pattern_type_counts.values())
            
            fig = px.pie(
                values=type_counts,
                names=type_names,
                title=t('analysis.pattern_type_distribution', '路径模式类型分布')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # 显示频次最高的模式
        all_patterns = (
            path_patterns.common_patterns + 
            path_patterns.conversion_paths + 
            path_patterns.anomalous_patterns + 
            path_patterns.exit_patterns
        )
        
        if all_patterns:
            top_patterns = sorted(all_patterns, key=lambda x: x.frequency, reverse=True)[:10]
            
            pattern_names = [' → '.join(p.path_sequence[:3]) + '...' if len(p.path_sequence) > 3 
                           else ' → '.join(p.path_sequence) for p in top_patterns]
            frequencies = [p.frequency for p in top_patterns]
            
            fig = px.bar(
                x=frequencies,
                y=pattern_names,
                orientation='h',
                title=t('analysis.top_pattern_frequencies', '频次最高的路径模式'),
                labels={'x': t('analysis.frequency', '频次'), 'y': t('analysis.pattern', '模式')}
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    def _create_path_sankey_diagram(self, sessions):
        """创建路径桑基图"""
        st.subheader("🌊 " + t('analysis.path_sankey', '路径桑基图'))
        
        # 限制显示步数避免图表过于复杂
        max_steps = 5
        
        # 统计每步的事件分布
        step_events = {}
        
        for session in sessions:
            if hasattr(session, 'path_sequence') and session.path_sequence:
                path = session.path_sequence[:max_steps]  # 只取前几步
                for step, event in enumerate(path):
                    if step not in step_events:
                        step_events[step] = {}
                    step_events[step][event] = step_events[step].get(event, 0) + 1
        
        if len(step_events) > 1:
            # 构建桑基图数据
            all_events = set()
            for step_data in step_events.values():
                all_events.update(step_data.keys())
            
            # 为每个事件创建唯一标识
            event_to_id = {event: i for i, event in enumerate(all_events)}
            
            # 构建连接
            source = []
            target = []
            value = []
            
            for session in sessions:
                if hasattr(session, 'path_sequence') and session.path_sequence:
                    path = session.path_sequence[:max_steps]
                    for i in range(len(path) - 1):
                        current_event = path[i]
                        next_event = path[i + 1]
                        
                        source.append(event_to_id[current_event])
                        target.append(event_to_id[next_event])
                    
            # 统计连接权重
            connections = {}
            if source and target and len(source) == len(target):
                for s, target_val in zip(source, target):
                    key = (s, target_val)
                    connections[key] = connections.get(key, 0) + 1
            
            # 准备最终数据
            final_source = []
            final_target = []
            final_value = []
            
            if connections:
                for connection_key, weight in connections.items():
                    if isinstance(connection_key, tuple) and len(connection_key) == 2:
                        s, target_node = connection_key
                        if weight > 1:  # 只显示出现多次的连接
                            final_source.append(s)
                            final_target.append(target_node)
                            final_value.append(weight)
            
            if final_source:
                # 创建桑基图
                fig = go.Figure(data=[go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=list(all_events),
                    ),
                    link=dict(
                        source=final_source,
                        target=final_target,
                        value=final_value
                    )
                )])
                
                fig.update_layout(
                    title_text=t('analysis.user_path_flow', '用户路径流向'),
                    font_size=10,
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_session_details(self, results: Dict[str, Any]):
        """渲染会话详情标签页"""
        st.subheader("🔍 " + t('analysis.session_details', '会话详情'))
        
        sessions = results.get('sessions', [])
        
        if not sessions:
            st.info(t('analysis.no_session_details', '暂无会话详情'))
            return
        
        # 会话筛选
        col1, col2 = st.columns(2)
        
        with col1:
            min_length = st.slider(
                t('analysis.filter_min_length', '最小路径长度'),
                min_value=1,
                max_value=20,
                value=1,
                key='session_filter_min'
            )
        
        with col2:
            max_length = st.slider(
                t('analysis.filter_max_length', '最大路径长度'),
                min_value=2,
                max_value=50,
                value=20,
                key='session_filter_max'
            )
        
        # 筛选会话
        filtered_sessions = [
            s for s in sessions 
            if min_length <= len(s.path_sequence) <= max_length
        ]
        
        st.info(t('analysis.showing_sessions', 'Showing {shown} sessions (out of {total} total)').format(shown=len(filtered_sessions), total=len(sessions)))
        
        # 显示会话样本
        session_data = []
        for i, session in enumerate(filtered_sessions[:20]):  # 显示前20个会话
            path_text = ' → '.join(session.path_sequence)
            session_data.append({
                t('analysis.session_id', 'Session ID'): session.session_id,
                t('analysis.user_id', 'User ID'): session.user_id,
                t('analysis.path_length', 'Path Length'): len(session.path_sequence),
                t('analysis.duration_minutes', 'Duration (minutes)'): f"{session.duration_seconds/60:.1f}" if session.duration_seconds else 'N/A',
                t('analysis.page_views', 'Page Views'): session.page_views,
                t('analysis.conversions', 'Conversions'): session.conversions,
                t('analysis.path_sequence', 'Path Sequence'): path_text[:100] + '...' if len(path_text) > 100 else path_text
            })
        
        if session_data:
            df = pd.DataFrame(session_data)
            st.dataframe(df, use_container_width=True)
        
        if len(filtered_sessions) > 20:
            st.info(t('analysis.showing_top_sessions', 'Showing top 20 sessions, filtered {count} sessions').format(count=len(filtered_sessions)))
    
    def _render_insights_and_recommendations(self, results: Dict[str, Any]):
        """渲染洞察与建议标签页"""
        st.subheader("💡 " + t('analysis.insights_and_recommendations', '洞察与建议'))
        
        insights = results.get('insights', {})
        
        # 模式洞察
        pattern_insights = insights.get('pattern_insights', [])
        if pattern_insights:
            st.subheader("🔍 " + t('analysis.pattern_insights', '模式洞察'))
            for insight in pattern_insights:
                st.info(insight)
        
        # 流程洞察
        flow_insights = insights.get('flow_insights', [])
        if flow_insights:
            st.subheader("🌊 " + t('analysis.flow_insights', '流程洞察'))
            for insight in flow_insights:
                st.success(insight)
        
        # 优化建议
        recommendations = insights.get('recommendations', [])
        if recommendations:
            st.subheader("📋 " + t('analysis.optimization_recommendations', '优化建议'))
            for i, recommendation in enumerate(recommendations, 1):
                st.write(f"**{i}.** {recommendation}")
        
        # 基于数据的额外洞察
        sessions = results.get('sessions', [])
        if sessions:
            st.subheader("📊 " + t('analysis.additional_insights', '额外洞察'))
            
            # 计算一些额外的统计信息
            total_sessions = len(sessions)
            conversion_sessions = len([s for s in sessions if s.conversions > 0])
            avg_conversions = np.mean([s.conversions for s in sessions])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(t('analysis.conversion_session_ratio', 'Conversion Session Ratio'), f"{conversion_sessions/total_sessions:.1%}")
                st.metric(t('analysis.avg_conversions', 'Average Conversions'), f"{avg_conversions:.2f}")
            
            with col2:
                # 路径多样性分析
                unique_paths = set()
                for session in sessions:
                    path_str = ' → '.join(session.path_sequence)
                    unique_paths.add(path_str)
                
                path_diversity = len(unique_paths) / total_sessions if total_sessions > 0 else 0
                st.metric(t('analysis.path_diversity', 'Path Diversity'), f"{path_diversity:.2f}")
                
                # 平均页面浏览数
                avg_page_views = np.mean([s.page_views for s in sessions])
                st.metric(t('analysis.avg_page_views', 'Average Page Views'), f"{avg_page_views:.1f}")


@render_data_status_check
def show_path_analysis_page():
    """显示路径分析页面 - 保持向后兼容"""
    page = PathAnalysisPage()
    page.render()
