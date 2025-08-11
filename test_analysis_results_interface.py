"""
分析结果展示界面集成测试
测试各个分析页面的功能和可视化组件集成
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from visualization.chart_generator import ChartGenerator
from visualization.advanced_visualizer import AdvancedVisualizer
from engines.event_analysis_engine import EventAnalysisEngine
from engines.retention_analysis_engine import RetentionAnalysisEngine
from engines.conversion_analysis_engine import ConversionAnalysisEngine
from engines.user_segmentation_engine import UserSegmentationEngine
from engines.path_analysis_engine import PathAnalysisEngine


class TestAnalysisResultsInterface:
    """分析结果展示界面测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        self.chart_generator = ChartGenerator()
        self.advanced_visualizer = AdvancedVisualizer()
        
        # 创建测试数据
        self.test_data = self._create_test_data()
    
    def _create_test_data(self):
        """创建测试用的GA4数据"""
        np.random.seed(42)
        
        # 生成测试事件数据
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        events = ['page_view', 'sign_up', 'login', 'purchase', 'search']
        platforms = ['WEB', 'MOBILE_APP', 'TABLET']
        
        data = []
        for i in range(1000):
            date = pd.Timestamp(np.random.choice(dates))
            event = np.random.choice(events)
            platform = np.random.choice(platforms)
            user_id = f"user_{np.random.randint(1, 100)}"
            
            data.append({
                'event_date': date.strftime('%Y%m%d'),
                'event_timestamp': int(date.timestamp() * 1000000),
                'event_name': event,
                'user_pseudo_id': user_id,
                'user_id': user_id,
                'platform': platform,
                'device': {'category': 'desktop'},
                'geo': {'country': 'US'},
                'traffic_source': {'source': 'google'},
                'event_params': [],
                'user_properties': []
            })
        
        return pd.DataFrame(data)
    
    def test_event_timeline_chart(self):
        """测试事件时间线图表生成"""
        print("🧪 测试事件时间线图表...")
        
        # 测试正常数据
        chart = self.chart_generator.create_event_timeline(self.test_data)
        assert chart is not None
        assert hasattr(chart, 'data')
        assert len(chart.data) > 0
        print("✅ 事件时间线图表生成成功")
        
        # 测试空数据
        empty_chart = self.chart_generator.create_event_timeline(pd.DataFrame())
        assert empty_chart is not None
        print("✅ 空数据处理正常")
    
    def test_retention_heatmap(self):
        """测试留存热力图生成"""
        print("🧪 测试留存热力图...")
        
        # 创建留存测试数据
        retention_data = pd.DataFrame({
            'cohort_group': ['2024-01-01', '2024-01-02', '2024-01-03'] * 5,
            'period_number': [0, 1, 2, 3, 4] * 3,
            'retention_rate': np.random.uniform(0.1, 1.0, 15)
        })
        
        chart = self.chart_generator.create_retention_heatmap(retention_data)
        assert chart is not None
        assert hasattr(chart, 'data')
        print("✅ 留存热力图生成成功")
    
    def test_funnel_chart(self):
        """测试转化漏斗图表生成"""
        print("🧪 测试转化漏斗图表...")
        
        # 创建漏斗测试数据
        funnel_data = pd.DataFrame({
            'step_name': ['访问首页', '浏览产品', '加入购物车', '完成购买'],
            'user_count': [1000, 800, 400, 100],
            'step_order': [0, 1, 2, 3]
        })
        
        chart = self.chart_generator.create_funnel_chart(funnel_data)
        assert chart is not None
        assert hasattr(chart, 'data')
        print("✅ 转化漏斗图表生成成功")
    
    def test_user_segmentation_scatter(self):
        """测试用户分群散点图"""
        print("🧪 测试用户分群散点图...")
        
        # 创建分群测试数据
        scatter_data = pd.DataFrame({
            'user_id': [f'user_{i}' for i in range(100)],
            'segment': [f'分群{i%4+1}' for i in range(100)],
            'x_feature': np.random.normal(0, 1, 100),
            'y_feature': np.random.normal(0, 1, 100)
        })
        
        chart = self.advanced_visualizer.create_user_segmentation_scatter(scatter_data)
        assert chart is not None
        assert hasattr(chart, 'data')
        print("✅ 用户分群散点图生成成功")
    
    def test_feature_radar_chart(self):
        """测试特征雷达图"""
        print("🧪 测试特征雷达图...")
        
        # 创建雷达图测试数据
        radar_data = pd.DataFrame({
            'segment': ['分群1', '分群1', '分群1', '分群2', '分群2', '分群2'],
            'feature_name': ['活跃度', '转化率', '留存率', '活跃度', '转化率', '留存率'],
            'feature_value': [0.8, 0.3, 0.6, 0.5, 0.7, 0.4]
        })
        
        chart = self.advanced_visualizer.create_feature_radar_chart(radar_data)
        assert chart is not None
        assert hasattr(chart, 'data')
        print("✅ 特征雷达图生成成功")
    
    def test_user_behavior_flow(self):
        """测试用户行为流程图"""
        print("🧪 测试用户行为流程图...")
        
        # 创建流程测试数据
        flow_data = pd.DataFrame({
            'source': ['首页', '首页', '产品页', '产品页', '购物车'],
            'target': ['产品页', '搜索页', '购物车', '详情页', '结算页'],
            'value': [100, 50, 80, 30, 60]
        })
        
        chart = self.advanced_visualizer.create_user_behavior_flow(flow_data)
        assert chart is not None
        assert hasattr(chart, 'data')
        print("✅ 用户行为流程图生成成功")
    
    def test_multi_metric_dashboard(self):
        """测试多指标仪表板"""
        print("🧪 测试多指标仪表板...")
        
        # 创建多指标测试数据
        metrics = {
            'event_trends': pd.DataFrame({
                'date': pd.date_range('2024-01-01', periods=10),
                'count': np.random.randint(100, 1000, 10)
            }),
            'user_activity': pd.DataFrame({
                'date': pd.date_range('2024-01-01', periods=10),
                'active_users': np.random.randint(50, 500, 10)
            }),
            'conversion_rates': {'步骤1': 0.8, '步骤2': 0.6, '步骤3': 0.4},
            'retention_rates': {'第1天': 1.0, '第7天': 0.7, '第30天': 0.3}
        }
        
        chart = self.chart_generator.create_multi_metric_dashboard(metrics)
        assert chart is not None
        assert hasattr(chart, 'data')
        print("✅ 多指标仪表板生成成功")
    
    def test_interactive_drill_down(self):
        """测试交互式钻取图表"""
        print("🧪 测试交互式钻取图表...")
        
        # 创建钻取测试数据
        drill_data = pd.DataFrame({
            'level1': ['类别A', '类别A', '类别B', '类别B'] * 5,
            'level2': ['子类1', '子类2', '子类1', '子类2'] * 5,
            'level3': ['项目1', '项目2', '项目3', '项目4'] * 5,
            'value': np.random.randint(10, 100, 20)
        })
        
        drill_levels = ['level1', 'level2', 'level3']
        chart = self.advanced_visualizer.create_interactive_drill_down_chart(drill_data, drill_levels)
        assert chart is not None
        assert hasattr(chart, 'data')
        print("✅ 交互式钻取图表生成成功")
    
    def test_cohort_analysis_heatmap(self):
        """测试队列分析热力图"""
        print("🧪 测试队列分析热力图...")
        
        # 创建队列测试数据
        cohort_data = pd.DataFrame({
            'cohort_group': ['2024-01-01', '2024-01-02', '2024-01-03'] * 5,
            'period_number': [0, 1, 2, 3, 4] * 3,
            'metric_value': np.random.uniform(0.1, 1.0, 15),
            'metric_type': ['留存率'] * 15
        })
        
        chart = self.advanced_visualizer.create_cohort_analysis_heatmap(cohort_data)
        assert chart is not None
        assert hasattr(chart, 'data')
        print("✅ 队列分析热力图生成成功")
    
    def test_path_analysis_network(self):
        """测试路径分析网络图"""
        print("🧪 测试路径分析网络图...")
        
        # 创建路径测试数据
        path_data = pd.DataFrame({
            'from_page': ['首页', '首页', '产品页', '产品页', '购物车'],
            'to_page': ['产品页', '搜索页', '购物车', '详情页', '结算页'],
            'transition_count': [100, 50, 80, 30, 60]
        })
        
        chart = self.advanced_visualizer.create_path_analysis_network(path_data)
        assert chart is not None
        assert hasattr(chart, 'data')
        print("✅ 路径分析网络图生成成功")
    
    def test_data_filtering_functionality(self):
        """测试数据筛选功能"""
        print("🧪 测试数据筛选功能...")
        
        # 测试事件类型筛选
        filtered_data = self.test_data[self.test_data['event_name'].isin(['page_view', 'purchase'])]
        assert len(filtered_data) > 0
        assert set(filtered_data['event_name'].unique()).issubset({'page_view', 'purchase'})
        print("✅ 事件类型筛选正常")
        
        # 测试时间范围筛选
        start_date = '20240101'
        end_date = '20240115'
        time_filtered = self.test_data[
            (self.test_data['event_date'] >= start_date) & 
            (self.test_data['event_date'] <= end_date)
        ]
        assert len(time_filtered) > 0
        print("✅ 时间范围筛选正常")
        
        # 测试平台筛选
        platform_filtered = self.test_data[self.test_data['platform'] == 'WEB']
        assert len(platform_filtered) > 0
        assert all(platform_filtered['platform'] == 'WEB')
        print("✅ 平台筛选正常")
    
    def test_error_handling(self):
        """测试错误处理"""
        print("🧪 测试错误处理...")
        
        # 测试缺少必要列的情况
        incomplete_data = pd.DataFrame({'incomplete': [1, 2, 3]})
        
        try:
            self.chart_generator.create_event_timeline(incomplete_data)
            assert False, "应该抛出错误"
        except ValueError as e:
            assert "缺少必要的列" in str(e)
            print("✅ 缺少列错误处理正常")
        
        # 测试空数据处理
        empty_chart = self.chart_generator.create_event_timeline(pd.DataFrame())
        assert empty_chart is not None
        print("✅ 空数据错误处理正常")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始分析结果展示界面集成测试")
        print("=" * 60)
        
        test_methods = [
            self.test_event_timeline_chart,
            self.test_retention_heatmap,
            self.test_funnel_chart,
            self.test_user_segmentation_scatter,
            self.test_feature_radar_chart,
            self.test_user_behavior_flow,
            self.test_multi_metric_dashboard,
            self.test_interactive_drill_down,
            self.test_cohort_analysis_heatmap,
            self.test_path_analysis_network,
            self.test_data_filtering_functionality,
            self.test_error_handling
        ]
        
        passed = 0
        failed = 0
        
        for test_method in test_methods:
            try:
                test_method()
                passed += 1
            except Exception as e:
                print(f"❌ {test_method.__name__} 失败: {str(e)}")
                failed += 1
        
        print("\n" + "=" * 60)
        print(f"📊 测试结果: {passed} 通过, {failed} 失败")
        
        if failed == 0:
            print("🎉 所有测试通过! 分析结果展示界面集成正常")
        else:
            print("⚠️ 部分测试失败，请检查相关功能")
        
        return failed == 0


def test_interface_integration():
    """测试界面集成功能"""
    print("🧪 测试分析结果展示界面集成...")
    
    # 测试可视化组件初始化
    chart_gen = ChartGenerator()
    advanced_viz = AdvancedVisualizer()
    
    assert chart_gen is not None
    assert advanced_viz is not None
    assert hasattr(chart_gen, 'create_event_timeline')
    assert hasattr(advanced_viz, 'create_user_behavior_flow')
    
    print("✅ 可视化组件初始化成功")
    
    # 测试分析引擎初始化
    event_engine = EventAnalysisEngine()
    retention_engine = RetentionAnalysisEngine()
    conversion_engine = ConversionAnalysisEngine()
    segmentation_engine = UserSegmentationEngine()
    path_engine = PathAnalysisEngine()
    
    assert event_engine is not None
    assert retention_engine is not None
    assert conversion_engine is not None
    assert segmentation_engine is not None
    assert path_engine is not None
    
    print("✅ 分析引擎初始化成功")
    
    print("✅ 界面集成测试通过")


if __name__ == "__main__":
    print("🎯 分析结果展示界面集成测试")
    print("=" * 80)
    
    # 运行基础集成测试
    test_interface_integration()
    
    # 运行详细功能测试
    tester = TestAnalysisResultsInterface()
    tester.setup_method()
    success = tester.run_all_tests()
    
    print("\n" + "=" * 80)
    if success:
        print("✨ 分析结果展示界面集成测试完成! 所有功能正常")
    else:
        print("⚠️ 部分功能存在问题，请检查相关实现")
    print("=" * 80)