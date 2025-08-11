"""
ChartGenerator类的测试用例
测试基础图表生成功能，包括事件时间线、留存热力图和转化漏斗图表
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
from visualization.chart_generator import ChartGenerator


class TestChartGenerator:
    """ChartGenerator类的测试用例"""
    
    def setup_method(self):
        """测试前的设置"""
        self.chart_generator = ChartGenerator()
        
    def create_sample_event_data(self) -> pd.DataFrame:
        """创建示例事件数据"""
        dates = pd.date_range('2024-01-01', periods=7, freq='D')
        events = ['page_view', 'sign_up', 'purchase', 'logout']
        
        data = []
        for date in dates:
            for event in events:
                # 为每个事件类型生成随机数量的记录
                count = np.random.randint(10, 100)
                for _ in range(count):
                    data.append({
                        'event_name': event,
                        'event_date': date.strftime('%Y%m%d'),
                        'event_timestamp': int(date.timestamp() * 1000000),  # 微秒
                        'user_pseudo_id': f'user_{np.random.randint(1, 1000)}'
                    })
        
        return pd.DataFrame(data)
    
    def create_sample_retention_data(self) -> pd.DataFrame:
        """创建示例留存数据"""
        cohorts = ['2024-01-01', '2024-01-08', '2024-01-15', '2024-01-22']
        periods = range(0, 8)  # 0-7期
        
        data = []
        for cohort in cohorts:
            for period in periods:
                # 模拟留存率递减
                retention_rate = max(0.1, 1.0 - (period * 0.15) + np.random.normal(0, 0.05))
                retention_rate = min(1.0, max(0.0, retention_rate))
                
                data.append({
                    'cohort_group': cohort,
                    'period_number': period,
                    'retention_rate': retention_rate
                })
        
        return pd.DataFrame(data)
    
    def create_sample_funnel_data(self) -> pd.DataFrame:
        """创建示例漏斗数据"""
        steps = [
            {'step_name': '访问首页', 'user_count': 10000, 'step_order': 0},
            {'step_name': '浏览产品', 'user_count': 7500, 'step_order': 1},
            {'step_name': '添加购物车', 'user_count': 3000, 'step_order': 2},
            {'step_name': '开始结账', 'user_count': 1500, 'step_order': 3},
            {'step_name': '完成购买', 'user_count': 1200, 'step_order': 4}
        ]
        
        return pd.DataFrame(steps)
    
    def test_chart_generator_initialization(self):
        """测试ChartGenerator初始化"""
        generator = ChartGenerator()
        assert generator is not None
        assert len(generator.default_colors) == 10
        assert generator.default_colors[0] == '#1f77b4'
    
    def test_create_event_timeline_with_valid_data(self):
        """测试使用有效数据创建事件时间线图表"""
        data = self.create_sample_event_data()
        
        fig = self.chart_generator.create_event_timeline(data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '事件时间线分析'
        assert fig.layout.xaxis.title.text == '日期'
        assert fig.layout.yaxis.title.text == '事件数量'
        assert len(fig.data) > 0  # 应该有数据轨迹
    
    def test_create_event_timeline_with_empty_data(self):
        """测试使用空数据创建事件时间线图表"""
        empty_data = pd.DataFrame()
        
        fig = self.chart_generator.create_event_timeline(empty_data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '事件时间线图表'
        assert len(fig.layout.annotations) == 1
        assert '暂无事件数据' in fig.layout.annotations[0].text
    
    def test_create_event_timeline_missing_columns(self):
        """测试缺少必要列时的错误处理"""
        invalid_data = pd.DataFrame({'invalid_column': [1, 2, 3]})
        
        with pytest.raises(ValueError) as excinfo:
            self.chart_generator.create_event_timeline(invalid_data)
        
        assert "缺少必要的列" in str(excinfo.value)
    
    def test_create_retention_heatmap_with_valid_data(self):
        """测试使用有效数据创建留存热力图"""
        data = self.create_sample_retention_data()
        
        fig = self.chart_generator.create_retention_heatmap(data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '用户留存热力图'
        assert fig.layout.xaxis.title.text == '时期'
        assert fig.layout.yaxis.title.text == '用户队列'
        assert len(fig.data) == 1
        assert isinstance(fig.data[0], go.Heatmap)
    
    def test_create_retention_heatmap_with_empty_data(self):
        """测试使用空数据创建留存热力图"""
        empty_data = pd.DataFrame()
        
        fig = self.chart_generator.create_retention_heatmap(empty_data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '留存热力图'
        assert len(fig.layout.annotations) == 1
        assert '暂无留存数据' in fig.layout.annotations[0].text
    
    def test_create_retention_heatmap_missing_columns(self):
        """测试留存热力图缺少必要列时的错误处理"""
        invalid_data = pd.DataFrame({'invalid_column': [1, 2, 3]})
        
        with pytest.raises(ValueError) as excinfo:
            self.chart_generator.create_retention_heatmap(invalid_data)
        
        assert "缺少必要的列" in str(excinfo.value)
    
    def test_create_funnel_chart_with_valid_data(self):
        """测试使用有效数据创建转化漏斗图表"""
        data = self.create_sample_funnel_data()
        
        fig = self.chart_generator.create_funnel_chart(data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '转化漏斗分析'
        assert len(fig.data) == 1
        assert isinstance(fig.data[0], go.Funnel)
    
    def test_create_funnel_chart_with_empty_data(self):
        """测试使用空数据创建转化漏斗图表"""
        empty_data = pd.DataFrame()
        
        fig = self.chart_generator.create_funnel_chart(empty_data)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '转化漏斗图'
        assert len(fig.layout.annotations) == 1
        assert '暂无转化数据' in fig.layout.annotations[0].text
    
    def test_create_funnel_chart_missing_columns(self):
        """测试转化漏斗图缺少必要列时的错误处理"""
        invalid_data = pd.DataFrame({'invalid_column': [1, 2, 3]})
        
        with pytest.raises(ValueError) as excinfo:
            self.chart_generator.create_funnel_chart(invalid_data)
        
        assert "缺少必要的列" in str(excinfo.value)
    
    def test_create_funnel_chart_auto_conversion_rate(self):
        """测试漏斗图自动计算转化率功能"""
        data = pd.DataFrame({
            'step_name': ['步骤1', '步骤2', '步骤3'],
            'user_count': [1000, 800, 600],
            'step_order': [0, 1, 2]
        })
        
        fig = self.chart_generator.create_funnel_chart(data)
        
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        # 验证转化率计算正确
        funnel_data = fig.data[0]
        assert funnel_data.x[0] == 1000
        assert funnel_data.x[1] == 800
        assert funnel_data.x[2] == 600
    
    def test_create_multi_metric_dashboard_with_all_metrics(self):
        """测试创建包含所有指标的多指标仪表板"""
        metrics = {
            'event_trends': pd.DataFrame({
                'date': pd.date_range('2024-01-01', periods=7),
                'count': [100, 120, 110, 130, 125, 140, 135]
            }),
            'user_activity': pd.DataFrame({
                'date': pd.date_range('2024-01-01', periods=7),
                'active_users': [50, 60, 55, 65, 62, 70, 68]
            }),
            'conversion_rates': {
                '注册转化': 0.15,
                '购买转化': 0.08,
                '复购转化': 0.25
            },
            'retention_rates': {
                '1日留存': 0.80,
                '7日留存': 0.45,
                '30日留存': 0.25
            }
        }
        
        fig = self.chart_generator.create_multi_metric_dashboard(metrics)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '数据分析仪表板'
        assert len(fig.data) == 4  # 四个子图的数据
    
    def test_create_multi_metric_dashboard_with_empty_metrics(self):
        """测试创建空指标的多指标仪表板"""
        empty_metrics = {}
        
        fig = self.chart_generator.create_multi_metric_dashboard(empty_metrics)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == '数据分析仪表板'
        # 即使没有数据，也应该创建基本的图表结构
    
    def test_create_empty_chart(self):
        """测试创建空图表占位符"""
        fig = self.chart_generator._create_empty_chart("测试标题", "测试消息")
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == "测试标题"
        assert len(fig.layout.annotations) == 1
        assert fig.layout.annotations[0].text == "测试消息"
    
    def test_event_timeline_data_processing(self):
        """测试事件时间线数据处理逻辑"""
        # 创建包含重复事件的数据
        data = pd.DataFrame({
            'event_name': ['page_view', 'page_view', 'sign_up', 'sign_up'],
            'event_date': ['20240101', '20240101', '20240101', '20240102'],
            'event_timestamp': [1704067200000000, 1704067260000000, 1704067320000000, 1704153600000000],
            'user_pseudo_id': ['user1', 'user2', 'user3', 'user4']
        })
        
        fig = self.chart_generator.create_event_timeline(data)
        
        assert isinstance(fig, go.Figure)
        # 应该有两种事件类型的轨迹
        assert len(fig.data) == 2
        
        # 验证数据聚合正确
        page_view_trace = next(trace for trace in fig.data if trace.name == 'page_view')
        sign_up_trace = next(trace for trace in fig.data if trace.name == 'sign_up')
        
        assert page_view_trace is not None
        assert sign_up_trace is not None
    
    def test_retention_heatmap_annotations(self):
        """测试留存热力图注释功能"""
        data = pd.DataFrame({
            'cohort_group': ['2024-01-01', '2024-01-01'],
            'period_number': [0, 1],
            'retention_rate': [1.0, 0.8]
        })
        
        fig = self.chart_generator.create_retention_heatmap(data)
        
        assert isinstance(fig, go.Figure)
        # 应该有注释显示百分比
        assert len(fig.layout.annotations) == 2
        assert '100.0%' in fig.layout.annotations[0].text
        assert '80.0%' in fig.layout.annotations[1].text


if __name__ == '__main__':
    pytest.main([__file__, '-v'])