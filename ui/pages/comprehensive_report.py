"""
综合报告页面
生成全面的分析报告
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import numpy as np

from ui.components.common import render_no_data_warning, render_data_status_check
from utils.i18n import t

class ComprehensiveReportPage:
    """综合报告页面类"""
    
    def __init__(self):
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化组件"""
        pass
    
    def render(self):
        """渲染综合报告页面"""
        from ui.state import get_state_manager
        
        # 检查数据状态
        state_manager = get_state_manager()
        if not state_manager.is_data_loaded():
            render_no_data_warning()
            return
        
        st.header("📋 " + t("pages.comprehensive_report.title", "综合报告"))
        st.markdown("---")
        
        # 报告配置面板
        config = self._render_report_config()
        
        # 生成报告按钮
        if st.button(t('report.generate_report', '生成综合报告'), type="primary"):
            self._generate_comprehensive_report(config)
        
        # 显示报告结果
        if 'comprehensive_report_results' in st.session_state:
            self._render_report_results()
    
    def _render_report_config(self) -> Dict[str, Any]:
        """渲染报告配置面板"""
        with st.expander(t('report.config', '报告配置'), expanded=False):
            
            # 基础配置
            col1, col2, col3 = st.columns(3)
            
            with col1:
                date_range = st.date_input(
                    t('report.time_range_label', '时间范围'),
                    value=(datetime.now() - timedelta(days=30), datetime.now()),
                    help=t('report.time_range_help', '选择报告的时间范围')
                )
            
            with col2:
                report_type = st.selectbox(
                    t('report.report_type', '报告类型'),
                    options=[
                        t('report.executive_summary', '执行摘要'),
                        t('report.detailed_analysis', '详细分析'),
                        t('report.technical_report', '技术报告'),
                        t('report.full_report', '完整报告')
                    ],
                    index=3,
                    help=t('report.report_type_help', '选择报告的详细程度')
                )
            
            with col3:
                include_recommendations = st.checkbox(
                    t('report.include_recommendations', '包含优化建议'),
                    value=True,
                    help=t('report.recommendations_help', '在报告中包含具体的优化建议')
                )
            
            # 高级配置
            with st.expander(t('report.advanced_config', '高级配置'), expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    include_segments = st.multiselect(
                        t('report.analysis_segments', '包含分析模块'),
                        options=[
                            t('report.user_segmentation', '用户分群'),
                            t('report.event_analysis', '事件分析'),
                            t('report.retention_analysis', '留存分析'),
                            t('report.conversion_analysis', '转化分析'),
                            t('report.path_analysis', '路径分析')
                        ],
                        default=[
                            t('report.user_segmentation', '用户分群'),
                            t('report.event_analysis', '事件分析'),
                            t('report.retention_analysis', '留存分析'),
                            t('report.conversion_analysis', '转化分析'),
                            t('report.path_analysis', '路径分析')
                        ],
                        help=t('report.segments_help', '选择要包含在报告中的分析模块')
                    )
                
                with col2:
                    export_format = st.selectbox(
                        t('report.export_format', '导出格式'),
                        options=['HTML', 'PDF', 'Word'],
                        index=0,
                        help=t('report.export_help', '选择报告的导出格式')
                    )
                    
                    include_charts = st.checkbox(
                        t('report.include_charts', '包含图表'),
                        value=True,
                        help=t('report.charts_help', '在报告中包含可视化图表')
                    )
        
        return {
            'date_range': date_range,
            'report_type': report_type,
            'include_recommendations': include_recommendations,
            'include_segments': include_segments,
            'export_format': export_format,
            'include_charts': include_charts
        }
    
    def _generate_comprehensive_report(self, config: Dict[str, Any]):
        """生成综合报告"""
        from ui.state import get_state_manager
        
        with st.spinner(t('report.generating', '正在生成综合报告...')):
            try:
                # 获取数据
                state_manager = get_state_manager()
                raw_data = state_manager.get_raw_data()
                
                if raw_data.empty:
                    st.error(t('report.no_data', '没有可用的数据生成报告'))
                    return
                
                # 应用时间筛选
                filtered_data = self._filter_data_by_time(raw_data, config['date_range'])
                
                # 生成报告
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 步骤1: 数据概况分析
                status_text.text(t('report.step_data_overview', '分析数据概况...'))
                progress_bar.progress(10)
                
                data_overview = self._analyze_data_overview(filtered_data)
                
                # 步骤2: 收集已有分析结果
                status_text.text(t('report.step_collect_results', '收集分析结果...'))
                progress_bar.progress(30)
                
                analysis_results = self._collect_analysis_results(state_manager, config['include_segments'])
                
                # 步骤3: 生成关键指标
                status_text.text(t('report.step_key_metrics', '生成关键指标...'))
                progress_bar.progress(50)
                
                key_metrics = self._generate_key_metrics(filtered_data, analysis_results)
                
                # 步骤4: 趋势分析
                status_text.text(t('report.step_trend_analysis', '执行趋势分析...'))
                progress_bar.progress(70)
                
                trend_analysis = self._perform_trend_analysis(filtered_data)
                
                # 步骤5: 生成洞察和建议
                status_text.text(t('report.step_insights', '生成洞察和建议...'))
                progress_bar.progress(90)
                
                insights_and_recommendations = self._generate_insights_and_recommendations(
                    data_overview, analysis_results, key_metrics, trend_analysis, config
                )
                
                # 完成报告
                status_text.text(t('report.step_completed', '报告生成完成'))
                progress_bar.progress(100)
                
                # 存储报告结果
                report_results = {
                    'data_overview': data_overview,
                    'analysis_results': analysis_results,
                    'key_metrics': key_metrics,
                    'trend_analysis': trend_analysis,
                    'insights_and_recommendations': insights_and_recommendations,
                    'config': config,
                    'data_size': len(filtered_data),
                    'generation_time': datetime.now().isoformat()
                }
                
                # 使用StateManager存储结果
                state_manager.set_analysis_results('comprehensive_report', report_results)
                st.session_state.comprehensive_report_results = report_results
                
                st.success(t('report.generation_complete', '✅ 综合报告生成完成!'))
                
            except Exception as e:
                st.error(f"{t('report.generation_failed', '报告生成失败')}: {str(e)}")
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
            st.warning(f"{t('common.filter_failed', 'Time filter failed')}: {e}")
            return data
    
    def _analyze_data_overview(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析数据概况"""
        overview = {
            'total_events': len(data),
            'unique_users': data['user_pseudo_id'].nunique() if 'user_pseudo_id' in data.columns else 0,
            'date_range': {
                'start': data['event_datetime'].min() if 'event_datetime' in data.columns else None,
                'end': data['event_datetime'].max() if 'event_datetime' in data.columns else None
            },
            'event_types': {},
            'platforms': {},
            'countries': {}
        }
        
        # 事件类型分布
        if 'event_name' in data.columns:
            overview['event_types'] = data['event_name'].value_counts().to_dict()
        
        # 平台分布
        if 'platform' in data.columns:
            overview['platforms'] = data['platform'].value_counts().to_dict()
        
        # 国家分布
        if 'geo_country' in data.columns:
            overview['countries'] = data['geo_country'].value_counts().head(10).to_dict()
        
        return overview
    
    def _collect_analysis_results(self, state_manager, include_segments: List[str]) -> Dict[str, Any]:
        """收集已有分析结果"""
        analysis_results = {}
        
        segment_mapping = {
            t('report.user_segmentation', '用户分群'): 'user_segmentation',
            t('report.event_analysis', '事件分析'): 'event_analysis',
            t('report.retention_analysis', '留存分析'): 'retention_analysis',
            t('report.conversion_analysis', '转化分析'): 'conversion',
            t('report.path_analysis', '路径分析'): 'path'
        }
        
        for segment_name in include_segments:
            analysis_type = segment_mapping.get(segment_name)
            if analysis_type:
                try:
                    result = state_manager.get_analysis_results(analysis_type)
                    if result:
                        analysis_results[analysis_type] = result
                except:
                    pass  # 忽略未完成的分析
        
        return analysis_results
    
    def _generate_key_metrics(self, data: pd.DataFrame, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成关键指标"""
        metrics = {
            'data_quality': {},
            'user_engagement': {},
            'conversion_performance': {},
            'retention_performance': {}
        }
        
        # 数据质量指标
        metrics['data_quality'] = {
            'completeness': self._calculate_data_completeness(data),
            'consistency': self._calculate_data_consistency(data),
            'timeliness': self._calculate_data_timeliness(data)
        }
        
        # 用户参与度指标
        if 'user_pseudo_id' in data.columns:
            metrics['user_engagement'] = {
                'avg_session_duration': self._calculate_avg_session_duration(data),
                'avg_events_per_user': len(data) / data['user_pseudo_id'].nunique(),
                'bounce_rate': self._calculate_bounce_rate(data)
            }
        
        # 转化性能指标
        if 'conversion' in analysis_results:
            conversion_result = analysis_results['conversion'].get('conversion_result')
            if conversion_result and hasattr(conversion_result, 'funnels'):
                metrics['conversion_performance'] = {
                    'avg_conversion_rate': sum(f.overall_conversion_rate for f in conversion_result.funnels) / len(conversion_result.funnels),
                    'best_funnel_conversion': max(f.overall_conversion_rate for f in conversion_result.funnels),
                    'total_conversions': sum(f.total_users_converted for f in conversion_result.funnels)
                }
        
        # 留存性能指标
        if 'retention_analysis' in analysis_results:
            retention_data = analysis_results['retention_analysis']
            if retention_data:
                metrics['retention_performance'] = {
                    'day_1_retention': retention_data.get('day_1_retention', 0),
                    'day_7_retention': retention_data.get('day_7_retention', 0),
                    'day_30_retention': retention_data.get('day_30_retention', 0)
                }
        
        return metrics
    
    def _calculate_data_completeness(self, data: pd.DataFrame) -> float:
        """计算数据完整性"""
        if data.empty:
            return 0.0
        
        total_cells = data.size
        missing_cells = data.isnull().sum().sum()
        return (total_cells - missing_cells) / total_cells
    
    def _calculate_data_consistency(self, data: pd.DataFrame) -> float:
        """计算数据一致性"""
        # Simplified consistency check
        consistency_score = 1.0
        
        # Check time format consistency
        if 'event_datetime' in data.columns:
            try:
                pd.to_datetime(data['event_datetime'])
            except:
                consistency_score -= 0.2
        
        return max(0.0, consistency_score)
    
    def _calculate_data_timeliness(self, data: pd.DataFrame) -> float:
        """计算数据时效性"""
        if 'event_datetime' not in data.columns:
            return 0.0
        
        latest_event = data['event_datetime'].max()
        if pd.isna(latest_event):
            return 0.0
        
        hours_since_latest = (datetime.now() - latest_event).total_seconds() / 3600
        
        # 24小时内为1.0，每增加24小时减少0.1
        timeliness = max(0.0, 1.0 - (hours_since_latest / 24) * 0.1)
        return timeliness
    
    def _calculate_avg_session_duration(self, data: pd.DataFrame) -> float:
        """计算平均会话时长（分钟）"""
        if 'user_pseudo_id' not in data.columns or 'event_datetime' not in data.columns:
            return 0.0
        
        # 按用户分组计算会话时长
        user_sessions = data.groupby('user_pseudo_id')['event_datetime'].agg(['min', 'max'])
        durations = (user_sessions['max'] - user_sessions['min']).dt.total_seconds() / 60
        
        return durations.mean()
    
    def _calculate_bounce_rate(self, data: pd.DataFrame) -> float:
        """计算跳出率"""
        if 'user_pseudo_id' not in data.columns:
            return 0.0
        
        user_event_counts = data['user_pseudo_id'].value_counts()
        single_event_users = (user_event_counts == 1).sum()
        total_users = len(user_event_counts)
        
        return single_event_users / total_users if total_users > 0 else 0.0
    
    def _perform_trend_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """执行趋势分析"""
        trends = {
            'daily_trends': {},
            'weekly_trends': {},
            'event_trends': {}
        }
        
        if 'event_datetime' not in data.columns:
            return trends
        
        # 按日趋势
        daily_data = data.groupby(data['event_datetime'].dt.date).size()
        trends['daily_trends'] = {
            'data': daily_data.to_dict(),
            'trend_direction': self._calculate_trend_direction(daily_data.values)
        }
        
        # 按周趋势
        weekly_data = data.groupby(data['event_datetime'].dt.isocalendar().week).size()
        trends['weekly_trends'] = {
            'data': weekly_data.to_dict(),
            'trend_direction': self._calculate_trend_direction(weekly_data.values)
        }
        
        # 事件类型趋势
        if 'event_name' in data.columns:
            event_trends = data.groupby(['event_name', data['event_datetime'].dt.date]).size().unstack(fill_value=0)
            trends['event_trends'] = event_trends.to_dict()
        
        return trends
    
    def _calculate_trend_direction(self, values) -> str:
        """计算趋势方向"""
        if len(values) < 2:
            return 'stable'
        
        # 简单的线性回归斜率
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def _generate_insights_and_recommendations(self, data_overview, analysis_results, key_metrics, trend_analysis, config) -> Dict[str, Any]:
        """生成洞察和建议"""
        insights = {
            'data_insights': [],
            'performance_insights': [],
            'user_behavior_insights': [],
            'recommendations': []
        }
        
        # 数据洞察
        completeness = key_metrics.get('data_quality', {}).get('completeness', 0)
        if completeness < 0.9:
            insights['data_insights'].append(f"数据完整性为 {completeness:.1%}，建议检查数据收集流程")
        
        # 性能洞察
        if 'conversion_performance' in key_metrics:
            avg_conversion = key_metrics['conversion_performance'].get('avg_conversion_rate', 0)
            insights['performance_insights'].append(f"平均转化率为 {avg_conversion:.1%}")
            
            if avg_conversion < 0.05:
                insights['recommendations'].append("转化率较低，建议优化关键转化路径")
        
        # 用户行为洞察
        if 'user_engagement' in key_metrics:
            bounce_rate = key_metrics['user_engagement'].get('bounce_rate', 0)
            if bounce_rate > 0.7:
                insights['user_behavior_insights'].append(f"跳出率高达 {bounce_rate:.1%}，用户参与度较低")
                insights['recommendations'].append("降低跳出率，提升首屏内容吸引力")
        
        # 趋势洞察
        daily_trend = trend_analysis.get('daily_trends', {}).get('trend_direction', 'stable')
        if daily_trend == 'decreasing':
            insights['performance_insights'].append("用户活跃度呈下降趋势")
            insights['recommendations'].append("制定用户留存策略，提升用户活跃度")
        elif daily_trend == 'increasing':
            insights['performance_insights'].append("用户活跃度呈上升趋势，表现良好")
        
        # 基于配置的建议
        if config.get('include_recommendations', True):
            insights['recommendations'].extend([
                "定期监控关键指标变化趋势",
                "建立数据质量监控体系",
                "持续优化用户体验和转化路径"
            ])
        
        return insights
    
    def _render_report_results(self):
        """渲染报告结果"""
        results = st.session_state.comprehensive_report_results
        
        if not results:
            st.warning(t('report.no_results', '没有报告结果可显示'))
            return
        
        st.markdown("---")
        st.subheader("📋 " + t('report.comprehensive_results', '综合分析报告'))
        
        # 创建标签页
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 " + t('report.executive_summary', '执行摘要'),
            "📈 " + t('report.key_metrics', '关键指标'),
            "📉 " + t('report.trend_analysis', '趋势分析'),
            "🔍 " + t('report.detailed_analysis', '详细分析'),
            "💡 " + t('report.insights_recommendations', '洞察与建议')
        ])
        
        with tab1:
            self._render_executive_summary(results)
        
        with tab2:
            self._render_key_metrics(results)
        
        with tab3:
            self._render_trend_analysis(results)
        
        with tab4:
            self._render_detailed_analysis(results)
        
        with tab5:
            self._render_insights_and_recommendations(results)
    
    def _render_executive_summary(self, results: Dict[str, Any]):
        """渲染执行摘要"""
        st.subheader("📊 " + t('report.summary_title', '执行摘要'))
        
        data_overview = results.get('data_overview', {})
        key_metrics = results.get('key_metrics', {})
        
        # 数据概况
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                t('report.total_events', '总事件数'),
                f"{data_overview.get('total_events', 0):,}",
                help=t('report.total_events_help', '分析期间的总事件数量')
            )
        
        with col2:
            st.metric(
                t('report.unique_users', '独立用户数'),
                f"{data_overview.get('unique_users', 0):,}",
                help=t('report.unique_users_help', '分析期间的独立用户数量')
            )
        
        with col3:
            completeness = key_metrics.get('data_quality', {}).get('completeness', 0)
            st.metric(
                t('report.data_quality', '数据质量'),
                f"{completeness:.1%}",
                help=t('report.data_quality_help', '数据完整性得分')
            )
        
        with col4:
            avg_events = key_metrics.get('user_engagement', {}).get('avg_events_per_user', 0)
            st.metric(
                t('report.avg_events_per_user', '人均事件数'),
                f"{avg_events:.1f}",
                help=t('report.avg_events_help', '每个用户平均产生的事件数')
            )
        
        # 关键发现
        st.subheader("🔍 " + t('report.key_findings', '关键发现'))
        
        insights = results.get('insights_and_recommendations', {})
        performance_insights = insights.get('performance_insights', [])
        
        if performance_insights:
            for insight in performance_insights[:3]:  # 显示前3个关键洞察
                st.info(f"• {insight}")
        else:
            st.info("暂无关键发现")
    
    def _render_key_metrics(self, results: Dict[str, Any]):
        """渲染关键指标"""
        st.subheader("📈 " + t('report.metrics_dashboard', '指标仪表板'))
        
        key_metrics = results.get('key_metrics', {})
        
        # 数据质量指标
        st.subheader("🔧 " + t('report.data_quality_metrics', '数据质量指标'))
        
        quality_metrics = key_metrics.get('data_quality', {})
        col1, col2, col3 = st.columns(3)
        
        with col1:
            completeness = quality_metrics.get('completeness', 0)
            st.metric(t('report.completeness', 'Completeness'), f"{completeness:.1%}")
        
        with col2:
            consistency = quality_metrics.get('consistency', 0)
            st.metric(t('report.consistency', 'Consistency'), f"{consistency:.1%}")
        
        with col3:
            timeliness = quality_metrics.get('timeliness', 0)
            st.metric(t('report.timeliness', 'Timeliness'), f"{timeliness:.1%}")
        
        # 用户参与度指标
        engagement_metrics = key_metrics.get('user_engagement', {})
        if engagement_metrics:
            st.subheader("👥 " + t('report.engagement_metrics', '用户参与度指标'))
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_duration = engagement_metrics.get('avg_session_duration', 0)
                st.metric(t('report.avg_session_duration', 'Average Session Duration'), f"{avg_duration:.1f} {t('common.minutes', 'minutes')}")
            
            with col2:
                avg_events = engagement_metrics.get('avg_events_per_user', 0)
                st.metric(t('report.avg_events_per_user', 'Average Events Per User'), f"{avg_events:.1f}")
            
            with col3:
                bounce_rate = engagement_metrics.get('bounce_rate', 0)
                st.metric(t('report.bounce_rate', 'Bounce Rate'), f"{bounce_rate:.1%}")
        
        # 转化性能指标
        conversion_metrics = key_metrics.get('conversion_performance', {})
        if conversion_metrics:
            st.subheader("🎯 " + t('report.conversion_metrics', '转化性能指标'))
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_conversion = conversion_metrics.get('avg_conversion_rate', 0)
                st.metric(t('report.avg_conversion_rate', 'Average Conversion Rate'), f"{avg_conversion:.1%}")
            
            with col2:
                best_conversion = conversion_metrics.get('best_funnel_conversion', 0)
                st.metric(t('report.best_conversion_rate', 'Best Conversion Rate'), f"{best_conversion:.1%}")
            
            with col3:
                total_conversions = conversion_metrics.get('total_conversions', 0)
                st.metric(t('report.total_conversions', 'Total Conversions'), f"{total_conversions:,}")
        
        # 留存性能指标
        retention_metrics = key_metrics.get('retention_performance', {})
        if retention_metrics:
            st.subheader("🔄 " + t('report.retention_metrics', '留存性能指标'))
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                day1_retention = retention_metrics.get('day_1_retention', 0)
                st.metric(t('report.day1_retention', 'Day 1 Retention'), f"{day1_retention:.1%}")
            
            with col2:
                day7_retention = retention_metrics.get('day_7_retention', 0)
                st.metric(t('report.day7_retention', 'Day 7 Retention'), f"{day7_retention:.1%}")
            
            with col3:
                day30_retention = retention_metrics.get('day_30_retention', 0)
                st.metric(t('report.day30_retention', 'Day 30 Retention'), f"{day30_retention:.1%}")
    
    def _render_trend_analysis(self, results: Dict[str, Any]):
        """渲染趋势分析"""
        st.subheader("📉 " + t('report.trend_analysis_title', '趋势分析'))
        
        trend_analysis = results.get('trend_analysis', {})
        
        # 日活趋势
        daily_trends = trend_analysis.get('daily_trends', {})
        if daily_trends:
            st.subheader("📅 " + t('report.daily_trends', '日活趋势'))
            
            daily_data = daily_trends.get('data', {})
            if daily_data:
                dates = list(daily_data.keys())
                values = list(daily_data.values())
                
                fig = px.line(
                    x=dates,
                    y=values,
                    title=t('report.daily_event_trends', '每日事件数趋势'),
                    labels={'x': t('report.date', '日期'), 'y': t('report.event_count', '事件数')}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                trend_direction = daily_trends.get('trend_direction', 'stable')
                if trend_direction == 'increasing':
                    st.success(t('report.upward_trend', '📈 Trend is upward, user activity continues to grow'))
                elif trend_direction == 'decreasing':
                    st.warning(t('report.downward_trend', '📉 Trend is downward, need to focus on declining user activity'))
                else:
                    st.info(t('report.stable_trend', '📊 Trend is stable, user activity remains steady'))
        
        # 事件类型趋势
        event_trends = trend_analysis.get('event_trends', {})
        if event_trends:
            st.subheader("🎯 " + t('report.event_type_trends', '事件类型趋势'))
            
            # 选择前5个最活跃的事件类型进行展示
            if event_trends:
                top_events = list(event_trends.keys())[:5]
                
                for event_name in top_events:
                    event_data = event_trends[event_name]
                    if event_data:
                        dates = list(event_data.keys())
                        values = list(event_data.values())
                        
                        fig = px.line(
                            x=dates,
                            y=values,
                            title=t('report.event_trend_title', '{event} Event Trend').format(event=event_name),
                            labels={'x': t('report.date', 'Date'), 'y': t('report.event_count', 'Event Count')}
                        )
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
    
    def _render_detailed_analysis(self, results: Dict[str, Any]):
        """渲染详细分析"""
        st.subheader("🔍 " + t('report.detailed_analysis_title', '详细分析'))
        
        analysis_results = results.get('analysis_results', {})
        
        if not analysis_results:
            st.info(t('report.no_detailed_analysis', '暂无详细分析结果'))
            return
        
        # 显示各个分析模块的摘要
        for analysis_type, result in analysis_results.items():
            if analysis_type == 'conversion':
                self._render_conversion_summary(result)
            elif analysis_type == 'path':
                self._render_path_summary(result)
            elif analysis_type == 'retention_analysis':
                self._render_retention_summary(result)
            elif analysis_type == 'user_segmentation':
                self._render_segmentation_summary(result)
            elif analysis_type == 'event_analysis':
                self._render_event_summary(result)
    
    def _render_conversion_summary(self, result):
        """渲染转化分析摘要"""
        st.subheader("🎯 转化分析摘要")
        
        conversion_result = result.get('conversion_result')
        if conversion_result and hasattr(conversion_result, 'funnels'):
            col1, col2 = st.columns(2)
            
            with col1:
                avg_conversion = sum(f.overall_conversion_rate for f in conversion_result.funnels) / len(conversion_result.funnels)
                st.metric(t('report.avg_conversion_rate', 'Average Conversion Rate'), f"{avg_conversion:.1%}")
            
            with col2:
                total_funnels = len(conversion_result.funnels)
                st.metric(t('report.analyzed_funnels', 'Analyzed Funnels'), f"{total_funnels}")
            
            st.success(t('report.conversion_analysis_complete', '✅ Conversion analysis completed, view detailed results on conversion analysis page'))
        else:
            st.info(t('report.no_conversion_results', 'No conversion analysis results'))
    
    def _render_path_summary(self, result):
        """渲染路径分析摘要"""
        st.subheader("🛤️ " + t('report.path_analysis_summary', 'Path Analysis Summary'))
        
        sessions = result.get('sessions', [])
        if sessions:
            col1, col2 = st.columns(2)
            
            with col1:
                total_sessions = len(sessions)
                st.metric(t('report.analyzed_sessions', 'Analyzed Sessions'), f"{total_sessions:,}")
            
            with col2:
                avg_path_length = np.mean([len(s.path_sequence) for s in sessions])
                st.metric(t('report.avg_path_length', 'Average Path Length'), f"{avg_path_length:.1f}")
            
            st.success(t('report.path_analysis_complete', '✅ Path analysis completed, view detailed results on path analysis page'))
        else:
            st.info(t('report.no_path_results', 'No path analysis results'))
    
    def _render_retention_summary(self, result):
        """渲染留存分析摘要"""
        st.subheader("🔄 " + t('report.retention_analysis_summary', 'Retention Analysis Summary'))
        
        if result:
            st.success(t('report.retention_analysis_complete', '✅ Retention analysis completed, view detailed results on retention analysis page'))
        else:
            st.info(t('report.no_retention_results', 'No retention analysis results'))
    
    def _render_segmentation_summary(self, result):
        """渲染用户分群摘要"""
        st.subheader("👥 " + t('report.user_segmentation_summary', 'User Segmentation Summary'))
        
        if result:
            st.success(t('report.user_segmentation_complete', '✅ User segmentation completed, view detailed results on user segmentation page'))
        else:
            st.info(t('report.no_segmentation_results', 'No user segmentation results'))
    
    def _render_event_summary(self, result):
        """渲染事件分析摘要"""
        st.subheader("📊 " + t('report.event_analysis_summary', 'Event Analysis Summary'))
        
        if result:
            st.success(t('report.event_analysis_complete', '✅ Event analysis completed, view detailed results on event analysis page'))
        else:
            st.info(t('report.no_event_results', 'No event analysis results'))
    
    def _render_insights_and_recommendations(self, results: Dict[str, Any]):
        """渲染洞察与建议"""
        st.subheader("💡 " + t('report.insights_recommendations_title', '洞察与建议'))
        
        insights = results.get('insights_and_recommendations', {})
        
        # 数据洞察
        data_insights = insights.get('data_insights', [])
        if data_insights:
            st.subheader("📊 " + t('report.data_insights', '数据洞察'))
            for insight in data_insights:
                st.info(f"• {insight}")
        
        # 性能洞察
        performance_insights = insights.get('performance_insights', [])
        if performance_insights:
            st.subheader("🏆 " + t('report.performance_insights', '性能洞察'))
            for insight in performance_insights:
                st.success(f"• {insight}")
        
        # 用户行为洞察
        behavior_insights = insights.get('user_behavior_insights', [])
        if behavior_insights:
            st.subheader("👥 " + t('report.behavior_insights', '用户行为洞察'))
            for insight in behavior_insights:
                st.warning(f"• {insight}")
        
        # 优化建议
        recommendations = insights.get('recommendations', [])
        if recommendations:
            st.subheader("📋 " + t('report.optimization_recommendations', '优化建议'))
            for i, recommendation in enumerate(recommendations, 1):
                st.write(f"**{i}.** {recommendation}")
        
        # 总结
        st.subheader("📝 " + t('report.summary_conclusion', '总结'))
        
        data_overview = results.get('data_overview', {})
        total_events = data_overview.get('total_events', 0)
        unique_users = data_overview.get('unique_users', 0)
        
        st.markdown(f"""
        **报告概览**:
        - 分析了 **{total_events:,}** 个事件，涉及 **{unique_users:,}** 个独立用户
        - 数据质量评分: **{results.get('key_metrics', {}).get('data_quality', {}).get('completeness', 0):.1%}**
        - 生成时间: **{results.get('generation_time', 'Unknown')}**
        
        **下一步行动建议**:
        1. 定期审查关键指标变化
        2. 重点关注识别出的优化机会
        3. 持续监控数据质量和用户体验
        """)


@render_data_status_check
def show_comprehensive_report_page():
    """显示综合报告页面 - 保持向后兼容"""
    page = ComprehensiveReportPage()
    page.render()
