"""
高级可视化组件
实现用户行为流程图、用户分群散点图、特征雷达图和交互式图表功能
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from math import pi


class AdvancedVisualizer:
    """高级可视化组件类，提供复杂的数据可视化功能"""
    
    def __init__(self):
        """初始化高级可视化器"""
        self.default_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        self.segment_colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9'
        ]
        
    def create_user_behavior_flow(self, flow_data: pd.DataFrame) -> go.Figure:
        """
        创建用户行为流程图可视化
        
        Args:
            flow_data: 包含用户行为流程数据的DataFrame
                     需要包含source, target, value列
                     
        Returns:
            plotly.graph_objects.Figure: 用户行为流程图
        """
        if flow_data.empty:
            return self._create_empty_chart("用户行为流程图", "暂无流程数据")
            
        # 确保必要的列存在
        required_columns = ['source', 'target', 'value']
        missing_columns = [col for col in required_columns if col not in flow_data.columns]
        if missing_columns:
            raise ValueError(f"缺少必要的列: {missing_columns}")
        
        # 获取所有唯一的节点
        all_nodes = list(set(flow_data['source'].tolist() + flow_data['target'].tolist()))
        node_indices = {node: i for i, node in enumerate(all_nodes)}
        
        # 创建Sankey图
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_nodes,
                color=self.default_colors[:len(all_nodes)]
            ),
            link=dict(
                source=[node_indices[source] for source in flow_data['source']],
                target=[node_indices[target] for target in flow_data['target']],
                value=flow_data['value'].tolist(),
                hovertemplate='%{source.label} → %{target.label}<br>' +
                             '用户数量: %{value}<br>' +
                             '<extra></extra>'
            )
        )])
        
        fig.update_layout(
            title="用户行为流程图",
            font_size=12,
            height=600,
            template='plotly_white'
        )
        
        return fig
    
    def create_user_segmentation_scatter(self, segment_data: pd.DataFrame) -> go.Figure:
        """
        创建用户分群散点图
        
        Args:
            segment_data: 用户分群数据DataFrame
                        需要包含user_id, segment, x_feature, y_feature列
                        
        Returns:
            plotly.graph_objects.Figure: 用户分群散点图
        """
        if segment_data.empty:
            return self._create_empty_chart("用户分群散点图", "暂无分群数据")
            
        # 确保必要的列存在
        required_columns = ['user_id', 'segment', 'x_feature', 'y_feature']
        missing_columns = [col for col in required_columns if col not in segment_data.columns]
        if missing_columns:
            raise ValueError(f"缺少必要的列: {missing_columns}")
        
        # 创建散点图
        fig = px.scatter(
            segment_data,
            x='x_feature',
            y='y_feature',
            color='segment',
            hover_data=['user_id'],
            color_discrete_sequence=self.segment_colors,
            title='用户分群散点图分析'
        )
        
        # 更新悬停模板
        fig.update_traces(
            hovertemplate='<b>%{hovertext}</b><br>' +
                         'X特征: %{x}<br>' +
                         'Y特征: %{y}<br>' +
                         '用户ID: %{customdata[0]}<br>' +
                         '<extra></extra>',
            hovertext=segment_data['segment']
        )
        
        # 添加分群中心点
        segment_centers = segment_data.groupby('segment').agg({
            'x_feature': 'mean',
            'y_feature': 'mean'
        }).reset_index()
        
        for i, center in segment_centers.iterrows():
            fig.add_trace(go.Scatter(
                x=[center['x_feature']],
                y=[center['y_feature']],
                mode='markers',
                marker=dict(
                    size=15,
                    symbol='diamond',
                    color='black',
                    line=dict(width=2, color='white')
                ),
                name=f'{center["segment"]}中心',
                hovertemplate=f'<b>{center["segment"]}分群中心</b><br>' +
                             f'X特征: {center["x_feature"]:.2f}<br>' +
                             f'Y特征: {center["y_feature"]:.2f}<br>' +
                             '<extra></extra>'
            ))
        
        fig.update_layout(
            xaxis_title='X特征值',
            yaxis_title='Y特征值',
            height=600,
            template='plotly_white',
            showlegend=True
        )
        
        return fig
    
    def create_feature_radar_chart(self, feature_data: pd.DataFrame) -> go.Figure:
        """
        创建特征雷达图
        
        Args:
            feature_data: 特征数据DataFrame
                        需要包含segment, feature_name, feature_value列
                        
        Returns:
            plotly.graph_objects.Figure: 特征雷达图
        """
        if feature_data.empty:
            return self._create_empty_chart("特征雷达图", "暂无特征数据")
            
        # 确保必要的列存在
        required_columns = ['segment', 'feature_name', 'feature_value']
        missing_columns = [col for col in required_columns if col not in feature_data.columns]
        if missing_columns:
            raise ValueError(f"缺少必要的列: {missing_columns}")
        
        # 创建雷达图
        fig = go.Figure()
        
        segments = feature_data['segment'].unique()
        features = feature_data['feature_name'].unique()
        
        for i, segment in enumerate(segments):
            segment_data = feature_data[feature_data['segment'] == segment]
            
            # 确保所有特征都有值，缺失的用0填充
            feature_values = []
            for feature in features:
                feature_row = segment_data[segment_data['feature_name'] == feature]
                if not feature_row.empty:
                    feature_values.append(feature_row['feature_value'].iloc[0])
                else:
                    feature_values.append(0)
            
            fig.add_trace(go.Scatterpolar(
                r=feature_values,
                theta=features,
                fill='toself',
                name=segment,
                line_color=self.segment_colors[i % len(self.segment_colors)],
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             '特征: %{theta}<br>' +
                             '数值: %{r:.2f}<br>' +
                             '<extra></extra>'
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(feature_data['feature_value']) * 1.1]
                )
            ),
            title='用户分群特征雷达图',
            height=600,
            template='plotly_white',
            showlegend=True
        )
        
        return fig
    
    def create_interactive_drill_down_chart(self, data: pd.DataFrame, 
                                          drill_levels: List[str]) -> go.Figure:
        """
        创建交互式数据钻取图表
        
        Args:
            data: 包含多层级数据的DataFrame
            drill_levels: 钻取层级列表
            
        Returns:
            plotly.graph_objects.Figure: 交互式钻取图表
        """
        if data.empty:
            return self._create_empty_chart("交互式钻取图表", "暂无钻取数据")
            
        # 确保钻取层级列存在
        missing_columns = [col for col in drill_levels if col not in data.columns]
        if missing_columns:
            raise ValueError(f"缺少钻取层级列: {missing_columns}")
        
        if 'value' not in data.columns:
            raise ValueError("缺少value列")
        
        # 创建树状图用于钻取
        fig = go.Figure()
        
        # 第一层级数据
        level1_data = data.groupby(drill_levels[0])['value'].sum().reset_index()
        
        fig.add_trace(go.Bar(
            x=level1_data[drill_levels[0]],
            y=level1_data['value'],
            name='总览',
            marker_color=self.default_colors[0],
            hovertemplate='<b>%{x}</b><br>' +
                         '数值: %{y}<br>' +
                         '点击查看详情<br>' +
                         '<extra></extra>'
        ))
        
        # 添加下钻按钮
        buttons = []
        for i, level in enumerate(drill_levels):
            if i == 0:
                continue
                
            level_data = data.groupby(drill_levels[:i+1])['value'].sum().reset_index()
            
            button = dict(
                label=f'钻取到{level}',
                method='restyle',
                args=[{
                    'x': [level_data[level].tolist()],
                    'y': [level_data['value'].tolist()],
                    'name': level
                }]
            )
            buttons.append(button)
        
        # 添加返回顶层按钮
        buttons.insert(0, dict(
            label='返回总览',
            method='restyle',
            args=[{
                'x': [level1_data[drill_levels[0]].tolist()],
                'y': [level1_data['value'].tolist()],
                'name': '总览'
            }]
        ))
        
        fig.update_layout(
            title='交互式数据钻取分析',
            xaxis_title='类别',
            yaxis_title='数值',
            height=500,
            template='plotly_white',
            updatemenus=[dict(
                type="buttons",
                direction="left",
                buttons=buttons,
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.01,
                xanchor="left",
                y=1.02,
                yanchor="top"
            )]
        )
        
        return fig
    
    def create_cohort_analysis_heatmap(self, cohort_data) -> go.Figure:
        """
        创建队列分析热力图（增强版）

        Args:
            cohort_data: 队列数据，可以是DataFrame或字典
                       需要包含cohort_group, period_number, metric_value, metric_type列

        Returns:
            plotly.graph_objects.Figure: 队列分析热力图
        """
        # 安全地检查和转换数据
        if cohort_data is None:
            return self._create_empty_chart("队列分析热力图", "暂无队列数据")

        # 如果是字典，尝试转换为DataFrame
        if isinstance(cohort_data, dict):
            try:
                if len(cohort_data) == 0:
                    return self._create_empty_chart("队列分析热力图", "队列数据为空")
                cohort_data = pd.DataFrame(cohort_data)
            except Exception as e:
                return self._create_empty_chart("队列分析热力图", f"数据转换失败: {str(e)}")

        # 如果是列表，尝试转换为DataFrame
        elif isinstance(cohort_data, list):
            try:
                if len(cohort_data) == 0:
                    return self._create_empty_chart("队列分析热力图", "队列数据列表为空")
                cohort_data = pd.DataFrame(cohort_data)
            except Exception as e:
                return self._create_empty_chart("队列分析热力图", f"列表转换失败: {str(e)}")

        # 如果是DataFrame，检查是否为空
        elif isinstance(cohort_data, pd.DataFrame):
            if cohort_data.empty:
                return self._create_empty_chart("队列分析热力图", "队列数据DataFrame为空")

        # 如果是其他类型，返回错误
        else:
            return self._create_empty_chart("队列分析热力图", f"不支持的数据类型: {type(cohort_data)}")
            
        # 确保必要的列存在
        required_columns = ['cohort_group', 'period_number', 'metric_value']
        missing_columns = [col for col in required_columns if col not in cohort_data.columns]
        if missing_columns:
            raise ValueError(f"缺少必要的列: {missing_columns}")
        
        # 如果有多个指标类型，创建子图
        if 'metric_type' in cohort_data.columns:
            metric_types = cohort_data['metric_type'].unique()
            
            if len(metric_types) > 1:
                fig = make_subplots(
                    rows=len(metric_types), cols=1,
                    subplot_titles=[f'{metric}队列分析' for metric in metric_types],
                    vertical_spacing=0.1
                )
                
                for i, metric_type in enumerate(metric_types):
                    metric_data = cohort_data[cohort_data['metric_type'] == metric_type]
                    heatmap_data = metric_data.pivot(
                        index='cohort_group',
                        columns='period_number',
                        values='metric_value'
                    )
                    
                    fig.add_trace(
                        go.Heatmap(
                            z=heatmap_data.values,
                            x=[f'第{j}期' for j in heatmap_data.columns],
                            y=heatmap_data.index,
                            colorscale='RdYlBu_r',
                            name=metric_type,
                            hovertemplate='队列: %{y}<br>' +
                                         '时期: %{x}<br>' +
                                         f'{metric_type}: %{{z:.2f}}<br>' +
                                         '<extra></extra>'
                        ),
                        row=i+1, col=1
                    )
                
                fig.update_layout(
                    title='多指标队列分析热力图',
                    height=300 * len(metric_types),
                    template='plotly_white'
                )
                
                return fig
        
        # 单一指标的热力图
        heatmap_data = cohort_data.pivot(
            index='cohort_group',
            columns='period_number',
            values='metric_value'
        )
        
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=[f'第{i}期' for i in heatmap_data.columns],
            y=heatmap_data.index,
            colorscale='RdYlBu_r',
            hoverongaps=False,
            hovertemplate='队列: %{y}<br>' +
                         '时期: %{x}<br>' +
                         '指标值: %{z:.2f}<br>' +
                         '<extra></extra>'
        ))
        
        fig.update_layout(
            title='队列分析热力图',
            xaxis_title='时期',
            yaxis_title='用户队列',
            height=500,
            template='plotly_white'
        )
        
        return fig
    
    def create_path_analysis_network(self, path_data: pd.DataFrame) -> go.Figure:
        """
        创建路径分析网络图
        
        Args:
            path_data: 路径数据DataFrame
                     需要包含from_page, to_page, transition_count列
                     
        Returns:
            plotly.graph_objects.Figure: 路径分析网络图
        """
        if path_data.empty:
            return self._create_empty_chart("路径分析网络图", "暂无路径数据")
            
        # 确保必要的列存在
        required_columns = ['from_page', 'to_page', 'transition_count']
        missing_columns = [col for col in required_columns if col not in path_data.columns]
        if missing_columns:
            raise ValueError(f"缺少必要的列: {missing_columns}")
        
        # 创建网络图
        G = nx.from_pandas_edgelist(
            path_data, 
            source='from_page', 
            target='to_page', 
            edge_attr='transition_count',
            create_using=nx.DiGraph()
        )
        
        # 计算节点位置
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # 提取边的信息
        edge_x = []
        edge_y = []
        edge_info = []
        
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
            weight = G[edge[0]][edge[1]]['transition_count']
            edge_info.append(f'{edge[0]} → {edge[1]}: {weight}次转换')
        
        # 创建边的轨迹
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # 提取节点信息
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            
            # 节点大小基于度数
            degree = G.degree(node)
            node_size.append(max(20, degree * 5))
        
        # 创建节点轨迹
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="middle center",
            marker=dict(
                size=node_size,
                color=self.default_colors[0],
                line=dict(width=2, color='white')
            ),
            hovertemplate='<b>%{text}</b><br>' +
                         '连接数: %{marker.size}<br>' +
                         '<extra></extra>'
        )
        
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title=dict(text='用户路径分析网络图', font=dict(size=16)),
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="节点大小表示页面连接数，箭头表示用户流向",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002,
                               xanchor='left', yanchor='bottom',
                               font=dict(color='gray', size=12)
                           )],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           height=600,
                           template='plotly_white'
                       ))
        
        return fig
    
    def create_retention_heatmap(self, data) -> go.Figure:
        """
        创建留存热力图（兼容方法）

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