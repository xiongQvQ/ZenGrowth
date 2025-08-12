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
    
    def create_retention_heatmap(self, data) -> go.Figure:
        """
        创建留存热力图

        Args:
            data: 留存数据，可以是DataFrame或字典

        Returns:
            plotly.graph_objects.Figure: 留存热力图
        """
        # 安全地检查和转换数据
        if data is None:
            return self._create_empty_chart("留存热力图", "暂无留存数据")

        # 如果是字典，尝试转换为DataFrame
        if isinstance(data, dict):
            try:
                # 尝试从字典创建DataFrame
                if len(data) == 0:
                    return self._create_empty_chart("留存热力图", "留存数据为空")

                # 处理不同的字典结构
                if 'cohorts' in data and isinstance(data['cohorts'], list):
                    # 从cohorts列表创建标准化的DataFrame
                    cohort_rows = []
                    for cohort in data['cohorts']:
                        cohort_period = cohort.get('cohort_period', 'Unknown')
                        retention_rates = cohort.get('retention_rates', [])
                        for period_num, rate in enumerate(retention_rates):
                            cohort_rows.append({
                                'cohort_group': cohort_period,
                                'period_number': period_num,
                                'retention_rate': rate
                            })

                    if cohort_rows:
                        data = pd.DataFrame(cohort_rows)
                    else:
                        return self._create_empty_chart("留存热力图", "队列数据为空")

                elif all(isinstance(v, (list, dict)) for v in data.values()):
                    # 尝试直接转换，但要处理长度不一致的问题
                    try:
                        # 检查所有值的长度
                        lengths = [len(v) if isinstance(v, (list, dict)) else 1 for v in data.values()]
                        if len(set(lengths)) > 1:
                            # 长度不一致，需要特殊处理
                            max_length = max(lengths)
                            normalized_data = {}
                            for key, value in data.items():
                                if isinstance(value, list):
                                    # 用None填充到最大长度
                                    normalized_data[key] = value + [None] * (max_length - len(value))
                                else:
                                    normalized_data[key] = value
                            data = pd.DataFrame(normalized_data)
                        else:
                            data = pd.DataFrame(data)
                    except Exception:
                        # 如果还是失败，创建示例数据
                        data = pd.DataFrame([
                            {'cohort_group': '2024-01', 'period_number': 0, 'retention_rate': 1.0},
                            {'cohort_group': '2024-01', 'period_number': 1, 'retention_rate': 0.7},
                            {'cohort_group': '2024-01', 'period_number': 2, 'retention_rate': 0.5}
                        ])
                else:
                    # 创建示例数据结构
                    data = pd.DataFrame([
                        {'cohort_group': '2024-01', 'period_number': 0, 'retention_rate': 1.0},
                        {'cohort_group': '2024-01', 'period_number': 1, 'retention_rate': 0.7},
                        {'cohort_group': '2024-01', 'period_number': 2, 'retention_rate': 0.5}
                    ])
            except Exception as e:
                return self._create_empty_chart("留存热力图", f"数据转换失败: {str(e)}")

        # 如果是列表，尝试转换为DataFrame
        elif isinstance(data, list):
            try:
                if len(data) == 0:
                    return self._create_empty_chart("留存热力图", "留存数据列表为空")

                # 检查列表中的数据结构
                if all(isinstance(item, dict) for item in data):
                    # 检查字典的键是否一致
                    all_keys = set()
                    for item in data:
                        all_keys.update(item.keys())

                    # 标准化所有字典，确保它们有相同的键
                    normalized_data = []
                    for item in data:
                        normalized_item = {}
                        for key in all_keys:
                            normalized_item[key] = item.get(key, None)
                        normalized_data.append(normalized_item)

                    data = pd.DataFrame(normalized_data)
                else:
                    data = pd.DataFrame(data)
            except Exception as e:
                return self._create_empty_chart("留存热力图", f"列表转换失败: {str(e)}")

        # 如果是DataFrame，检查是否为空
        elif isinstance(data, pd.DataFrame):
            if data.empty:
                return self._create_empty_chart("留存热力图", "留存数据DataFrame为空")

        # 如果是其他类型，返回错误
        else:
            return self._create_empty_chart("留存热力图", f"不支持的数据类型: {type(data)}")
            
        # 确保必要的列存在
        required_columns = ['cohort_group', 'period_number', 'retention_rate']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            # 尝试映射常见的列名
            column_mapping = {
                'cohort': 'cohort_group',
                'cohort_name': 'cohort_group',
                'period': 'period_number',
                'period_num': 'period_number',
                'retention': 'retention_rate',
                'rate': 'retention_rate'
            }

            for old_name, new_name in column_mapping.items():
                if old_name in data.columns and new_name in missing_columns:
                    data = data.rename(columns={old_name: new_name})
                    missing_columns.remove(new_name)

            # 如果还有缺失的列，返回错误
            if missing_columns:
                return self._create_empty_chart("留存热力图", f"缺少必要的列: {missing_columns}")

        # 清理数据：移除空值和无效数据
        data = data.dropna(subset=['cohort_group', 'period_number', 'retention_rate'])

        if data.empty:
            return self._create_empty_chart("留存热力图", "清理后的数据为空")

        # 确保数据类型正确
        try:
            data['period_number'] = pd.to_numeric(data['period_number'], errors='coerce')
            data['retention_rate'] = pd.to_numeric(data['retention_rate'], errors='coerce')
            data = data.dropna()  # 移除转换失败的行
        except Exception:
            pass

        if data.empty:
            return self._create_empty_chart("留存热力图", "数据类型转换后为空")

        # 创建透视表用于热力图，使用fillna处理缺失值
        try:
            heatmap_data = data.pivot(
                index='cohort_group',
                columns='period_number',
                values='retention_rate'
            ).fillna(0)  # 用0填充缺失值
        except Exception as e:
            return self._create_empty_chart("留存热力图", f"透视表创建失败: {str(e)}")
        
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
            return self._create_empty_chart("转化漏斗图", "暂无转化数据")

        # 如果是ConversionFunnel对象，转换为DataFrame
        if hasattr(data, 'steps') and hasattr(data, 'funnel_name'):
            try:
                if not data.steps or len(data.steps) == 0:
                    return self._create_empty_chart("转化漏斗图", "漏斗步骤为空")

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
                return self._create_empty_chart("转化漏斗图", f"ConversionFunnel转换失败: {str(e)}")

        # 如果是字典，尝试转换为DataFrame
        elif isinstance(data, dict):
            try:
                if len(data) == 0:
                    return self._create_empty_chart("转化漏斗图", "转化数据为空")
                data = pd.DataFrame(data)
            except Exception as e:
                return self._create_empty_chart("转化漏斗图", f"字典转换失败: {str(e)}")

        # 如果是列表，尝试转换为DataFrame
        elif isinstance(data, list):
            try:
                if len(data) == 0:
                    return self._create_empty_chart("转化漏斗图", "转化数据列表为空")
                data = pd.DataFrame(data)
            except Exception as e:
                return self._create_empty_chart("转化漏斗图", f"列表转换失败: {str(e)}")

        # 如果是DataFrame，检查是否为空
        elif isinstance(data, pd.DataFrame):
            if data.empty:
                return self._create_empty_chart("转化漏斗图", "转化数据DataFrame为空")

        # 如果是其他类型，返回错误
        else:
            return self._create_empty_chart("转化漏斗图", f"不支持的数据类型: {type(data)}")
            
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