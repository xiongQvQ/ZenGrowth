"""
用户分群智能体独立版本测试

测试UserSegmentationAgentStandalone的基本功能
"""

import sys
sys.path.append('.')

from agents.user_segmentation_agent_standalone import UserSegmentationAgentStandalone
from tools.data_storage_manager import DataStorageManager
import pandas as pd
from datetime import datetime


def test_user_segmentation_agent_standalone():
    """测试用户分群智能体独立版本的基本功能"""
    
    print("=== 用户分群智能体独立版本测试 ===\n")
    
    # 创建测试数据
    print("1. 创建测试数据...")
    events_data = pd.DataFrame({
        'user_pseudo_id': ['user1', 'user1', 'user2', 'user2', 'user3', 'user3', 'user4', 'user4'],
        'event_name': ['page_view', 'purchase', 'page_view', 'add_to_cart', 'login', 'page_view', 'sign_up', 'purchase'],
        'event_timestamp': [
            1640995200000000, 1640995260000000, 1640995320000000, 1640995380000000,
            1640995440000000, 1640995500000000, 1640995560000000, 1640995620000000
        ],
        'platform': ['web', 'web', 'mobile', 'mobile', 'web', 'web', 'mobile', 'mobile'],
        'device': [
            {'category': 'desktop'}, {'category': 'desktop'},
            {'category': 'mobile'}, {'category': 'mobile'},
            {'category': 'desktop'}, {'category': 'desktop'},
            {'category': 'mobile'}, {'category': 'mobile'}
        ],
        'geo': [
            {'country': 'US'}, {'country': 'US'},
            {'country': 'CN'}, {'country': 'CN'},
            {'country': 'US'}, {'country': 'US'},
            {'country': 'JP'}, {'country': 'JP'}
        ]
    })
    events_data['event_datetime'] = pd.to_datetime(events_data['event_timestamp'], unit='us')
    print(f"   创建了{len(events_data)}条事件数据，涉及{events_data['user_pseudo_id'].nunique()}个用户")
    
    # 创建存储管理器和智能体
    print("\n2. 初始化智能体...")
    storage_manager = DataStorageManager()
    storage_manager.store_events(events_data)
    
    agent = UserSegmentationAgentStandalone(storage_manager)
    print("   用户分群智能体初始化完成")
    
    # 测试特征提取
    print("\n3. 测试特征提取...")
    feature_result = agent.extract_user_features()
    
    assert feature_result['status'] == 'success', f"特征提取失败: {feature_result.get('error_message')}"
    
    user_features = feature_result['user_features']
    print(f"   ✓ 成功提取了{len(user_features)}个用户的特征")
    
    # 验证特征结构
    for user_feature in user_features:
        assert 'user_id' in user_feature
        assert 'behavioral_features' in user_feature
        assert 'demographic_features' in user_feature
        assert 'engagement_features' in user_feature
        assert 'conversion_features' in user_feature
        assert 'temporal_features' in user_feature
    
    print("   ✓ 特征结构验证通过")
    
    # 测试聚类分析
    print("\n4. 测试聚类分析...")
    clustering_result = agent.perform_clustering(method='kmeans', n_clusters=2)
    
    assert clustering_result['status'] == 'success', f"聚类分析失败: {clustering_result.get('error_message')}"
    
    segments = clustering_result['segments']
    print(f"   ✓ 成功生成了{len(segments)}个用户分群")
    
    # 验证分群结构
    for segment in segments:
        assert 'segment_id' in segment
        assert 'segment_name' in segment
        assert 'user_count' in segment
        assert 'user_ids' in segment
        assert segment['user_count'] == len(segment['user_ids'])
    
    print("   ✓ 分群结构验证通过")
    
    # 测试分群画像生成
    print("\n5. 测试分群画像生成...")
    profile_result = agent.generate_segment_profiles(segments)
    
    assert profile_result['status'] == 'success', f"画像生成失败: {profile_result.get('error_message')}"
    
    segment_profiles = profile_result['segment_profiles']
    print(f"   ✓ 成功生成了{len(segment_profiles)}个分群画像")
    
    # 验证画像结构
    for profile in segment_profiles:
        assert 'detailed_profile' in profile
        assert 'marketing_recommendations' in profile
        assert 'operation_strategies' in profile
        assert 'key_insights' in profile
        
        # 验证详细画像结构
        detailed_profile = profile['detailed_profile']
        assert 'demographic_profile' in detailed_profile
        assert 'behavioral_profile' in detailed_profile
        assert 'engagement_profile' in detailed_profile
        assert 'conversion_profile' in detailed_profile
    
    print("   ✓ 画像结构验证通过")
    
    # 测试综合分析
    print("\n6. 测试综合分群分析...")
    comprehensive_result = agent.comprehensive_user_segmentation(method='kmeans', n_clusters=3)
    
    assert comprehensive_result['status'] == 'success', f"综合分析失败: {comprehensive_result.get('error_message')}"
    
    assert 'feature_extraction' in comprehensive_result
    assert 'clustering_analysis' in comprehensive_result
    assert 'segment_profiles' in comprehensive_result
    assert 'summary' in comprehensive_result
    
    print("   ✓ 综合分析完成")
    
    # 显示分析结果摘要
    print("\n7. 分析结果摘要:")
    summary = comprehensive_result['summary']
    print(f"   - 执行的分析数量: {summary['total_analyses_performed']}")
    print(f"   - 成功的分析数量: {summary['successful_analyses']}")
    print("   - 关键发现:")
    for finding in summary['key_findings'][:5]:  # 显示前5个发现
        print(f"     • {finding}")
    
    # 显示分群信息
    clustering_analysis = comprehensive_result['clustering_analysis']
    segments = clustering_analysis['segments']
    print(f"\n   - 生成的用户分群:")
    for segment in segments:
        print(f"     • {segment['segment_name']}: {segment['user_count']}个用户")
    
    print("\n=== 所有测试通过! ===")
    return True


def test_different_clustering_methods():
    """测试不同的聚类方法"""
    
    print("\n=== 测试不同聚类方法 ===\n")
    
    # 创建测试数据
    events_data = pd.DataFrame({
        'user_pseudo_id': ['user1', 'user1', 'user2', 'user2', 'user3', 'user3'],
        'event_name': ['page_view', 'purchase', 'page_view', 'add_to_cart', 'login', 'page_view'],
        'event_timestamp': [1640995200000000, 1640995260000000, 1640995320000000, 1640995380000000, 1640995440000000, 1640995500000000],
        'platform': ['web', 'web', 'mobile', 'mobile', 'web', 'web']
    })
    events_data['event_datetime'] = pd.to_datetime(events_data['event_timestamp'], unit='us')
    
    storage_manager = DataStorageManager()
    storage_manager.store_events(events_data)
    agent = UserSegmentationAgentStandalone(storage_manager)
    
    # 测试不同的聚类方法
    methods = ['kmeans', 'dbscan', 'behavioral', 'value_based', 'engagement']
    
    for method in methods:
        print(f"测试{method}聚类方法...")
        try:
            result = agent.perform_clustering(method=method, n_clusters=2)
            if result['status'] == 'success':
                segments = result['segments']
                print(f"   ✓ {method}方法成功，生成{len(segments)}个分群")
            else:
                print(f"   ✗ {method}方法失败: {result.get('error_message')}")
        except Exception as e:
            print(f"   ✗ {method}方法异常: {str(e)}")
    
    print("\n聚类方法测试完成")


if __name__ == '__main__':
    try:
        # 运行基本功能测试
        test_user_segmentation_agent_standalone()
        
        # 运行不同聚类方法测试
        test_different_clustering_methods()
        
        print("\n🎉 所有测试都通过了!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()