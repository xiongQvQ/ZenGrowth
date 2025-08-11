"""
事件分析智能体集成测试

使用真实的GA4数据测试EventAnalysisAgent的完整功能
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta

from agents.event_analysis_agent_standalone import EventAnalysisAgent
from tools.data_storage_manager import DataStorageManager
from tools.ga4_data_parser import GA4DataParser


class TestEventAnalysisAgentIntegration:
    """事件分析智能体集成测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.storage_manager = DataStorageManager()
        self.agent = EventAnalysisAgent(self.storage_manager)
        self.parser = GA4DataParser()
        
    def create_realistic_ga4_data(self):
        """创建真实的GA4数据"""
        base_time = datetime(2024, 1, 1)
        events_data = []
        
        # 模拟100个用户的行为数据
        for user_id in range(100):
            user_pseudo_id = f'user_{user_id:03d}'
            
            # 每个用户的会话开始时间
            session_start = base_time + timedelta(days=user_id % 30, hours=user_id % 24)
            
            # 页面浏览事件
            for page_view in range(1, 4):  # 每个用户1-3个页面浏览
                events_data.append({
                    'user_pseudo_id': user_pseudo_id,
                    'event_name': 'page_view',
                    'event_timestamp': int((session_start + timedelta(minutes=page_view)).timestamp() * 1000000),
                    'event_datetime': session_start + timedelta(minutes=page_view),
                    'event_date': (session_start + timedelta(minutes=page_view)).strftime('%Y%m%d'),
                    'platform': 'WEB',
                    'device': {'category': 'desktop'},
                    'geo': {'country': 'US'},
                    'traffic_source': {'source': 'google', 'medium': 'organic'},
                    'event_params': [{'key': 'page_title', 'value': {'string_value': f'Page {page_view}'}}],
                    'user_properties': [{'key': 'user_type', 'value': {'string_value': 'returning'}}]
                })
            
            # 30%的用户会查看商品
            if user_id % 3 == 0:
                events_data.append({
                    'user_pseudo_id': user_pseudo_id,
                    'event_name': 'view_item',
                    'event_timestamp': int((session_start + timedelta(minutes=5)).timestamp() * 1000000),
                    'event_datetime': session_start + timedelta(minutes=5),
                    'event_date': (session_start + timedelta(minutes=5)).strftime('%Y%m%d'),
                    'platform': 'WEB',
                    'device': {'category': 'desktop'},
                    'geo': {'country': 'US'},
                    'traffic_source': {'source': 'google', 'medium': 'organic'},
                    'event_params': [
                        {'key': 'item_id', 'value': {'string_value': f'item_{user_id}'}},
                        {'key': 'item_name', 'value': {'string_value': f'Product {user_id}'}},
                        {'key': 'price', 'value': {'double_value': 29.99}}
                    ],
                    'user_properties': [{'key': 'user_type', 'value': {'string_value': 'returning'}}]
                })
            
            # 10%的用户会添加到购物车
            if user_id % 10 == 0:
                events_data.append({
                    'user_pseudo_id': user_pseudo_id,
                    'event_name': 'add_to_cart',
                    'event_timestamp': int((session_start + timedelta(minutes=8)).timestamp() * 1000000),
                    'event_datetime': session_start + timedelta(minutes=8),
                    'event_date': (session_start + timedelta(minutes=8)).strftime('%Y%m%d'),
                    'platform': 'WEB',
                    'device': {'category': 'desktop'},
                    'geo': {'country': 'US'},
                    'traffic_source': {'source': 'google', 'medium': 'organic'},
                    'event_params': [
                        {'key': 'item_id', 'value': {'string_value': f'item_{user_id}'}},
                        {'key': 'quantity', 'value': {'int_value': 1}},
                        {'key': 'value', 'value': {'double_value': 29.99}}
                    ],
                    'user_properties': [{'key': 'user_type', 'value': {'string_value': 'returning'}}]
                })
            
            # 5%的用户会购买
            if user_id % 20 == 0:
                events_data.append({
                    'user_pseudo_id': user_pseudo_id,
                    'event_name': 'purchase',
                    'event_timestamp': int((session_start + timedelta(minutes=12)).timestamp() * 1000000),
                    'event_datetime': session_start + timedelta(minutes=12),
                    'event_date': (session_start + timedelta(minutes=12)).strftime('%Y%m%d'),
                    'platform': 'WEB',
                    'device': {'category': 'desktop'},
                    'geo': {'country': 'US'},
                    'traffic_source': {'source': 'google', 'medium': 'organic'},
                    'event_params': [
                        {'key': 'transaction_id', 'value': {'string_value': f'txn_{user_id}'}},
                        {'key': 'value', 'value': {'double_value': 29.99}},
                        {'key': 'currency', 'value': {'string_value': 'USD'}}
                    ],
                    'user_properties': [{'key': 'user_type', 'value': {'string_value': 'returning'}}],
                    'items': [
                        {
                            'item_id': f'item_{user_id}',
                            'item_name': f'Product {user_id}',
                            'price': 29.99,
                            'quantity': 1
                        }
                    ]
                })
            
            # 15%的用户会注册
            if user_id % 7 == 0:
                events_data.append({
                    'user_pseudo_id': user_pseudo_id,
                    'event_name': 'sign_up',
                    'event_timestamp': int((session_start + timedelta(minutes=15)).timestamp() * 1000000),
                    'event_datetime': session_start + timedelta(minutes=15),
                    'event_date': (session_start + timedelta(minutes=15)).strftime('%Y%m%d'),
                    'platform': 'WEB',
                    'device': {'category': 'desktop'},
                    'geo': {'country': 'US'},
                    'traffic_source': {'source': 'google', 'medium': 'organic'},
                    'event_params': [{'key': 'method', 'value': {'string_value': 'email'}}],
                    'user_properties': [{'key': 'user_type', 'value': {'string_value': 'new'}}]
                })
        
        return pd.DataFrame(events_data)
    
    def test_full_event_analysis_workflow(self):
        """测试完整的事件分析工作流"""
        # 1. 创建并存储测试数据
        test_data = self.create_realistic_ga4_data()
        self.storage_manager.store_events(test_data)
        
        print(f"存储了 {len(test_data)} 条事件数据")
        print(f"事件类型: {test_data['event_name'].unique()}")
        print(f"用户数量: {test_data['user_pseudo_id'].nunique()}")
        
        # 2. 执行频次分析
        frequency_result = self.agent.analyze_event_frequency()
        assert frequency_result['status'] == 'success'
        assert len(frequency_result['results']) > 0
        
        print("\\n=== 频次分析结果 ===")
        for event_name, result in frequency_result['results'].items():
            print(f"{event_name}: {result['total_count']} 次事件, {result['unique_users']} 个用户")
        
        # 3. 执行趋势分析
        trend_result = self.agent.analyze_event_trends()
        assert trend_result['status'] == 'success'
        
        print("\\n=== 趋势分析结果 ===")
        for event_name, result in trend_result['results'].items():
            print(f"{event_name}: 趋势方向 {result['trend_direction']}, 增长率 {result['growth_rate']:.2f}%")
        
        # 4. 执行关联性分析
        correlation_result = self.agent.analyze_event_correlations(min_co_occurrence=2)
        assert correlation_result['status'] == 'success'
        
        print("\\n=== 关联性分析结果 ===")
        for correlation in correlation_result['results'][:5]:  # 显示前5个
            event1, event2 = correlation['event_pair']
            print(f"{event1} <-> {event2}: 相关系数 {correlation['correlation_coefficient']:.3f}")
        
        # 5. 执行关键事件识别
        key_event_result = self.agent.identify_key_events(top_k=5)
        assert key_event_result['status'] == 'success'
        
        print("\\n=== 关键事件识别结果 ===")
        for key_event in key_event_result['results']:
            print(f"{key_event['event_name']}: 重要性得分 {key_event['importance_score']:.1f}")
        
        # 6. 执行综合分析
        comprehensive_result = self.agent.comprehensive_event_analysis()
        assert comprehensive_result['status'] == 'success'
        assert 'frequency_analysis' in comprehensive_result
        assert 'trend_analysis' in comprehensive_result
        assert 'correlation_analysis' in comprehensive_result
        assert 'key_event_analysis' in comprehensive_result
        
        print("\\n=== 综合分析摘要 ===")
        summary = comprehensive_result['summary']
        print(f"成功执行的分析: {summary['successful_analyses']}/{summary['total_analyses_performed']}")
        print(f"分析类型: {', '.join(summary['analysis_types'])}")
        
        # 验证关键发现
        key_findings = summary.get('key_findings', [])
        assert len(key_findings) > 0
        print("\\n=== 关键发现 ===")
        for i, finding in enumerate(key_findings[:5], 1):
            print(f"{i}. {finding}")
    
    def test_event_pattern_recognition(self):
        """测试事件模式识别"""
        # 创建具有明显模式的数据
        test_data = self.create_realistic_ga4_data()
        self.storage_manager.store_events(test_data)
        
        # 分析频次模式
        frequency_result = self.agent.analyze_event_frequency()
        
        # 验证page_view是最频繁的事件
        results = frequency_result['results']
        page_view_count = results['page_view']['total_count']
        purchase_count = results['purchase']['total_count']
        
        assert page_view_count > purchase_count  # page_view应该比purchase更频繁
        
        # 验证转化漏斗模式
        view_item_count = results['view_item']['total_count']
        add_to_cart_count = results['add_to_cart']['total_count']
        
        assert page_view_count > view_item_count > add_to_cart_count > purchase_count
        
        print("\\n=== 转化漏斗验证 ===")
        print(f"页面浏览: {page_view_count}")
        print(f"查看商品: {view_item_count}")
        print(f"添加购物车: {add_to_cart_count}")
        print(f"购买: {purchase_count}")
        
        # 计算转化率
        view_to_purchase_rate = (purchase_count / page_view_count) * 100
        cart_to_purchase_rate = (purchase_count / add_to_cart_count) * 100 if add_to_cart_count > 0 else 0
        
        print(f"浏览到购买转化率: {view_to_purchase_rate:.2f}%")
        print(f"购物车到购买转化率: {cart_to_purchase_rate:.2f}%")
        
        assert view_to_purchase_rate < 10  # 转化率应该合理
        assert cart_to_purchase_rate > view_to_purchase_rate  # 购物车转化率应该更高
    
    def test_user_behavior_insights(self):
        """测试用户行为洞察生成"""
        test_data = self.create_realistic_ga4_data()
        self.storage_manager.store_events(test_data)
        
        # 执行综合分析
        result = self.agent.comprehensive_event_analysis()
        
        # 验证洞察生成
        frequency_insights = result['frequency_analysis']['insights']
        trend_insights = result['trend_analysis']['insights']
        correlation_insights = result['correlation_analysis']['insights']
        key_event_insights = result['key_event_analysis']['insights']
        
        assert len(frequency_insights) > 0
        assert len(key_event_insights) > 0
        
        print("\\n=== 频次分析洞察 ===")
        for insight in frequency_insights:
            print(f"- {insight}")
        
        print("\\n=== 关键事件洞察 ===")
        for insight in key_event_insights:
            print(f"- {insight}")
        
        # 验证洞察内容的合理性
        frequency_text = ' '.join(frequency_insights)
        assert 'page_view' in frequency_text  # 应该提到最频繁的事件
        
        key_event_text = ' '.join(key_event_insights)
        assert any(event in key_event_text for event in ['page_view', 'purchase', 'sign_up'])


if __name__ == '__main__':
    # 运行集成测试
    test = TestEventAnalysisAgentIntegration()
    test.setup_method()
    
    print("开始事件分析智能体集成测试...")
    test.test_full_event_analysis_workflow()
    print("\\n" + "="*50)
    test.test_event_pattern_recognition()
    print("\\n" + "="*50)
    test.test_user_behavior_insights()
    print("\\n集成测试完成！")