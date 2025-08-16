"""
基础图表生成器
实现基于Plotly的事件时间线图表、留存热力图和转化漏斗图表
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import numpy as np
from utils.i18n import t


class ChartGenerator:
    """基础图表生成器类，提供各种数据可视化功能"""
    
    def __init__(self):
        """初始化图表生成器"""
        self.default_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
    def create_event_timeline(self, data: pd.DataFrame) -> go.Figure:
        """
        创建事件时间线图表
        
        Args:
            data: 包含事件数据的DataFrame，需要包含event_name, event_timestamp, event_date列
            
        Returns:
            plotly.graph_objects.Figure: 事件时间线图表
        """
        if data.empty:
            return self._create_empty_chart(
                t('charts.event_timeline_title', 'Event Timeline Chart'), 
                t('charts.no_event_data', 'No event data available')
            )
            
        # 确保必要的列存在
        required_columns = ['event_name', 'event_timestamp', 'event_date']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"缺少必要的列: {missing_columns}")
        
        # 转换时间戳为日期时间
        data = data.copy()
        data['datetime'] = pd.to_datetime(data['event_timestamp'], unit='us')
        data['date'] = pd.to_datetime(data['event_date'])
        
        # 按日期和事件类型聚合数据
        daily_events = data.groupby(['date', 'event_name']).size().reset_index(name='count')
        
        # 创建时间线图表
        fig = go.Figure()
        
        # 为每种事件类型添加一条线
        event_types = daily_events['event_name'].unique()
        for i, event_type in enumerate(event_types):
            event_data = daily_events[daily_events['event_name'] == event_type]
            
            fig.add_trace(go.Scatter(
                x=event_data['date'],
                y=event_data['count'],
                mode='lines+markers',
                name=event_type,
                line=dict(color=self.default_colors[i % len(self.default_colors)]),
                hovertemplate=f'<b>{event_type}</b><br>' +
                             f'{t("charts.date_label", "Date")}: %{{x}}<br>' +
                             f'{t("charts.event_count_label", "Event Count")}: %{{y}}<br>' +
                             '<extra></extra>'
            ))
        
        # 设置图表布局
        fig.update_layout(
            title=t('charts.event_timeline_title', 'Event Timeline Analysis'),
            xaxis_title=t('charts.date_label', 'Date'),
            yaxis_title=t('charts.event_count_label', 'Event Count'),
            hovermode='x unified',
            showlegend=True,
            height=500,
            template='plotly_white'
        )
        
        return fig
    
    def create_retention_heatmap(self, data) -> go.Figure:
        """
        创建留存热力图 - 简化版本，直接处理标准格式数据

        Args:
            data: 标准格式的留存数据（DataFrame或RetentionAnalysisResult）

        Returns:
            plotly.graph_objects.Figure: 留存热力图
        """
        if data is None:
            return self._create_empty_chart(
                t('charts.retention_heatmap_title', 'Retention Heatmap'), 
                t('charts.no_retention_data', 'No retention data available')
            )

        try:
            # 处理RetentionAnalysisResult对象
            if hasattr(data, 'cohorts') and hasattr(data, 'retention_matrix'):
                if not data.cohorts:
                    return self._create_empty_chart(
                        t('charts.retention_heatmap_title', 'Retention Heatmap'), 
                        t('charts.no_cohort_data', 'No cohort data available')
                    )
                
                # 使用现有的retention_matrix如果可用
                if data.retention_matrix is not None and not data.retention_matrix.empty:
                    heatmap_data = data.retention_matrix
                else:
                    # 从cohorts构建标准格式DataFrame
                    cohort_rows = []
                    for cohort in data.cohorts:
                        for period_num, rate in enumerate(cohort.retention_rates):
                            cohort_rows.append({
                                'cohort_group': str(cohort.cohort_period),
                                'period_number': period_num,
                                'retention_rate': float(rate)
                            })
                    if not cohort_rows:
                        return self._create_empty_chart(
                            t('charts.retention_heatmap_title', 'Retention Heatmap'), 
                            t('charts.empty_cohort_data', 'Cohort data is empty')
                        )
                    data = pd.DataFrame(cohort_rows)
            
            # 转换为DataFrame并验证
            if isinstance(data, dict):
                data = pd.DataFrame(data) if data else pd.DataFrame()
            elif isinstance(data, list):
                data = pd.DataFrame(data) if data else pd.DataFrame()
            
            if not isinstance(data, pd.DataFrame) or data.empty:
                return self._create_empty_chart(
                    t('charts.retention_heatmap_title', 'Retention Heatmap'), 
                    t('charts.data_empty_or_unsupported', 'Data is empty or format not supported')
                )

            # 标准化列名
            column_mapping = {
                'cohort': 'cohort_group',
                'cohort_name': 'cohort_group', 
                'period': 'period_number',
                'period_num': 'period_number',
                'retention': 'retention_rate',
                'rate': 'retention_rate'
            }
            data = data.rename(columns=column_mapping)

            # 确保必要列存在
            required_cols = ['cohort_group', 'period_number', 'retention_rate']
            if not all(col in data.columns for col in required_cols):
                return self._create_empty_chart(
                    t('charts.retention_heatmap_title', 'Retention Heatmap'), 
                    f"{t('charts.missing_required_columns', 'Missing required columns')}: {required_cols}"
                )

            # 清理和转换数据
            data = data[required_cols].copy()
            data = data.dropna()
            
            # 确保数据类型正确
            data['period_number'] = pd.to_numeric(data['period_number'], errors='coerce')
            data['retention_rate'] = pd.to_numeric(data['retention_rate'], errors='coerce')
            data = data.dropna()

            if data.empty:
                return self._create_empty_chart(
                    t('charts.retention_heatmap_title', 'Retention Heatmap'), 
                    t('charts.no_valid_retention_data', 'No valid retention data')
                )

            # 创建热力图数据
            heatmap_data = data.pivot(
                index='cohort_group',
                columns='period_number', 
                values='retention_rate'
            ).fillna(0.0)

            if heatmap_data.empty:
                return self._create_empty_chart(
                    t('charts.retention_heatmap_title', 'Retention Heatmap'), 
                    t('charts.cannot_generate_heatmap', 'Cannot generate heatmap data')
                )

        except Exception as e:
            return self._create_empty_chart(
                t('charts.retention_heatmap_title', 'Retention Heatmap'), 
                f"{t('charts.data_processing_error', 'Data processing error')}: {str(e)}"
            )

        # 创建热力图
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=[f'{t("charts.period_label", "Period")} {i}' for i in heatmap_data.columns],
            y=heatmap_data.index,
            colorscale='RdYlBu_r',
            zmin=0, zmax=1,
            hovertemplate=f'{t("charts.cohort_label", "Cohort")}: %{{y}}<br>' +
                         f'{t("charts.period_label", "Period")}: %{{x}}<br>' +
                         f'{t("charts.retention_rate_label", "Retention Rate")}: %{{z:.1%}}<br>' +
                         '<extra></extra>',
            colorbar=dict(title=t("charts.retention_rate_label", "Retention Rate"), tickformat=".0%")
        ))

        # 添加数值标签
        annotations = []
        for i, cohort in enumerate(heatmap_data.index):
            for j, period in enumerate(heatmap_data.columns):
                value = heatmap_data.iloc[i, j]
                if value > 0:
                    annotations.append(dict(
                        x=j, y=i,
                        text=f'{value:.1%}',
                        showarrow=False,
                        font=dict(color='white' if value < 0.5 else 'black', size=10)
                    ))

        fig.update_layout(
            title=t('charts.retention_heatmap_title', 'User Retention Heatmap'),
            xaxis_title=t('charts.period_label', 'Period'),
            yaxis_title=t('charts.user_cohort_label', 'User Cohort'),
            annotations=annotations,
            height=400 + len(heatmap_data.index) * 20,
            template='plotly_white'
        )

        return fig
    
    def create_funnel_chart(self, data) -> go.Figure:
        """
        创建转化漏斗图表

        Args:
            data: 漏斗数据，可以是DataFrame、ConversionFunnel对象或字典

        Returns:
            plotly.graph_objects.Figure: 转化漏斗图表
        """
        # 安全地检查和转换数据
        if data is None:
            return self._create_empty_chart(
                t('charts.funnel_chart_title', 'Conversion Funnel Chart'), 
                t('charts.no_conversion_data', 'No conversion data available')
            )

        # 如果是ConversionFunnel对象，转换为DataFrame
        if hasattr(data, 'steps') and hasattr(data, 'funnel_name'):
            try:
                if not data.steps or len(data.steps) == 0:
                    return self._create_empty_chart(
                        t('charts.funnel_chart_title', 'Conversion Funnel Chart'), 
                        t('charts.funnel_steps_empty', 'Funnel steps are empty')
                    )

                # 从ConversionFunnel对象提取数据
                funnel_data = []
                for step in data.steps:
                    funnel_data.append({
                        'step_name': step.step_name,
                        'user_count': step.total_users,
                        'conversion_rate': step.conversion_rate,
                        'step_order': step.step_order
                    })
                data = pd.DataFrame(funnel_data)
            except Exception as e:
                return self._create_empty_chart(
                    t('charts.funnel_chart_title', 'Conversion Funnel Chart'), 
                    f"{t('charts.conversion_funnel_error', 'ConversionFunnel conversion failed')}: {str(e)}"
                )

        # 如果是字典，尝试转换为DataFrame
        elif isinstance(data, dict):
            try:
                if len(data) == 0:
                    return self._create_empty_chart(
                        t('charts.funnel_chart_title', 'Conversion Funnel Chart'), 
                        t('charts.conversion_data_empty', 'Conversion data is empty')
                    )
                data = pd.DataFrame(data)
            except Exception as e:
                return self._create_empty_chart(
                    t('charts.funnel_chart_title', 'Conversion Funnel Chart'), 
                    f"{t('charts.dict_conversion_error', 'Dictionary conversion failed')}: {str(e)}"
                )

        # 如果是列表，尝试转换为DataFrame
        elif isinstance(data, list):
            try:
                if len(data) == 0:
                    return self._create_empty_chart(
                        t('charts.funnel_chart_title', 'Conversion Funnel Chart'), 
                        t('charts.conversion_data_list_empty', 'Conversion data list is empty')
                    )
                data = pd.DataFrame(data)
            except Exception as e:
                return self._create_empty_chart(
                    t('charts.funnel_chart_title', 'Conversion Funnel Chart'), 
                    f"{t('charts.list_conversion_error', 'List conversion failed')}: {str(e)}"
                )

        # 如果是DataFrame，检查是否为空
        elif isinstance(data, pd.DataFrame):
            if data.empty:
                return self._create_empty_chart(
                    t('charts.funnel_chart_title', 'Conversion Funnel Chart'), 
                    t('charts.conversion_dataframe_empty', 'Conversion data DataFrame is empty')
                )

        # 如果是其他类型，返回错误
        else:
            return self._create_empty_chart(
                t('charts.funnel_chart_title', 'Conversion Funnel Chart'), 
                f"{t('charts.unsupported_data_type', 'Unsupported data type')}: {type(data)}"
            )
            
        # 确保必要的列存在
        required_columns = ['step_name', 'user_count']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"缺少必要的列: {missing_columns}")
        
        # 按步骤顺序排序
        data = data.copy()
        if 'step_order' not in data.columns:
            data['step_order'] = range(len(data))
        data = data.sort_values('step_order')
        
        # 计算转化率（如果没有提供）
        if 'conversion_rate' not in data.columns:
            data['conversion_rate'] = data['user_count'] / data['user_count'].iloc[0]
        
        # 创建漏斗图
        fig = go.Figure()
        
        # 添加漏斗图
        fig.add_trace(go.Funnel(
            y=data['step_name'],
            x=data['user_count'],
            textinfo="value+percent initial",
            hovertemplate=f'{t("charts.step_label", "Step")}: %{{y}}<br>' +
                         f'{t("charts.user_count_label", "User Count")}: %{{x}}<br>' +
                         f'{t("charts.conversion_rate_label", "Conversion Rate")}: %{{percentInitial}}<br>' +
                         '<extra></extra>',
            marker=dict(
                color=self.default_colors[:len(data)],
                line=dict(width=2, color='white')
            )
        ))
        
        fig.update_layout(
            title=t('charts.funnel_chart_title', 'Conversion Funnel Analysis'),
            height=500,
            template='plotly_white'
        )
        
        return fig
    
    def create_event_distribution_chart(self, data: pd.DataFrame) -> go.Figure:
        """
        创建事件分布图表
        
        Args:
            data: 包含事件数据的DataFrame，需要包含event_name列
            
        Returns:
            plotly.graph_objects.Figure: 事件分布图表
        """
        if data.empty:
            return self._create_empty_chart(
                t('charts.event_distribution_title', 'Event Distribution Chart'), 
                t('charts.no_event_data', 'No event data available')
            )
            
        # 确保必要的列存在
        if 'event_name' not in data.columns:
            raise ValueError("缺少必要的列: event_name")
        
        # 统计事件分布
        event_counts = data['event_name'].value_counts()
        
        # 创建饼图显示事件分布
        fig = go.Figure(data=[go.Pie(
            labels=event_counts.index,
            values=event_counts.values,
            hole=0.3,
            hovertemplate='<b>%{label}</b><br>' +
                         f'{t("charts.event_count_label", "Event Count")}: %{{value}}<br>' +
                         f'{t("charts.percentage_label", "Percentage")}: %{{percent}}<br>' +
                         '<extra></extra>',
            textinfo='label+percent',
            textposition='auto',
            marker=dict(
                colors=self.default_colors[:len(event_counts)],
                line=dict(color='white', width=2)
            )
        )])
        
        fig.update_layout(
            title=t('charts.event_distribution_title', 'Event Type Distribution'),
            height=500,
            template='plotly_white',
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.01
            )
        )
        
        return fig
    
    def _create_empty_chart(self, title: str, message: str) -> go.Figure:
        """
        创建空图表占位符
        
        Args:
            title: 图表标题
            message: 显示消息
            
        Returns:
            plotly.graph_objects.Figure: 空图表
        """
        fig = go.Figure()
        
        fig.add_annotation(
            x=0.5, y=0.5,
            text=message,
            showarrow=False,
            font=dict(size=16, color='gray'),
            xref="paper", yref="paper"
        )
        
        fig.update_layout(
            title=title,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=400,
            template='plotly_white'
        )
        
        return fig
    
    def create_multi_metric_dashboard(self, metrics: Dict[str, Any]) -> go.Figure:
        """
        创建多指标仪表板
        
        Args:
            metrics: 包含各种指标的字典
            
        Returns:
            plotly.graph_objects.Figure: 多指标仪表板
        """
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                t('charts.event_trends_label', 'Event Trends'), 
                t('charts.user_activity_label', 'User Activity'), 
                t('charts.conversion_rate_label', 'Conversion Rate'), 
                t('charts.retention_rate_label', 'Retention Rate')
            ),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 如果有事件趋势数据
        if 'event_trends' in metrics and not metrics['event_trends'].empty:
            event_data = metrics['event_trends']
            fig.add_trace(
                go.Scatter(
                    x=event_data.get('date', []),
                    y=event_data.get('count', []),
                    mode='lines',
                    name=t('charts.event_count_label', 'Event Count'),
                    line=dict(color=self.default_colors[0])
                ),
                row=1, col=1
            )
        
        # 如果有用户活跃度数据
        if 'user_activity' in metrics and not metrics['user_activity'].empty:
            activity_data = metrics['user_activity']
            fig.add_trace(
                go.Bar(
                    x=activity_data.get('date', []),
                    y=activity_data.get('active_users', []),
                    name=t('charts.active_users_label', 'Active Users'),
                    marker_color=self.default_colors[1]
                ),
                row=1, col=2
            )
        
        # 如果有转化率数据
        if 'conversion_rates' in metrics:
            conversion_data = metrics['conversion_rates']
            fig.add_trace(
                go.Scatter(
                    x=list(conversion_data.keys()),
                    y=list(conversion_data.values()),
                    mode='lines+markers',
                    name=t('charts.conversion_rate_label', 'Conversion Rate'),
                    line=dict(color=self.default_colors[2])
                ),
                row=2, col=1
            )
        
        # 如果有留存率数据
        if 'retention_rates' in metrics:
            retention_data = metrics['retention_rates']
            fig.add_trace(
                go.Bar(
                    x=list(retention_data.keys()),
                    y=list(retention_data.values()),
                    name=t('charts.retention_rate_label', 'Retention Rate'),
                    marker_color=self.default_colors[3]
                ),
                row=2, col=2
            )
        
        fig.update_layout(
            title=t('charts.dashboard_title', 'Data Analysis Dashboard'),
            height=600,
            showlegend=False,
            template='plotly_white'
        )
        
        return fig