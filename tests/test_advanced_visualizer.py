"""
AdvancedVisualizer类的测试用例
测试高级可视化功能，包括用户行为流程图、分群散点图、特征雷达图和交互式图表
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from visualization.advanced_visualizer import AdvancedVisualizer


class TestAdvancedVisualizer:
    """AdvancedVisualizer类的测试用例"""
    
    def setup_method(self):
        """测试前的设置"""
        self.visualizer = AdvancedVisualizer()
        
    def create_sample_flow_data(self) -> pd.DataFrame:
        """创建示例流程数据"""
        flow_data = [
            {'source': '首页', 'target': '产品页', 'value': 1000},
            {'source': '首页', 'target': '关于我们', 'value': 200},
            {'source': '产品页', 'target': '购物车', 'value': 300},
            {'source': '产品页', 'target': '产品详情', 'value': 500},
            {'source': '购物车', 'target': '结账', 'value': 150},
            {'source': '产品详情', 'target': '购物车', 'value': 200},
            {'source': '结账', 'target': '支付完成', 'value': 120}
        ]
        return pd.DataFrame(flow_data)
    
    def create_sample_segment_data(self) -> pd.DataFrame:
        """创建示例分群数据"""
        np.random.seed(42)
        segments = ['高价值用户', '活跃用户', '新用户', '流失用户']
        data = []
        
        for i, segment in enumerate(segments):
            # 为每个分群生成不同的特征分布
            n_users = 50
            x_base = i * 2
            y_base = i * 1.5
            
            for j in range(n_users):
                data.append({
                    'user_id': f'user_{i}_{j}',
                    'segment': segment,
                    'x_feature': x_base + np.random.normal(0, 0.5),
                    'y_feature': y_base + np.random.normal(0, 0.5)
                })
        
        return pd.DataFrame(data)
    
    def create_sample_feature_data(self) -> pd.DataFrame:
        """创建示例特征数据"""
        segments = ['高价值用户', '活跃用户', '新用户']
        features = ['活跃度', '消费金额', '使用频率', '留存率', '推荐度']
        
        data = []
        for segment in segments:
            for feature in features:
                # 为不同分群生成不同的特征值
                if segment == '高价值用户':
                    value = np.random.uniform(0.7, 1.0)
                elif segment == '活跃用户':
                    value = np.random.uniform(0.5, 0.8)
                else:  # 新用户
                    value = np.random.uniform(0.2, 0.6)
                
                data.append({
                    'segment': segment,
                    'feature_name': feature,
                    'feature_value': value
                })
        
        return pd.DataFrame(data)
    
    def create_sample_drill_down_data(self) -> pd.DataFrame:
        """创建示例钻取数据"""
        categories = ['电子产品', '服装', '家居']
        subcategories = {
            '电子产品': ['手机', '电脑', '耳机'],
            '服装': ['上衣', '裤子', '鞋子'],
            '家居': ['家具', '装饰', '厨具']
        }
        
        data = []
        for category in categories:
            for subcategory in subcategories[category]:
                value = np.random.randint(100, 1000)
                data.append({
                    'category': category,
                    'subcategory': subcategory,
                    'value': value
                })
        
        return pd.DataFrame(data)
    
    def create_sample_cohort_data(self) -> pd.DataFrame:
        """创建示例队列数据"""
        cohorts = ['2024-01-01', '2024-01-08', '2024-01-15']
        periods = range(0, 6)
        
        data = []
        for cohort in cohorts:
            for period in periods:
                # 模拟留存率递减
                retention_rate = max(0.1, 1.0 - (period * 0.15) + np.random.normal(0, 0.05))
                retention_rate = min(1.0, max(0.0, retention_rate))
                
                data.append({
                    'cohort_group': cohort,
                    'period_number': period,
                    'metric_value': retention_rate,
                    'metric_type': '留存率'
                })
        
        return pd.DataFrame(data)
    
    def create_sample_path_data(self) -> pd.DataFrame:
        """创建示例路径数据"""
        paths = [
            {'from_page': '首页', 'to_page': '产品列表', 'transition_count': 500},
            {'from_page': '首页', 'to_page': '搜索页', 'transition_count': 300},
            {'from_page': '产品列表', 'to_page': '产品详情', 'transition_count': 400},
            {'from_page': '搜索页', 'to_page': '产品详情', 'transition_count': 200},
            {'from_page': '产品详情', 'to_page': '购物车', 'transition_count': 250},
            {'from_page': '购物车', 'to_page': '结账页', 'transition_count': 150},
            {'from_page': '结账页', 'to_page': '支付完成', 'transition_count': 120}
        ]
        return pd.DataFrame(paths)
    
    def test_advanced_visualizer_initialization(self):
        """测试AdvancedVisualizer初始化"""
        visualizer = AdvancedVisualizer()
        assert visualizer is not None
        assert len(visualizer.default_colors) == 10
        assert len(visualizer.segment_colors) == 10
    
    def test_create_user_behavior_flow_with_valid_data(self):
        """测试使用有效数据创建用户行为流程图"""
        data = self.create_sample_flow_data()
        
        fig = self.visualizer.create_user_behavior_flow(data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '用户行为流程图'
        assert len(fig.data) == 1
        assert isinstance(fig.data[0], go.Sankey)
    
    def test_create_user_behavior_flow_with_empty_data(self):
        """测试使用空数据创建用户行为流程图"""
        empty_data = pd.DataFrame()
        
        fig = self.visualizer.create_user_behavior_flow(empty_data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '用户行为流程图'
        assert len(fig.layout.annotations) == 1
        assert '暂无流程数据' in fig.layout.annotations[0].text
    
    def test_create_user_behavior_flow_missing_columns(self):
        """测试流程图缺少必要列时的错误处理"""
        invalid_data = pd.DataFrame({'invalid_column': [1, 2, 3]})
        
        with pytest.raises(ValueError) as excinfo:
            self.visualizer.create_user_behavior_flow(invalid_data)
        
        assert "缺少必要的列" in str(excinfo.value)
    
    def test_create_user_segmentation_scatter_with_valid_data(self):
        """测试使用有效数据创建用户分群散点图"""
        data = self.create_sample_segment_data()
        
        fig = self.visualizer.create_user_segmentation_scatter(data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '用户分群散点图分析'
        assert fig.layout.xaxis.title.text == 'X特征值'
        assert fig.layout.yaxis.title.text == 'Y特征值'
        # 应该有分群数据 + 中心点数据
        assert len(fig.data) > 4  # 4个分群 + 4个中心点
    
    def test_create_user_segmentation_scatter_with_empty_data(self):
        """测试使用空数据创建用户分群散点图"""
        empty_data = pd.DataFrame()
        
        fig = self.visualizer.create_user_segmentation_scatter(empty_data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '用户分群散点图'
        assert len(fig.layout.annotations) == 1
        assert '暂无分群数据' in fig.layout.annotations[0].text
    
    def test_create_user_segmentation_scatter_missing_columns(self):
        """测试分群散点图缺少必要列时的错误处理"""
        invalid_data = pd.DataFrame({'invalid_column': [1, 2, 3]})
        
        with pytest.raises(ValueError) as excinfo:
            self.visualizer.create_user_segmentation_scatter(invalid_data)
        
        assert "缺少必要的列" in str(excinfo.value)
    
    def test_create_feature_radar_chart_with_valid_data(self):
        """测试使用有效数据创建特征雷达图"""
        data = self.create_sample_feature_data()
        
        fig = self.visualizer.create_feature_radar_chart(data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '用户分群特征雷达图'
        assert len(fig.data) == 3  # 3个分群
        
        # 验证所有轨迹都是雷达图类型
        for trace in fig.data:
            assert isinstance(trace, go.Scatterpolar)
    
    def test_create_feature_radar_chart_with_empty_data(self):
        """测试使用空数据创建特征雷达图"""
        empty_data = pd.DataFrame()
        
        fig = self.visualizer.create_feature_radar_chart(empty_data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '特征雷达图'
        assert len(fig.layout.annotations) == 1
        assert '暂无特征数据' in fig.layout.annotations[0].text
    
    def test_create_feature_radar_chart_missing_columns(self):
        """测试特征雷达图缺少必要列时的错误处理"""
        invalid_data = pd.DataFrame({'invalid_column': [1, 2, 3]})
        
        with pytest.raises(ValueError) as excinfo:
            self.visualizer.create_feature_radar_chart(invalid_data)
        
        assert "缺少必要的列" in str(excinfo.value)
    
    def test_create_interactive_drill_down_chart_with_valid_data(self):
        """测试使用有效数据创建交互式钻取图表"""
        data = self.create_sample_drill_down_data()
        drill_levels = ['category', 'subcategory']
        
        fig = self.visualizer.create_interactive_drill_down_chart(data, drill_levels)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '交互式数据钻取分析'
        assert len(fig.data) == 1
        assert isinstance(fig.data[0], go.Bar)
        
        # 验证有更新菜单
        assert len(fig.layout.updatemenus) == 1
        assert len(fig.layout.updatemenus[0].buttons) > 1
    
    def test_create_interactive_drill_down_chart_with_empty_data(self):
        """测试使用空数据创建交互式钻取图表"""
        empty_data = pd.DataFrame()
        drill_levels = ['category', 'subcategory']
        
        fig = self.visualizer.create_interactive_drill_down_chart(empty_data, drill_levels)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '交互式钻取图表'
        assert len(fig.layout.annotations) == 1
        assert '暂无钻取数据' in fig.layout.annotations[0].text
    
    def test_create_interactive_drill_down_chart_missing_columns(self):
        """测试钻取图表缺少必要列时的错误处理"""
        invalid_data = pd.DataFrame({'invalid_column': [1, 2, 3]})
        drill_levels = ['missing_column']
        
        with pytest.raises(ValueError) as excinfo:
            self.visualizer.create_interactive_drill_down_chart(invalid_data, drill_levels)
        
        assert "缺少钻取层级列" in str(excinfo.value)
    
    def test_create_cohort_analysis_heatmap_with_valid_data(self):
        """测试使用有效数据创建队列分析热力图"""
        data = self.create_sample_cohort_data()
        
        fig = self.visualizer.create_cohort_analysis_heatmap(data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '队列分析热力图'
        assert len(fig.data) == 1
        assert isinstance(fig.data[0], go.Heatmap)
    
    def test_create_cohort_analysis_heatmap_with_empty_data(self):
        """测试使用空数据创建队列分析热力图"""
        empty_data = pd.DataFrame()
        
        fig = self.visualizer.create_cohort_analysis_heatmap(empty_data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '队列分析热力图'
        assert len(fig.layout.annotations) == 1
        assert '暂无队列数据' in fig.layout.annotations[0].text
    
    def test_create_cohort_analysis_heatmap_missing_columns(self):
        """测试队列分析热力图缺少必要列时的错误处理"""
        invalid_data = pd.DataFrame({'invalid_column': [1, 2, 3]})
        
        with pytest.raises(ValueError) as excinfo:
            self.visualizer.create_cohort_analysis_heatmap(invalid_data)
        
        assert "缺少必要的列" in str(excinfo.value)
    
    def test_create_cohort_analysis_heatmap_multiple_metrics(self):
        """测试创建多指标队列分析热力图"""
        # 创建包含多个指标的数据
        data = self.create_sample_cohort_data()
        
        # 添加另一个指标
        additional_data = data.copy()
        additional_data['metric_type'] = '转化率'
        additional_data['metric_value'] = additional_data['metric_value'] * 0.5
        
        combined_data = pd.concat([data, additional_data], ignore_index=True)
        
        fig = self.visualizer.create_cohort_analysis_heatmap(combined_data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '多指标队列分析热力图'
        assert len(fig.data) == 2  # 两个指标
    
    def test_create_path_analysis_network_with_valid_data(self):
        """测试使用有效数据创建路径分析网络图"""
        data = self.create_sample_path_data()
        
        fig = self.visualizer.create_path_analysis_network(data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '用户路径分析网络图'
        assert len(fig.data) == 2  # 边和节点
        
        # 验证有边和节点轨迹
        edge_trace = fig.data[0]
        node_trace = fig.data[1]
        assert edge_trace.mode == 'lines'
        assert 'markers' in node_trace.mode
    
    def test_create_path_analysis_network_with_empty_data(self):
        """测试使用空数据创建路径分析网络图"""
        empty_data = pd.DataFrame()
        
        fig = self.visualizer.create_path_analysis_network(empty_data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '路径分析网络图'
        assert len(fig.layout.annotations) == 1
        assert '暂无路径数据' in fig.layout.annotations[0].text
    
    def test_create_path_analysis_network_missing_columns(self):
        """测试路径分析网络图缺少必要列时的错误处理"""
        invalid_data = pd.DataFrame({'invalid_column': [1, 2, 3]})
        
        with pytest.raises(ValueError) as excinfo:
            self.visualizer.create_path_analysis_network(invalid_data)
        
        assert "缺少必要的列" in str(excinfo.value)
    
    def test_create_empty_chart(self):
        """测试创建空图表占位符"""
        fig = self.visualizer._create_empty_chart("测试标题", "测试消息")
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == "测试标题"
        assert len(fig.layout.annotations) == 1
        assert fig.layout.annotations[0].text == "测试消息"
    
    def test_feature_radar_chart_missing_features(self):
        """测试雷达图处理缺失特征的情况"""
        # 创建不完整的特征数据
        incomplete_data = pd.DataFrame([
            {'segment': '用户A', 'feature_name': '特征1', 'feature_value': 0.8},
            {'segment': '用户A', 'feature_name': '特征2', 'feature_value': 0.6},
            {'segment': '用户B', 'feature_name': '特征1', 'feature_value': 0.7},
            # 用户B缺少特征2
        ])
        
        fig = self.visualizer.create_feature_radar_chart(incomplete_data)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # 两个用户分群
        
        # 验证缺失特征被填充为0
        user_b_trace = fig.data[1]
        assert 0 in user_b_trace.r  # 应该包含填充的0值
    
    def test_segmentation_scatter_center_calculation(self):
        """测试分群散点图中心点计算"""
        data = self.create_sample_segment_data()
        
        fig = self.visualizer.create_user_segmentation_scatter(data)
        
        # 验证有中心点标记
        center_traces = [trace for trace in fig.data if '中心' in trace.name]
        assert len(center_traces) == 4  # 4个分群的中心点
        
        # 验证中心点是钻石形状
        for center_trace in center_traces:
            assert center_trace.marker.symbol == 'diamond'
            assert center_trace.marker.size == 15


if __name__ == '__main__':
    pytest.main([__file__, '-v'])