"""
留存分析引擎集成测试

验证RetentionAnalysisEngine的基本功能是否正常工作。
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.retention_analysis_engine import RetentionAnalysisEngine
from tools.data_storage_manager import DataStorageManager


def create_retention_sample_data():
    """创建留存分析示例数据"""
    print("创建留存分析示例数据...")
    
    np.random.seed(42)
    events = []
    users = [f'user_{i}' for i in range(100)]
    
    # 创建90天的数据，模拟真实的用户留存模式
    start_date = datetime.now() - timedelta(days=90)
    
    for user_id in users:
        # 每个用户的首次活动时间（分布在前30天）
        first_activity = start_date + timedelta(days=np.random.randint(0, 30))
        
        # 模拟用户留存模式：
        # - 20%的用户是高留存用户（留存率0.7-0.9）
        # - 30%的用户是中等留存用户（留存率0.3-0.6）
        # - 50%的用户是低留存用户（留存率0.1-0.3）
        user_type = np.random.choice(['high', 'medium', 'low'], p=[0.2, 0.3, 0.5])
        
        if user_type == 'high':
            base_retention = np.random.uniform(0.7, 0.9)
            decay_rate = 0.98  # 慢衰减
        elif user_type == 'medium':
            base_retention = np.random.uniform(0.3, 0.6)
            decay_rate = 0.95  # 中等衰减
        else:
            base_retention = np.random.uniform(0.1, 0.3)
            decay_rate = 0.90  # 快衰减
            
        current_date = first_activity
        current_retention = base_retention
        day_offset = 0
        
        while current_date <= datetime.now() and day_offset < 60:
            # 决定用户是否在这一天活跃
            if np.random.random() < current_retention:
                # 用户活跃，生成1-8个事件
                daily_events = np.random.randint(1, 9)
                
                for _ in range(daily_events):
                    event_time = current_date + timedelta(
                        hours=np.random.randint(0, 24),
                        minutes=np.random.randint(0, 60)
                    )
                    
                    event = {
                        'user_pseudo_id': user_id,
                        'event_name': np.random.choice([
                            'page_view', 'login', 'purchase', 'add_to_cart', 'search'
                        ], p=[0.4, 0.2, 0.1, 0.2, 0.1]),
                        'event_timestamp': int(event_time.timestamp() * 1000000),
                        'event_datetime': event_time,
                        'event_date': current_date.strftime('%Y%m%d'),
                        'platform': np.random.choice(['web', 'mobile'], p=[0.6, 0.4])
                    }
                    events.append(event)
            
            # 留存概率随时间递减
            current_retention *= decay_rate
            current_date += timedelta(days=1)
            day_offset += 1
            
    events_df = pd.DataFrame(events)
    print(f"创建了 {len(events_df)} 条事件数据，涉及 {events_df['user_pseudo_id'].nunique()} 个用户")
    
    # 创建用户数据
    users_data = []
    for user_id in users:
        user_events = events_df[events_df['user_pseudo_id'] == user_id]
        if not user_events.empty:
            user = {
                'user_pseudo_id': user_id,
                'platform': user_events['platform'].iloc[0],
                'device_category': np.random.choice(['desktop', 'mobile', 'tablet']),
                'geo_country': np.random.choice(['US', 'UK', 'CA', 'DE', 'FR']),
                'first_seen': user_events['event_datetime'].min(),
                'last_seen': user_events['event_datetime'].max(),
                'total_events': len(user_events)
            }
            users_data.append(user)
    
    users_df = pd.DataFrame(users_data)
    print(f"创建了 {len(users_df)} 个用户数据")
    
    return events_df, users_df


def test_user_cohort_building(engine, events_df):
    """测试用户队列构建"""
    print("\n=== 测试用户队列构建 ===")
    
    try:
        # 测试月度队列
        monthly_cohorts = engine.build_user_cohorts(
            events_df, 
            cohort_period='monthly',
            min_cohort_size=5
        )
        
        print(f"月度队列数量: {len(monthly_cohorts)}")
        for cohort_period, user_ids in monthly_cohorts.items():
            print(f"  {cohort_period}: {len(user_ids)} 用户")
            
        # 测试周度队列
        weekly_cohorts = engine.build_user_cohorts(
            events_df,
            cohort_period='weekly',
            min_cohort_size=3
        )
        
        print(f"周度队列数量: {len(weekly_cohorts)}")
        
        # 测试日度队列
        daily_cohorts = engine.build_user_cohorts(
            events_df,
            cohort_period='daily',
            min_cohort_size=1
        )
        
        print(f"日度队列数量: {len(daily_cohorts)}")
        
        print("✅ 用户队列构建测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 用户队列构建测试失败: {e}")
        return False


def test_monthly_retention_analysis(engine, events_df):
    """测试月度留存分析"""
    print("\n=== 测试月度留存分析 ===")
    
    try:
        result = engine.analyze_monthly_retention(events_df, max_months=6)
        
        print(f"分析类型: {result.analysis_type}")
        print(f"队列数量: {len(result.cohorts)}")
        
        # 显示整体留存率
        print("整体留存率:")
        for period, rate in result.overall_retention_rates.items():
            print(f"  第{period}月: {rate:.3f} ({rate*100:.1f}%)")
            
        # 显示队列详情
        print("\n队列详情:")
        for i, cohort in enumerate(result.cohorts[:3]):  # 只显示前3个队列
            print(f"  队列 {cohort.cohort_period}:")
            print(f"    队列大小: {cohort.cohort_size}")
            print(f"    留存率: {[f'{r:.3f}' for r in cohort.retention_rates[:4]]}")
            
        # 显示摘要统计
        print(f"\n摘要统计:")
        stats = result.summary_stats
        print(f"  总队列数: {stats.get('total_cohorts', 0)}")
        print(f"  总用户数: {stats.get('total_users', 0)}")
        print(f"  平均队列大小: {stats.get('avg_cohort_size', 0):.1f}")
        print(f"  平均留存率: {stats.get('avg_retention_rate', 0):.3f}")
        
        print("✅ 月度留存分析测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 月度留存分析测试失败: {e}")
        return False


def test_weekly_retention_analysis(engine, events_df):
    """测试周度留存分析"""
    print("\n=== 测试周度留存分析 ===")
    
    try:
        result = engine.analyze_weekly_retention(events_df, max_weeks=8)
        
        print(f"分析类型: {result.analysis_type}")
        print(f"队列数量: {len(result.cohorts)}")
        
        # 显示整体留存率
        print("整体留存率:")
        for period, rate in list(result.overall_retention_rates.items())[:5]:
            print(f"  第{period}周: {rate:.3f} ({rate*100:.1f}%)")
            
        print("✅ 周度留存分析测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 周度留存分析测试失败: {e}")
        return False


def test_daily_retention_analysis(engine, events_df):
    """测试日度留存分析"""
    print("\n=== 测试日度留存分析 ===")
    
    try:
        result = engine.analyze_daily_retention(events_df, max_days=14)
        
        print(f"分析类型: {result.analysis_type}")
        print(f"队列数量: {len(result.cohorts)}")
        
        # 显示整体留存率
        print("整体留存率:")
        for period, rate in list(result.overall_retention_rates.items())[:8]:
            print(f"  第{period}天: {rate:.3f} ({rate*100:.1f}%)")
            
        print("✅ 日度留存分析测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 日度留存分析测试失败: {e}")
        return False


def test_user_retention_profiles(engine, events_df, users_df):
    """测试用户留存档案"""
    print("\n=== 测试用户留存档案 ===")
    
    try:
        profiles = engine.create_user_retention_profiles(events_df, users_df)
        
        print(f"创建了 {len(profiles)} 个用户留存档案")
        
        # 分析流失风险分布
        risk_scores = [profile.churn_risk_score for profile in profiles]
        high_risk_users = sum(1 for score in risk_scores if score > 70)
        medium_risk_users = sum(1 for score in risk_scores if 30 <= score <= 70)
        low_risk_users = sum(1 for score in risk_scores if score < 30)
        
        print(f"流失风险分布:")
        print(f"  高风险用户 (>70): {high_risk_users} ({high_risk_users/len(profiles)*100:.1f}%)")
        print(f"  中风险用户 (30-70): {medium_risk_users} ({medium_risk_users/len(profiles)*100:.1f}%)")
        print(f"  低风险用户 (<30): {low_risk_users} ({low_risk_users/len(profiles)*100:.1f}%)")
        
        # 显示几个示例档案
        print(f"\n示例用户档案:")
        for i, profile in enumerate(profiles[:3]):
            print(f"  用户 {profile.user_id}:")
            print(f"    活跃天数: {profile.total_active_days}")
            print(f"    流失风险: {profile.churn_risk_score:.1f}")
            print(f"    活动频率: {profile.activity_pattern.get('activity_frequency', 0):.3f}")
            print(f"    最近趋势: {profile.activity_pattern.get('recent_activity_trend', 'N/A')}")
            
        print("✅ 用户留存档案测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 用户留存档案测试失败: {e}")
        return False


def test_retention_insights(engine, events_df):
    """测试留存分析洞察"""
    print("\n=== 测试留存分析洞察 ===")
    
    try:
        # 先进行留存分析
        retention_result = engine.analyze_monthly_retention(events_df, max_months=6)
        
        # 获取洞察
        insights = engine.get_retention_insights(retention_result)
        
        print("关键指标:")
        key_metrics = insights.get('key_metrics', {})
        for metric, value in key_metrics.items():
            print(f"  {metric}: {value:.3f}")
            
        print(f"\n趋势分析:")
        trends = insights.get('trends', {})
        for trend_name, trend_value in trends.items():
            print(f"  {trend_name}: {trend_value}")
            
        print(f"\n改进建议:")
        recommendations = insights.get('recommendations', [])
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"  {i}. {rec}")
            
        print(f"\n风险因素:")
        risk_factors = insights.get('risk_factors', [])
        for i, risk in enumerate(risk_factors[:3], 1):
            print(f"  {i}. {risk}")
            
        print("✅ 留存分析洞察测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 留存分析洞察测试失败: {e}")
        return False


def test_analysis_summary(engine):
    """测试分析摘要"""
    print("\n=== 测试分析摘要 ===")
    
    try:
        summary = engine.get_analysis_summary()
        
        print("分析摘要:")
        print(f"  总事件数: {summary.get('total_events', 'N/A')}")
        print(f"  独立用户数: {summary.get('unique_users', 'N/A')}")
        print(f"  数据跨度: {summary.get('data_span_days', 'N/A')} 天")
        print(f"  日期范围: {summary.get('date_range', {}).get('start', 'N/A')} 到 {summary.get('date_range', {}).get('end', 'N/A')}")
        
        print(f"  估算队列数:")
        estimated = summary.get('estimated_cohorts', {})
        print(f"    日度队列: {estimated.get('daily', 0)}")
        print(f"    周度队列: {estimated.get('weekly', 0)}")
        print(f"    月度队列: {estimated.get('monthly', 0)}")
        
        print("✅ 分析摘要测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 分析摘要测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始留存分析引擎集成测试...")
    
    # 创建示例数据
    events_df, users_df = create_retention_sample_data()
    
    # 创建存储管理器并存储数据
    print("\n设置存储管理器...")
    storage_manager = DataStorageManager()
    storage_manager.store_events(events_df)
    storage_manager.store_users(users_df)
    
    # 创建留存分析引擎
    print("初始化留存分析引擎...")
    engine = RetentionAnalysisEngine(storage_manager)
    
    # 运行测试
    test_results = []
    
    test_results.append(test_user_cohort_building(engine, events_df))
    test_results.append(test_monthly_retention_analysis(engine, events_df))
    test_results.append(test_weekly_retention_analysis(engine, events_df))
    test_results.append(test_daily_retention_analysis(engine, events_df))
    test_results.append(test_user_retention_profiles(engine, events_df, users_df))
    test_results.append(test_retention_insights(engine, events_df))
    test_results.append(test_analysis_summary(engine))
    
    # 总结测试结果
    print(f"\n=== 测试总结 ===")
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"通过测试: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！留存分析引擎工作正常。")
        return True
    else:
        print("⚠️  部分测试失败，请检查实现。")
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)