"""
用户分群引擎集成测试

验证UserSegmentationEngine的基本功能是否正常工作。
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.user_segmentation_engine import UserSegmentationEngine
from tools.data_storage_manager import DataStorageManager


def create_segmentation_sample_data():
    """创建用户分群示例数据"""
    print("创建用户分群示例数据...")
    
    np.random.seed(42)
    events = []
    users = []
    sessions = []
    
    # 创建不同类型的用户
    user_types = {
        'high_value_active': {'count': 30, 'event_prob': 0.8, 'conversion_prob': 0.3, 'session_length': 'long'},
        'medium_value_regular': {'count': 50, 'event_prob': 0.5, 'conversion_prob': 0.15, 'session_length': 'medium'},
        'low_value_occasional': {'count': 70, 'event_prob': 0.2, 'conversion_prob': 0.05, 'session_length': 'short'},
        'new_users': {'count': 50, 'event_prob': 0.3, 'conversion_prob': 0.08, 'session_length': 'short'}
    }
    
    user_id_counter = 0
    start_date = datetime.now() - timedelta(days=90)
    
    for user_type, config in user_types.items():
        for _ in range(config['count']):
            user_id = f'user_{user_id_counter}'
            user_id_counter += 1
            
            # 创建用户基础信息
            platform = np.random.choice(['web', 'mobile'], p=[0.6, 0.4])
            device_category = np.random.choice(['desktop', 'mobile', 'tablet'], p=[0.5, 0.4, 0.1])
            geo_country = np.random.choice(['US', 'UK', 'CA', 'DE', 'FR'], p=[0.4, 0.2, 0.15, 0.15, 0.1])
            
            user_info = {
                'user_pseudo_id': user_id,
                'platform': platform,
                'device_category': device_category,
                'geo_country': geo_country,
                'first_seen': start_date + timedelta(days=np.random.randint(0, 60)),
                'last_seen': datetime.now() - timedelta(days=np.random.randint(0, 7)),
                'total_events': 0  # 将在后面更新
            }
            users.append(user_info)
            
            # 生成用户事件
            user_events = []
            user_sessions = []
            
            # 根据用户类型生成不同的行为模式
            if user_type == 'high_value_active':
                # 高价值活跃用户：频繁访问，多种事件类型，高转化
                days_active = np.random.randint(60, 90)
                events_per_day = np.random.randint(5, 20)
                event_types = ['page_view', 'view_item', 'search', 'add_to_cart', 'purchase', 'login']
                
            elif user_type == 'medium_value_regular':
                # 中等价值常规用户：定期访问，中等事件数，中等转化
                days_active = np.random.randint(30, 60)
                events_per_day = np.random.randint(2, 8)
                event_types = ['page_view', 'view_item', 'search', 'add_to_cart', 'login']
                
            elif user_type == 'low_value_occasional':
                # 低价值偶尔用户：偶尔访问，少量事件，低转化
                days_active = np.random.randint(5, 20)
                events_per_day = np.random.randint(1, 3)
                event_types = ['page_view', 'view_item']
                
            else:  # new_users
                # 新用户：最近注册，探索性行为
                days_active = np.random.randint(1, 10)
                events_per_day = np.random.randint(1, 5)
                event_types = ['page_view', 'sign_up', 'view_item', 'search']
                
            # 生成用户的活跃日期
            active_dates = np.random.choice(
                range(90), 
                size=min(days_active, 90), 
                replace=False
            )
            
            session_id_counter = 0
            
            for day_offset in sorted(active_dates):
                activity_date = start_date + timedelta(days=int(day_offset))
                
                # 决定这一天是否活跃
                if np.random.random() < config['event_prob']:
                    # 生成这一天的会话
                    sessions_today = np.random.randint(1, 4)
                    
                    for session_idx in range(sessions_today):
                        session_id = f'{user_id}_session_{session_id_counter}'
                        session_id_counter += 1
                        
                        session_start = activity_date + timedelta(
                            hours=np.random.randint(0, 24),
                            minutes=np.random.randint(0, 60)
                        )
                        
                        # 根据用户类型决定会话长度
                        if config['session_length'] == 'long':
                            session_duration = np.random.randint(300, 3600)  # 5分钟到1小时
                            events_in_session = np.random.randint(5, 20)
                        elif config['session_length'] == 'medium':
                            session_duration = np.random.randint(120, 1800)  # 2分钟到30分钟
                            events_in_session = np.random.randint(2, 10)
                        else:  # short
                            session_duration = np.random.randint(30, 600)   # 30秒到10分钟
                            events_in_session = np.random.randint(1, 5)
                            
                        session_end = session_start + timedelta(seconds=session_duration)
                        
                        # 生成会话中的事件
                        session_events = []
                        conversions_in_session = 0
                        
                        for event_idx in range(events_in_session):
                            event_time = session_start + timedelta(
                                seconds=np.random.randint(0, session_duration)
                            )
                            
                            # 选择事件类型
                            if event_idx == 0:
                                # 第一个事件通常是page_view
                                event_name = 'page_view'
                            else:
                                # 根据转化概率决定是否生成转化事件
                                if (np.random.random() < config['conversion_prob'] and 
                                    conversions_in_session == 0):
                                    conversion_events = ['add_to_cart', 'purchase', 'sign_up', 'login']
                                    available_conversions = [e for e in conversion_events if e in event_types]
                                    if available_conversions:
                                        event_name = np.random.choice(available_conversions)
                                        conversions_in_session += 1
                                    else:
                                        event_name = np.random.choice(event_types)
                                else:
                                    event_name = np.random.choice(event_types)
                                    
                            event = {
                                'user_pseudo_id': user_id,
                                'event_name': event_name,
                                'event_timestamp': int(event_time.timestamp() * 1000000),
                                'event_datetime': event_time,
                                'event_date': activity_date.strftime('%Y%m%d'),
                                'platform': platform,
                                'device': {'category': device_category},
                                'geo': {'country': geo_country}
                            }
                            
                            events.append(event)
                            session_events.append(event)
                            user_events.append(event)
                            
                        # 创建会话记录
                        session_record = {
                            'session_id': session_id,
                            'user_pseudo_id': user_id,
                            'start_time': session_start,
                            'end_time': session_end,
                            'duration_seconds': session_duration,
                            'event_count': len(session_events),
                            'conversions': conversions_in_session,
                            'platform': platform
                        }
                        
                        sessions.append(session_record)
                        user_sessions.append(session_record)
                        
            # 更新用户总事件数
            user_info['total_events'] = len(user_events)
            
    events_df = pd.DataFrame(events)
    users_df = pd.DataFrame(users)
    sessions_df = pd.DataFrame(sessions)
    
    print(f"创建了 {len(events_df)} 条事件数据")
    print(f"创建了 {len(users_df)} 个用户数据")
    print(f"创建了 {len(sessions_df)} 个会话数据")
    print(f"用户类型分布: {dict(zip(user_types.keys(), [config['count'] for config in user_types.values()]))}")
    
    return events_df, users_df, sessions_df


def test_user_feature_extraction(engine, events_df, users_df, sessions_df):
    """测试用户特征提取"""
    print("\n=== 测试用户特征提取 ===")
    
    try:
        user_features = engine.extract_user_features(events_df, users_df, sessions_df)
        
        print(f"提取了 {len(user_features)} 个用户的特征")
        
        # 显示特征类型统计
        feature_types = {
            'behavioral': 0,
            'demographic': 0,
            'engagement': 0,
            'conversion': 0,
            'temporal': 0
        }
        
        if user_features:
            sample_user = user_features[0]
            feature_types['behavioral'] = len(sample_user.behavioral_features)
            feature_types['demographic'] = len(sample_user.demographic_features)
            feature_types['engagement'] = len(sample_user.engagement_features)
            feature_types['conversion'] = len(sample_user.conversion_features)
            feature_types['temporal'] = len(sample_user.temporal_features)
            
        print(f"特征类型统计:")
        for feature_type, count in feature_types.items():
            print(f"  {feature_type}: {count} 个特征")
            
        # 显示几个示例用户的特征
        print(f"\n示例用户特征:")
        for i, user_feature in enumerate(user_features[:3]):
            print(f"  用户 {user_feature.user_id}:")
            print(f"    总事件数: {user_feature.behavioral_features.get('total_events', 0)}")
            print(f"    活跃天数: {user_feature.engagement_features.get('active_days', 0)}")
            print(f"    转化次数: {user_feature.conversion_features.get('total_conversions', 0)}")
            print(f"    平台: {user_feature.demographic_features.get('platform', 'unknown')}")
            
        print("✅ 用户特征提取测试通过")
        return True, user_features
        
    except Exception as e:
        print(f"❌ 用户特征提取测试失败: {e}")
        return False, []


def test_kmeans_segmentation(engine, user_features):
    """测试K-means分群"""
    print("\n=== 测试K-means分群 ===")
    
    try:
        segmentation_result = engine.create_user_segments(
            user_features,
            method='kmeans',
            n_clusters=4
        )
        
        print(f"K-means分群结果:")
        print(f"  分群方法: {segmentation_result.segmentation_method}")
        print(f"  分群数量: {len(segmentation_result.segments)}")
        
        # 显示各分群信息
        print(f"  分群详情:")
        for segment in segmentation_result.segments:
            print(f"    {segment.segment_name} (ID: {segment.segment_id}):")
            print(f"      用户数: {segment.user_count}")
            print(f"      参与度: {segment.segment_profile.get('engagement_level', 'unknown')}")
            print(f"      价值: {segment.segment_profile.get('value_level', 'unknown')}")
            print(f"      主要平台: {segment.segment_profile.get('dominant_platform', 'unknown')}")
            print(f"      关键特征: {', '.join(segment.key_characteristics[:2])}")
            
        # 显示质量指标
        print(f"  质量指标:")
        quality_metrics = segmentation_result.quality_metrics
        for metric, value in quality_metrics.items():
            if isinstance(value, float):
                print(f"    {metric}: {value:.3f}")
            else:
                print(f"    {metric}: {value}")
                
        # 显示特征重要性
        if segmentation_result.feature_importance:
            print(f"  重要特征 (前5个):")
            sorted_features = sorted(
                segmentation_result.feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )
            for feature, importance in sorted_features[:5]:
                print(f"    {feature}: {importance:.3f}")
                
        print("✅ K-means分群测试通过")
        return True, segmentation_result
        
    except Exception as e:
        print(f"❌ K-means分群测试失败: {e}")
        return False, None


def test_behavioral_segmentation(engine, user_features):
    """测试行为分群"""
    print("\n=== 测试行为分群 ===")
    
    try:
        segmentation_result = engine.create_user_segments(
            user_features,
            method='behavioral',
            n_clusters=3
        )
        
        print(f"行为分群结果:")
        print(f"  分群数量: {len(segmentation_result.segments)}")
        
        # 显示行为特征对比
        print(f"  行为特征对比:")
        for segment in segmentation_result.segments:
            avg_events = segment.segment_profile.get('avg_total_events', 0)
            avg_conversion = segment.segment_profile.get('avg_conversion_ratio', 0)
            print(f"    {segment.segment_name}: 平均事件 {avg_events:.1f}, 转化率 {avg_conversion:.3f}")
            
        print("✅ 行为分群测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 行为分群测试失败: {e}")
        return False


def test_engagement_segmentation(engine, user_features):
    """测试参与度分群"""
    print("\n=== 测试参与度分群 ===")
    
    try:
        segmentation_result = engine.create_user_segments(
            user_features,
            method='engagement',
            n_clusters=3
        )
        
        print(f"参与度分群结果:")
        print(f"  分群数量: {len(segmentation_result.segments)}")
        
        # 显示参与度分布
        engagement_distribution = {}
        for segment in segmentation_result.segments:
            engagement_level = segment.segment_profile.get('engagement_level', 'unknown')
            engagement_distribution[engagement_level] = engagement_distribution.get(engagement_level, 0) + segment.user_count
            
        print(f"  参与度分布:")
        for level, count in engagement_distribution.items():
            print(f"    {level}: {count} 用户")
            
        print("✅ 参与度分群测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 参与度分群测试失败: {e}")
        return False


def test_segment_characteristics_analysis(engine, segmentation_result):
    """测试分群特征分析"""
    print("\n=== 测试分群特征分析 ===")
    
    try:
        if segmentation_result is None:
            print("跳过分群特征分析（没有有效的分群结果）")
            return True
            
        analysis = engine.analyze_segment_characteristics(segmentation_result)
        
        print(f"分群特征分析:")
        
        # 分群摘要
        summary = analysis.get('segment_summary', {})
        print(f"  分群摘要:")
        print(f"    总分群数: {summary.get('total_segments', 0)}")
        print(f"    总用户数: {summary.get('total_users', 0)}")
        print(f"    平均分群大小: {summary.get('avg_segment_size', 0):.1f}")
        print(f"    最大分群大小: {summary.get('largest_segment_size', 0)}")
        print(f"    最小分群大小: {summary.get('smallest_segment_size', 0)}")
        
        # 特征分析
        feature_analysis = analysis.get('feature_analysis', {})
        if feature_analysis.get('most_important_features'):
            print(f"  最重要特征:")
            for feature in feature_analysis['most_important_features']:
                importance = feature_analysis['feature_importance_scores'].get(feature, 0)
                print(f"    {feature}: {importance:.3f}")
                
        # 分群洞察
        insights = analysis.get('segment_insights', [])
        if insights:
            print(f"  分群洞察:")
            for insight in insights[:3]:
                print(f"    {insight}")
                
        # 建议
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            print(f"  建议:")
            for recommendation in recommendations[:3]:
                print(f"    {recommendation}")
                
        print("✅ 分群特征分析测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 分群特征分析测试失败: {e}")
        return False


def test_segment_comparison(engine, segmentation_result):
    """测试分群对比"""
    print("\n=== 测试分群对比 ===")
    
    try:
        if segmentation_result is None:
            print("跳过分群对比（没有有效的分群结果）")
            return True
            
        comparison_df = segmentation_result.segment_comparison
        
        if not comparison_df.empty:
            print(f"分群对比表:")
            print(f"  表格大小: {comparison_df.shape}")
            print(f"  包含列: {list(comparison_df.columns)}")
            
            # 显示关键对比信息
            if 'segment_name' in comparison_df.columns and 'user_count' in comparison_df.columns:
                print(f"  分群用户数对比:")
                for _, row in comparison_df.iterrows():
                    print(f"    {row['segment_name']}: {row['user_count']} 用户")
                    
        print("✅ 分群对比测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 分群对比测试失败: {e}")
        return False


def test_analysis_summary(engine):
    """测试分析摘要"""
    print("\n=== 测试分析摘要 ===")
    
    try:
        summary = engine.get_analysis_summary()
        
        print("分析摘要:")
        print(f"  总事件数: {summary.get('total_events', 'N/A')}")
        print(f"  独立用户数: {summary.get('unique_users', 'N/A')}")
        print(f"  用户记录数: {summary.get('total_user_records', 'N/A')}")
        print(f"  日期范围: {summary.get('date_range', {}).get('start', 'N/A')} 到 {summary.get('date_range', {}).get('end', 'N/A')}")
        
        print(f"  可用分群方法:")
        for method in summary.get('available_methods', []):
            print(f"    {method}")
            
        print(f"  推荐聚类数范围: {summary.get('recommended_cluster_range', [])}")
        
        print(f"  特征类型:")
        feature_types = summary.get('feature_types', {})
        for feature_type, features in feature_types.items():
            print(f"    {feature_type}: {len(features)} 个特征")
            
        print("✅ 分析摘要测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 分析摘要测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始用户分群引擎集成测试...")
    
    # 创建示例数据
    events_df, users_df, sessions_df = create_segmentation_sample_data()
    
    # 创建存储管理器并存储数据
    print("\n设置存储管理器...")
    storage_manager = DataStorageManager()
    storage_manager.store_events(events_df)
    storage_manager.store_users(users_df)
    storage_manager.store_sessions(sessions_df)
    
    # 创建用户分群引擎
    print("初始化用户分群引擎...")
    engine = UserSegmentationEngine(storage_manager)
    
    # 运行测试
    test_results = []
    user_features = []
    segmentation_result = None
    
    # 特征提取测试
    success, user_features = test_user_feature_extraction(engine, events_df, users_df, sessions_df)
    test_results.append(success)
    
    if success and user_features:
        # K-means分群测试
        success, segmentation_result = test_kmeans_segmentation(engine, user_features)
        test_results.append(success)
        
        # 其他分群方法测试
        test_results.append(test_behavioral_segmentation(engine, user_features))
        test_results.append(test_engagement_segmentation(engine, user_features))
        
        # 分群分析测试
        test_results.append(test_segment_characteristics_analysis(engine, segmentation_result))
        test_results.append(test_segment_comparison(engine, segmentation_result))
    else:
        # 如果特征提取失败，跳过后续测试
        test_results.extend([False] * 5)
        
    # 分析摘要测试
    test_results.append(test_analysis_summary(engine))
    
    # 总结测试结果
    print(f"\n=== 测试总结 ===")
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"通过测试: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！用户分群引擎工作正常。")
        return True
    else:
        print("⚠️  部分测试失败，请检查实现。")
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)