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
            return self._create_empty_chart("事件时间线图表", "暂无事件数据")
            
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
                             '日期: %{x}<br>' +
                             '事件数量: %{y}<br>' +
                             '<extra></extra>'
            ))
        
        # 设置图表布局
        fig.update_layout(
            title='事件时间线分析',
            xaxis_title='日期',
            yaxis_title='事件数量',
            hovermode='x unified',
            showlegend=True,
            height=500,
            template='plotly_white'
        )
        
        return fig
    
    def create_retention_heatmap(self, data: pd.DataFrame) -> go.Figure:
        """
        创建留存热力图
        
        Args:
            data: 留存数据DataFrame，需要包含cohort_group, period_number, retention_rate列
            
        Returns:
            plotly.graph_objects.Figure: 留存热力图
        """
        if data.empty:
            return self._create_empty_chart("留存热力图", "暂无留存数据")
            
        # 确保必要的列存在
        required_columns = ['cohort_group', 'period_number', 'retention_rate']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValueError(f"缺少必要的列: {missing_columns}")
        
        # 创建透视表用于热力图
        heatmap_data = data.pivot(
            index='cohort_group', 
            columns='period_number', 
            values='retention_rate'
        )
        
        # 创建热力图
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=[f'第{i}期' for i in heatmap_data.columns],
            y=heatmap_data.index,
            colorscale='RdYlBu_r',
            hoverongaps=False,
            hovertemplate='队列: %{y}<br>' +
                         '时期: %{x}<br>' +
                         '留存率: %{z:.1%}<br>' +
                         '<extra></extra>',
            colorbar=dict(
                title="留存率",
                tickformat=".0%"
            )
        ))
        
        # 在每个单元格中显示数值
        annotations = []
        for i, cohort in enumerate(heatmap_data.index):
            for j, period in enumerate(heatmap_data.columns):
                value = heatmap_data.iloc[i, j]
                if not pd.isna(value):
                    annotations.append(
                        dict(
                            x=j, y=i,
                            text=f'{value:.1%}',
                            showarrow=False,
                            font=dict(color='white' if value < 0.5 else 'black')
                        )
                    )
        
        fig.update_layout(
            title='用户留存热力图',
            xaxis_title='时期',
            yaxis_title='用户队列',
            annotations=annotations,
            height=500,
            template='plotly_white'
        )
        
        return fig
    
    def create_funnel_chart(self, data: pd.DataFrame) -> go.Figure:
        """
        创建转化漏斗图表
        
        Args:
            data: 漏斗数据DataFrame，需要包含step_name, user_count, conversion_rate列
            
        Returns:
            plotly.graph_objects.Figure: 转化漏斗图表
        """
        if data.empty:
            return self._create_empty_chart("转化漏斗图", "暂无转化数据")
            
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
            hovertemplate='步骤: %{y}<br>' +
                         '用户数: %{x}<br>' +
                         '转化率: %{percentInitial}<br>' +
                         '<extra></extra>',
            marker=dict(
                color=self.default_colors[:len(data)],
                line=dict(width=2, color='white')
            )
        ))
        
        fig.update_layout(
            title='转化漏斗分析',
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
            return self._create_empty_chart("事件分布图", "暂无事件数据")
            
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
                         '事件数量: %{value}<br>' +
                         '占比: %{percent}<br>' +
                         '<extra></extra>',
            textinfo='label+percent',
            textposition='auto',
            marker=dict(
                colors=self.default_colors[:len(event_counts)],
                line=dict(color='white', width=2)
            )
        )])
        
        fig.update_layout(
            title='事件类型分布',
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
            subplot_titles=('事件趋势', '用户活跃度', '转化率', '留存率'),
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
                    name='事件数量',
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
                    name='活跃用户',
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
                    name='转化率',
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
                    name='留存率',
                    marker_color=self.default_colors[3]
                ),
                row=2, col=2
            )
        
        fig.update_layout(
            title='数据分析仪表板',
            height=600,
            showlegend=False,
            template='plotly_white'
        )
        
        return fig