"""
事件分析引擎集成测试

验证EventAnalysisEngine的基本功能是否正常工作。
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.event_analysis_engine import EventAnalysisEngine
from tools.data_storage_manager import DataStorageManager


def create_sample_data():
    """创建示例数据"""
    print("创建示例数据...")
    
    # 创建事件数据
    np.random.seed(42)
    events = []
    
    event_types = ['page_view', 'sign_up', 'login', 'purchase', 'add_to_cart']
    users = [f'user_{i}' for i in range(50)]
    
    # 生成30天的数据
    start_date = datetime.now() - timedelta(days=30)
    
    for day in range(30):
        current_date = start_date + timedelta(days=day)
        daily_events = np.random.poisson(20)  # 每天平均20个事件
        
        for _ in range(daily_events):
            event_time = current_date + timedelta(
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60)
            )
            
            event = {
                'user_pseudo_id': np.random.choice(users),
                'event_name': np.random.choice(event_types, p=[0.5, 0.1, 0.2, 0.05, 0.15]),
                'event_timestamp': int(event_time.timestamp() * 1000000),
                'event_datetime': event_time,
                'event_date': current_date.strftime('%Y%m%d'),
                'platform': np.random.choice(['web', 'mobile']),
                'device': {'category': np.random.choice(['desktop', 'mobile', 'tablet'])},
                'geo': {'country': np.random.choice(['US', 'UK', 'CA'])}
            }
            events.append(event)
    
    events_df = pd.DataFrame(events)
    print(f"创建了 {len(events_df)} 条事件数据")
    
    # 创建用户数据
    users_data = []
    for user_id in users:
        user_events = events_df[events_df['user_pseudo_id'] == user_id]
        if not user_events.empty:
            user = {
                'user_pseudo_id': user_id,
                'platform': user_events['platform'].iloc[0],
                'device_category': user_events['device'].iloc[0]['category'],
                'geo_country': user_events['geo'].iloc[0]['country'],
                'first_seen': user_events['event_datetime'].min(),
                'last_seen': user_events['event_datetime'].max(),
                'total_events': len(user_events)
            }
            users_data.append(user)
    
    users_df = pd.DataFrame(users_data)
    print(f"创建了 {len(users_df)} 个用户数据")
    
    # 创建会话数据
    sessions_data = []
    session_id = 1
    
    for user_id in users:
        user_events = events_df[events_df['user_pseudo_id'] == user_id].sort_values('event_datetime')
        if not user_events.empty:
            # 简单的会话分割：30分钟无活动则新会话
            current_session_events = []
            last_time = None
            
            for _, event in user_events.iterrows():
                if last_time is None or (event['event_datetime'] - last_time).total_seconds() > 1800:
                    # 开始新会话
                    if current_session_events:
                        # 保存上一个会话
                        session_start = min(e['event_datetime'] for e in current_session_events)
                        session_end = max(e['event_datetime'] for e in current_session_events)
                        
                        session = {
                            'session_id': f'session_{session_id}',
                            'user_pseudo_id': user_id,
                            'start_time': session_start,
                            'end_time': session_end,
                            'duration_seconds': int((session_end - session_start).total_seconds()),
                            'event_count': len(current_session_events),
                            'conversions': sum(1 for e in current_session_events 
                                             if e['event_name'] in ['sign_up', 'purchase']),
                            'platform': current_session_events[0]['platform']
                        }
                        sessions_data.append(session)
                        session_id += 1
                    
                    current_session_events = []
                
                current_session_events.append(event.to_dict())
                last_time = event['event_datetime']
            
            # 保存最后一个会话
            if current_session_events:
                session_start = min(e['event_datetime'] for e in current_session_events)
                session_end = max(e['event_datetime'] for e in current_session_events)
                
                session = {
                    'session_id': f'session_{session_id}',
                    'user_pseudo_id': user_id,
                    'start_time': session_start,
                    'end_time': session_end,
                    'duration_seconds': int((session_end - session_start).total_seconds()),
                    'event_count': len(current_session_events),
                    'conversions': sum(1 for e in current_session_events 
                                     if e['event_name'] in ['sign_up', 'purchase']),
                    'platform': current_session_events[0]['platform']
                }
                sessions_data.append(session)
                session_id += 1
    
    sessions_df = pd.DataFrame(sessions_data)
    print(f"创建了 {len(sessions_df)} 个会话数据")
    
    return events_df, users_df, sessions_df


def test_event_frequency_analysis(engine, events_df):
    """测试事件频次分析"""
    print("\n=== 测试事件频次分析 ===")
    
    try:
        results = engine.calculate_event_frequency(events_df)
        
        print(f"分析了 {len(results)} 种事件类型:")
        for event_type, result in results.items():
            print(f"  {event_type}:")
            print(f"    总事件数: {result.total_count}")
            print(f"    独立用户数: {result.unique_users}")
            print(f"    平均每用户: {result.avg_per_user:.2f}")
            print(f"    频次分布: {result.frequency_distribution}")
        
        print("✅ 事件频次分析测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 事件频次分析测试失败: {e}")
        return False


def test_event_trend_analysis(engine, events_df):
    """测试事件趋势分析"""
    print("\n=== 测试事件趋势分析 ===")
    
    try:
        results = engine.analyze_event_trends(events_df, time_granularity='daily')
        
        print(f"分析了 {len(results)} 种事件类型的趋势:")
        for event_type, result in results.items():
            print(f"  {event_type}:")
            print(f"    趋势方向: {result.trend_direction}")
            print(f"    增长率: {result.growth_rate:.2f}%")
            print(f"    数据点数: {len(result.trend_data)}")
            if result.anomalies:
                print(f"    异常点数: {len(result.anomalies)}")
        
        print("✅ 事件趋势分析测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 事件趋势分析测试失败: {e}")
        return False


def test_event_correlation_analysis(engine, events_df):
    """测试事件关联性分析"""
    print("\n=== 测试事件关联性分析 ===")
    
    try:
        results = engine.analyze_event_correlations(events_df, min_co_occurrence=5)
        
        print(f"发现 {len(results)} 个事件关联性:")
        for result in results[:5]:  # 只显示前5个
            event1, event2 = result.event_pair
            print(f"  {event1} <-> {event2}:")
            print(f"    相关系数: {result.correlation_coefficient:.3f}")
            print(f"    共现率: {result.co_occurrence_rate:.3f}")
            print(f"    显著性: {result.significance_level:.3f}")
        
        print("✅ 事件关联性分析测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 事件关联性分析测试失败: {e}")
        return False


def test_key_event_identification(engine, events_df, users_df, sessions_df):
    """测试关键事件识别"""
    print("\n=== 测试关键事件识别 ===")
    
    try:
        results = engine.identify_key_events(events_df, users_df, sessions_df, top_k=5)
        
        print(f"识别出 {len(results)} 个关键事件:")
        for result in results:
            print(f"  {result.event_name}:")
            print(f"    重要性得分: {result.importance_score:.2f}")
            print(f"    用户参与度影响: {result.user_engagement_impact:.2f}")
            print(f"    转化影响: {result.conversion_impact:.2f}")
            print(f"    留存影响: {result.retention_impact:.2f}")
            print(f"    原因: {', '.join(result.reasons[:2])}")
        
        print("✅ 关键事件识别测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 关键事件识别测试失败: {e}")
        return False


def test_analysis_summary(engine):
    """测试分析摘要"""
    print("\n=== 测试分析摘要 ===")
    
    try:
        summary = engine.get_analysis_summary()
        
        print("分析摘要:")
        print(f"  总事件数: {summary.get('total_events', 'N/A')}")
        print(f"  独立用户数: {summary.get('unique_users', 'N/A')}")
        print(f"  事件类型数: {summary.get('unique_event_types', 'N/A')}")
        print(f"  日期范围: {summary.get('date_range', {}).get('start', 'N/A')} 到 {summary.get('date_range', {}).get('end', 'N/A')}")
        
        if 'top_events' in summary:
            print("  热门事件:")
            for event, count in list(summary['top_events'].items())[:3]:
                print(f"    {event}: {count}")
        
        print("✅ 分析摘要测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 分析摘要测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始事件分析引擎集成测试...")
    
    # 创建示例数据
    events_df, users_df, sessions_df = create_sample_data()
    
    # 创建存储管理器并存储数据
    print("\n设置存储管理器...")
    storage_manager = DataStorageManager()
    storage_manager.store_events(events_df)
    storage_manager.store_users(users_df)
    storage_manager.store_sessions(sessions_df)
    
    # 创建事件分析引擎
    print("初始化事件分析引擎...")
    engine = EventAnalysisEngine(storage_manager)
    
    # 运行测试
    test_results = []
    
    test_results.append(test_event_frequency_analysis(engine, events_df))
    test_results.append(test_event_trend_analysis(engine, events_df))
    test_results.append(test_event_correlation_analysis(engine, events_df))
    test_results.append(test_key_event_identification(engine, events_df, users_df, sessions_df))
    test_results.append(test_analysis_summary(engine))
    
    # 总结测试结果
    print(f"\n=== 测试总结 ===")
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"通过测试: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！事件分析引擎工作正常。")
        return True
    else:
        print("⚠️  部分测试失败，请检查实现。")
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)