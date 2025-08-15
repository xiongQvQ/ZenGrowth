"""
转化分析页面
分析用户转化路径和效果
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from engines.conversion_analysis_engine import ConversionAnalysisEngine
from visualization.chart_generator import ChartGenerator
from visualization.advanced_visualizer import AdvancedVisualizer
from utils.i18n import t
from ui.components.common import render_no_data_warning, render_data_status_check

class ConversionAnalysisPage:
    """转化分析页面类"""
    
    def __init__(self):
        self._initialize_engines()
    
    def _initialize_engines(self):
        """初始化分析引擎和可视化组件"""
        if 'conversion_engine' not in st.session_state:
            st.session_state.conversion_engine = ConversionAnalysisEngine()
        if 'chart_generator' not in st.session_state:
            st.session_state.chart_generator = ChartGenerator()
        if 'advanced_visualizer' not in st.session_state:
            st.session_state.advanced_visualizer = AdvancedVisualizer()
    
    def render(self):
        """渲染转化分析页面"""
        from ui.state import get_state_manager
        
        # 检查数据状态
        state_manager = get_state_manager()
        if not state_manager.is_data_loaded():
            render_no_data_warning()
            return
        
        st.header("🎯 " + t("pages.conversion_analysis.title", "转化分析"))
        st.markdown("---")
        
        # 分析配置面板
        config = self._render_analysis_config()
        
        # 执行分析按钮
        if st.button(t('analysis.start_conversion_analysis', '开始转化分析'), type="primary"):
            self._execute_conversion_analysis(config)
        
        # 显示分析结果
        if 'conversion_analysis_results' in st.session_state:
            self._render_analysis_results()
    
    def _render_analysis_config(self) -> Dict[str, Any]:
        """渲染分析配置面板"""
        with st.expander(t('analysis.conversion_config', '转化分析配置'), expanded=False):
            
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
                    t('analysis.analysis_type', '分析类型'),
                    options=[
                        t('analysis.predefined_funnels', '预定义漏斗'),
                        t('analysis.custom_funnel', '自定义漏斗'),
                        t('analysis.all_funnels', '所有漏斗')
                    ],
                    index=0,
                    help=t('analysis.analysis_type_help', '选择转化分析的类型')
                )
            
            with col3:
                time_window = st.slider(
                    t('analysis.time_window', '时间窗口(小时)'),
                    min_value=1,
                    max_value=168,  # 7天
                    value=24,
                    help=t('analysis.time_window_help', '转化步骤间的最大时间间隔')
                )
            
            # 高级配置
            with st.expander(t('analysis.advanced_config', '高级配置'), expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    include_attribution = st.checkbox(
                        t('analysis.include_attribution', '包含归因分析'),
                        value=True,
                        help=t('analysis.attribution_help', '分析转化的归因模式')
                    )
                    
                    include_segments = st.checkbox(
                        t('analysis.include_segments', '包含分段分析'),
                        value=True,
                        help=t('analysis.segments_help', '按平台、设备等维度分析')
                    )
                
                with col2:
                    min_users_threshold = st.slider(
                        t('analysis.min_users_threshold', '最小用户数阈值'),
                        min_value=1,
                        max_value=100,
                        value=10,
                        help=t('analysis.min_users_help', '漏斗分析的最小用户数要求')
                    )
                    
                    attribution_window = st.slider(
                        t('analysis.attribution_window', '归因窗口(天)'),
                        min_value=1,
                        max_value=30,
                        value=7,
                        help=t('analysis.attribution_window_help', '归因分析的时间窗口')
                    )
            
            # 自定义漏斗配置
            custom_funnel_steps = []
            if analysis_type == t('analysis.custom_funnel', '自定义漏斗'):
                st.subheader(t('analysis.custom_funnel_config', '自定义漏斗配置'))
                
                # 获取可用事件类型
                from ui.state import get_state_manager
                state_manager = get_state_manager()
                data_summary = state_manager.get_data_summary()
                event_types = list(data_summary.get('event_types', {}).keys()) if data_summary else []
                
                if event_types:
                    custom_funnel_steps = st.multiselect(
                        t('analysis.funnel_steps', '漏斗步骤'),
                        options=event_types,
                        default=[],
                        help=t('analysis.funnel_steps_help', '按顺序选择漏斗的各个步骤')
                    )
                else:
                    st.warning(t('analysis.no_event_types', '暂无可用的事件类型'))
        
        return {
            'date_range': date_range,
            'analysis_type': analysis_type,
            'time_window': time_window,
            'include_attribution': include_attribution,
            'include_segments': include_segments,
            'min_users_threshold': min_users_threshold,
            'attribution_window': attribution_window,
            'custom_funnel_steps': custom_funnel_steps
        }
    
    def _execute_conversion_analysis(self, config: Dict[str, Any]):
        """执行转化分析"""
        from ui.state import get_state_manager
        
        with st.spinner(t('analysis.conversion_processing', '正在执行转化分析...')):
            try:
                # 获取数据
                state_manager = get_state_manager()
                raw_data = state_manager.get_raw_data()
                
                if raw_data.empty:
                    st.error(t('analysis.no_data', '没有可用的数据进行分析'))
                    return
                
                # 初始化引擎
                engine = st.session_state.conversion_engine
                
                # 应用时间筛选
                filtered_data = self._filter_data_by_time(raw_data, config['date_range'])
                
                # 执行转化分析
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 步骤1: 基础转化分析
                status_text.text(t('analysis.step_basic_conversion', '执行基础转化分析...'))
                progress_bar.progress(20)
                
                conversion_result = self._perform_conversion_analysis(engine, filtered_data, config)
                
                # 步骤2: 归因分析（如果启用）
                attribution_result = None
                if config.get('include_attribution', False):
                    status_text.text(t('analysis.step_attribution', '执行归因分析...'))
                    progress_bar.progress(50)
                    attribution_result = engine.analyze_conversion_attribution(
                        filtered_data, 
                        config.get('attribution_window', 7)
                    )
                
                # 步骤3: 流失点分析
                status_text.text(t('analysis.step_dropoff_analysis', '分析流失点...'))
                progress_bar.progress(70)
                
                dropoff_result = self._analyze_dropoff_points(engine, filtered_data, config)
                
                # 步骤4: 用户旅程分析
                status_text.text(t('analysis.step_user_journeys', '分析用户旅程...'))
                progress_bar.progress(90)
                
                user_journeys = self._analyze_user_journeys(engine, filtered_data, config)
                
                # 完成分析
                status_text.text(t('analysis.step_completed', '分析完成'))
                progress_bar.progress(100)
                
                # 存储分析结果
                results = {
                    'conversion_result': conversion_result,
                    'attribution_result': attribution_result,
                    'dropoff_result': dropoff_result,
                    'user_journeys': user_journeys,
                    'config': config,
                    'data_size': len(filtered_data),
                    'analysis_time': datetime.now().isoformat()
                }
                
                # 使用StateManager存储结果
                state_manager.set_analysis_results('conversion', results)
                st.session_state.conversion_analysis_results = results
                
                st.success(t('analysis.conversion_complete', '✅ 转化分析完成!'))
                
            except Exception as e:
                st.error(f"{t('analysis.analysis_failed', '转化分析失败')}: {str(e)}")
                import traceback
                st.text("详细错误信息:")
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
    
    def _perform_conversion_analysis(self, engine, data: pd.DataFrame, config: Dict[str, Any]):
        """执行转化分析"""
        try:
            analysis_type = config.get('analysis_type', '')
            
            if analysis_type == t('analysis.custom_funnel', '自定义漏斗'):
                # 自定义漏斗分析
                custom_steps = config.get('custom_funnel_steps', [])
                if not custom_steps:
                    st.warning(t('analysis.no_custom_steps', '请配置自定义漏斗步骤'))
                    return None
                
                funnel_definitions = {'custom_funnel': custom_steps}
                return engine.calculate_conversion_rates(data, funnel_definitions)
            
            elif analysis_type == t('analysis.all_funnels', '所有漏斗'):
                # 所有预定义漏斗分析
                return engine.calculate_conversion_rates(data)
            
            else:
                # 预定义漏斗分析（默认）
                return engine.calculate_conversion_rates(data)
                
        except Exception as e:
            st.error(f"{t('analysis.conversion_execution_failed', 'Conversion analysis execution failed')}: {e}")
            return None
    
    def _analyze_dropoff_points(self, engine, data: pd.DataFrame, config: Dict[str, Any]):
        """分析流失点"""
        try:
            custom_steps = config.get('custom_funnel_steps', [])
            if custom_steps:
                return engine.identify_drop_off_points(data, custom_steps)
            else:
                return engine.identify_drop_off_points(data)
        except Exception as e:
            st.warning(f"{t('analysis.dropoff_analysis_failed', 'Drop-off point analysis failed')}: {e}")
            return None
    
    def _analyze_user_journeys(self, engine, data: pd.DataFrame, config: Dict[str, Any]):
        """分析用户旅程"""
        try:
            custom_steps = config.get('custom_funnel_steps', [])
            if custom_steps:
                return engine.create_user_conversion_journeys(data, custom_steps)
            else:
                return engine.create_user_conversion_journeys(data)
        except Exception as e:
            st.warning(f"{t('analysis.journey_analysis_failed', 'User journey analysis failed')}: {e}")
            return []
    
    def _render_analysis_results(self):
        """渲染分析结果"""
        results = st.session_state.conversion_analysis_results
        
        if not results:
            st.warning(t('analysis.no_results', '没有分析结果可显示'))
            return
        
        st.markdown("---")
        st.subheader("📊 " + t('analysis.conversion_results', '转化分析结果'))
        
        # 创建标签页
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 " + t('analysis.overview', '概览'),
            "🔍 " + t('analysis.funnel_details', '漏斗详情'),
            "📊 " + t('analysis.visualizations', '可视化'),
            "🛤️ " + t('analysis.user_journeys', '用户旅程'),
            "💡 " + t('analysis.insights', '洞察与建议')
        ])
        
        with tab1:
            self._render_overview(results)
        
        with tab2:
            self._render_funnel_details(results)
        
        with tab3:
            self._render_visualizations(results)
        
        with tab4:
            self._render_user_journeys(results)
        
        with tab5:
            self._render_insights_and_recommendations(results)
    
    def _render_overview(self, results: Dict[str, Any]):
        """渲染概览标签页"""
        st.subheader("📈 " + t('analysis.key_metrics', '关键指标'))
        
        conversion_result = results.get('conversion_result')
        if not conversion_result or not conversion_result.funnels:
            st.info(t('analysis.no_conversion_data', '暂无转化数据'))
            return
        
        # 关键指标
        col1, col2, col3, col4 = st.columns(4)
        
        funnels = conversion_result.funnels
        avg_conversion = sum(f.overall_conversion_rate for f in funnels) / len(funnels)
        max_conversion = max(f.overall_conversion_rate for f in funnels)
        total_users_analyzed = sum(f.total_users_entered for f in funnels)
        total_conversions = sum(f.total_users_converted for f in funnels)
        
        with col1:
            st.metric(
                t('analysis.avg_conversion_rate', '平均转化率'),
                f"{avg_conversion:.1%}",
                help=t('analysis.avg_conversion_help', '所有漏斗的平均转化率')
            )
        
        with col2:
            st.metric(
                t('analysis.best_conversion_rate', '最佳转化率'),
                f"{max_conversion:.1%}",
                help=t('analysis.best_conversion_help', '表现最好的漏斗转化率')
            )
        
        with col3:
            st.metric(
                t('analysis.total_users_analyzed', '分析用户数'),
                f"{total_users_analyzed:,}",
                help=t('analysis.total_users_help', '参与转化分析的用户总数')
            )
        
        with col4:
            st.metric(
                t('analysis.total_conversions', '总转化数'),
                f"{total_conversions:,}",
                help=t('analysis.total_conversions_help', '成功转化的用户总数')
            )
        
        # 漏斗性能对比
        st.subheader("🏆 " + t('analysis.funnel_performance', '漏斗性能对比'))
        
        funnel_data = []
        for funnel in funnels:
            funnel_data.append({
                t('analysis.funnel_name', 'Funnel Name'): funnel.funnel_name,
                t('analysis.conversion_rate', 'Conversion Rate'): f"{funnel.overall_conversion_rate:.1%}",
                t('analysis.users_entered', 'Users Entered'): funnel.total_users_entered,
                t('analysis.users_converted', 'Users Converted'): funnel.total_users_converted,
                t('analysis.bottleneck_step', 'Bottleneck Step'): funnel.bottleneck_step or 'N/A'
            })
        
        if funnel_data:
            df = pd.DataFrame(funnel_data)
            st.dataframe(df, use_container_width=True)
    
    def _render_funnel_details(self, results: Dict[str, Any]):
        """渲染漏斗详情标签页"""
        st.subheader("🔍 " + t('analysis.detailed_funnel_analysis', '详细漏斗分析'))
        
        conversion_result = results.get('conversion_result')
        if not conversion_result or not conversion_result.funnels:
            st.info(t('analysis.no_funnel_details', '暂无漏斗详情'))
            return
        
        # 选择漏斗
        funnel_names = [f.funnel_name for f in conversion_result.funnels]
        selected_funnel_name = st.selectbox(
            t('analysis.select_funnel', '选择漏斗'),
            options=funnel_names,
            index=0
        )
        
        selected_funnel = next(f for f in conversion_result.funnels if f.funnel_name == selected_funnel_name)
        
        # 漏斗基本信息
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(t('analysis.overall_conversion', '整体转化率'), f"{selected_funnel.overall_conversion_rate:.1%}")
            st.metric(t('analysis.users_entered', '进入用户数'), f"{selected_funnel.total_users_entered:,}")
        
        with col2:
            st.metric(t('analysis.users_converted', '转化用户数'), f"{selected_funnel.total_users_converted:,}")
            if selected_funnel.avg_completion_time:
                st.metric(t('analysis.avg_completion_time', '平均完成时间'), f"{selected_funnel.avg_completion_time/60:.1f}分钟")
        
        # 步骤详情
        st.subheader("📋 " + t('analysis.step_details', '步骤详情'))
        
        step_data = []
        for step in selected_funnel.steps:
            step_data.append({
                t('analysis.step', 'Step'): step.step_name,
                t('analysis.order', 'Order'): step.step_order + 1,
                t('analysis.users_reached', 'Users Reached'): f"{step.total_users:,}",
                t('analysis.conversion_rate', 'Conversion Rate'): f"{step.conversion_rate:.1%}",
                t('analysis.dropoff_rate', 'Drop-off Rate'): f"{step.drop_off_rate:.1%}",
                t('analysis.avg_time_to_next', 'Avg Time to Next'): f"{step.avg_time_to_next_step/60:.1f} {t('common.minutes', 'minutes')}" if step.avg_time_to_next_step else 'N/A'
            })
        
        if step_data:
            df = pd.DataFrame(step_data)
            st.dataframe(df, use_container_width=True)
        
        # 瓶颈分析
        if selected_funnel.bottleneck_step:
            st.warning(f"🚨 **{t('analysis.bottleneck_step', 'Bottleneck Step')}**: {selected_funnel.bottleneck_step}")
            st.info(f"💡 {t('analysis.optimize_bottleneck', 'Focus on optimizing this step to improve overall conversion rate')}")
    
    def _render_visualizations(self, results: Dict[str, Any]):
        """渲染可视化标签页"""
        st.subheader("📊 " + t('analysis.conversion_visualizations', '转化可视化'))
        
        conversion_result = results.get('conversion_result')
        if not conversion_result or not conversion_result.funnels:
            st.info(t('analysis.no_visualization_data', '暂无可视化数据'))
            return
        
        # 漏斗图
        self._create_funnel_chart(conversion_result.funnels)
        
        # 转化率对比图
        self._create_conversion_comparison_chart(conversion_result.funnels)
        
        # 流失点分析图
        dropoff_result = results.get('dropoff_result')
        if dropoff_result:
            self._create_dropoff_analysis_chart(dropoff_result)
    
    def _create_funnel_chart(self, funnels):
        """创建漏斗图"""
        st.subheader("🏺 " + t('analysis.funnel_chart', '转化漏斗图'))
        
        # 选择漏斗
        funnel_names = [f.funnel_name for f in funnels]
        selected_funnel_name = st.selectbox(
            t('analysis.select_funnel_for_chart', '选择要显示的漏斗'),
            options=funnel_names,
            key='funnel_chart_select'
        )
        
        selected_funnel = next(f for f in funnels if f.funnel_name == selected_funnel_name)
        
        # 准备数据
        steps = []
        values = []
        
        for step in selected_funnel.steps:
            steps.append(step.step_name)
            values.append(step.total_users)
        
        # 创建漏斗图
        fig = go.Figure(go.Funnel(
            y=steps,
            x=values,
            textinfo="value+percent initial",
            opacity=0.8,
            marker={"color": ["deepskyblue", "lightsalmon", "tan", "teal", "silver"],
                   "line": {"width": [4, 2, 2, 3, 1, 1], "color": ["wheat", "wheat", "blue", "wheat", "wheat"]}},
            connector={"line": {"color": "royalblue", "dash": "dot", "width": 3}}
        ))
        
        fig.update_layout(
            title=f"{selected_funnel_name} {t('analysis.conversion_funnel', 'Conversion Funnel')}",
            font_size=12,
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _create_conversion_comparison_chart(self, funnels):
        """创建转化率对比图"""
        st.subheader("📊 " + t('analysis.conversion_comparison', '转化率对比'))
        
        funnel_names = [f.funnel_name for f in funnels]
        conversion_rates = [f.overall_conversion_rate * 100 for f in funnels]
        
        fig = px.bar(
            x=funnel_names,
            y=conversion_rates,
            title=t('analysis.overall_conversion_rates', '各漏斗整体转化率'),
            labels={'x': t('analysis.funnel_name', '漏斗名称'), 'y': t('analysis.conversion_rate_percent', '转化率 (%)')},
            color=conversion_rates,
            color_continuous_scale='viridis'
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    def _create_dropoff_analysis_chart(self, dropoff_result):
        """创建流失点分析图"""
        if not dropoff_result or 'funnel_steps' not in dropoff_result:
            return
        
        st.subheader("📉 " + t('analysis.dropoff_analysis', '流失点分析'))
        
        steps_data = dropoff_result['funnel_steps']
        if not steps_data:
            st.info(t('analysis.no_dropoff_data', '暂无流失点数据'))
            return
        
        # 准备数据
        step_names = []
        users_lost_rates = []
        
        for step_info in steps_data:
            if 'users_lost_rate' in step_info:
                step_names.append(step_info['step_name'])
                users_lost_rates.append(step_info['users_lost_rate'] * 100)
        
        if step_names and users_lost_rates:
            fig = px.bar(
                x=step_names,
                y=users_lost_rates,
                title=t('analysis.step_dropoff_rates', '各步骤流失率'),
                labels={'x': t('analysis.step_name', '步骤名称'), 'y': t('analysis.dropoff_rate_percent', '流失率 (%)')},
                color=users_lost_rates,
                color_continuous_scale='reds'
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_user_journeys(self, results: Dict[str, Any]):
        """渲染用户旅程标签页"""
        st.subheader("🛤️ " + t('analysis.user_conversion_journeys', '用户转化旅程'))
        
        user_journeys = results.get('user_journeys', [])
        if not user_journeys:
            st.info(t('analysis.no_journey_data', '暂无用户旅程数据'))
            return
        
        # 旅程统计
        col1, col2, col3 = st.columns(3)
        
        total_journeys = len(user_journeys)
        converted_journeys = len([j for j in user_journeys if j.conversion_status == 'converted'])
        conversion_rate = (converted_journeys / total_journeys * 100) if total_journeys > 0 else 0
        
        with col1:
            st.metric(t('analysis.total_journeys', '总旅程数'), f"{total_journeys:,}")
        
        with col2:
            st.metric(t('analysis.converted_journeys', '转化旅程数'), f"{converted_journeys:,}")
        
        with col3:
            st.metric(t('analysis.journey_conversion_rate', '旅程转化率'), f"{conversion_rate:.1f}%")
        
        # 旅程状态分布
        st.subheader("📈 " + t('analysis.journey_status_distribution', '旅程状态分布'))
        
        status_counts = {}
        for journey in user_journeys:
            status = journey.conversion_status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        if status_counts:
            fig = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                title=t('analysis.journey_status_breakdown', '用户旅程状态分解')
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # 旅程样本
        st.subheader("🔍 " + t('analysis.journey_samples', '旅程样本'))
        
        # 显示前10个旅程
        journey_data = []
        for i, journey in enumerate(user_journeys[:10]):
            steps_text = ' → '.join([step['step_name'] for step in journey.journey_steps])
            journey_data.append({
                t('analysis.user_id', 'User ID'): journey.user_id,
                t('analysis.conversion_status', 'Conversion Status'): journey.conversion_status,
                t('analysis.journey_steps', 'Journey Steps'): steps_text,
                t('analysis.total_duration_min', 'Total Duration (min)'): f"{journey.total_journey_time/60:.1f}" if journey.total_journey_time else 'N/A',
                t('analysis.dropoff_step', 'Drop-off Step'): journey.drop_off_step or 'N/A'
            })
        
        if journey_data:
            df = pd.DataFrame(journey_data)
            st.dataframe(df, use_container_width=True)
    
    def _render_insights_and_recommendations(self, results: Dict[str, Any]):
        """渲染洞察与建议标签页"""
        st.subheader("💡 " + t('analysis.insights_and_recommendations', '洞察与建议'))
        
        conversion_result = results.get('conversion_result')
        if not conversion_result:
            st.info(t('analysis.no_insights_data', '暂无洞察数据'))
            return
        
        # 获取洞察
        engine = st.session_state.conversion_engine
        insights = engine.get_conversion_insights(conversion_result)
        
        # 关键指标洞察
        if insights.get('key_metrics'):
            st.subheader("📊 " + t('analysis.key_insights', '关键洞察'))
            metrics = insights['key_metrics']
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**{t('analysis.avg_conversion_rate', 'Average Conversion Rate')}**: {metrics.get('avg_conversion_rate', 0):.1%}")
                st.info(f"**{t('analysis.best_conversion_rate', 'Best Conversion Rate')}**: {metrics.get('best_conversion_rate', 0):.1%}")
            
            with col2:
                st.info(f"**{t('analysis.worst_conversion_rate', 'Worst Conversion Rate')}**: {metrics.get('worst_conversion_rate', 0):.1%}")
                st.info(f"**{t('analysis.total_funnels_analyzed', 'Total Funnels Analyzed')}**: {metrics.get('total_funnels_analyzed', 0)}")
        
        # 优化机会
        if insights.get('optimization_opportunities'):
            st.subheader("🎯 " + t('analysis.optimization_opportunities', '优化机会'))
            for opportunity in insights['optimization_opportunities']:
                with st.expander(f"🔧 {opportunity.get('funnel', 'Unknown')} - {opportunity.get('bottleneck_step', 'Unknown')}"):
                    st.write(f"**{t('analysis.conversion_rate', 'Conversion Rate')}**: {opportunity.get('conversion_rate', 0):.1%}")
                    st.write(f"**{t('analysis.improvement_suggestion', 'Improvement Suggestion')}**: {opportunity.get('improvement_potential', 'N/A')}")
        
        # 性能洞察
        if insights.get('performance_insights'):
            st.subheader("🏆 " + t('analysis.performance_insights', '性能洞察'))
            for insight in insights['performance_insights']:
                st.success(insight)
        
        # 建议清单
        if insights.get('recommendations'):
            st.subheader("📋 " + t('analysis.recommendations', '优化建议'))
            for i, recommendation in enumerate(insights['recommendations'], 1):
                st.write(f"**{i}.** {recommendation}")
        
        # 归因分析洞察
        attribution_result = results.get('attribution_result')
        if attribution_result and attribution_result.get('attribution_insights'):
            st.subheader("🎯 " + t('analysis.attribution_insights', '归因洞察'))
            for insight in attribution_result['attribution_insights']:
                st.info(insight)


@render_data_status_check
def show_conversion_analysis_page():
    """显示转化分析页面 - 保持向后兼容"""
    page = ConversionAnalysisPage()
    page.render()
