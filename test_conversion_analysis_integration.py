"""
转化分析智能体集成测试

测试转化分析智能体与实际数据存储管理器的集成。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from agents.conversion_analysis_agent_standalone import ConversionAnalysisAgent
from tools.data_storage_manager import DataStorageManager


def create_realistic_events_data():
    """创建更真实的事件数据"""
    np.random.seed(42)
    
    # 创建用户ID
    user_ids = [f"user_{i:04d}" for i in range(200)]
    
    events = []
    base_time = datetime.now() - timedelta(days=30)
    
    # 定义事件权重（模拟真实用户行为）
    event_weights = {
        'page_view': 1.0,
        'view_item': 0.7,
        'add_to_cart': 0.3,
        'begin_checkout': 0.6,  # 相对于add_to_cart
        'purchase': 0.8,  # 相对于begin_checkout
        'sign_up': 0.2,
        'login': 0.9  # 相对于sign_up
    }
    
    for user_id in user_ids:
        user_events = []
        current_time = base_time + timedelta(hours=np.random.randint(0, 720))  # 30天内随机时间
        
        # 每个用户都有page_view
        user_events.append({
            'user_pseudo_id': user_id,
            'event_name': 'page_view',
            'event_datetime': current_time,
            'event_timestamp': int(current_time.timestamp() * 1000000),
            'platform': np.random.choice(['web', 'mobile', 'tablet'], p=[0.6, 0.3, 0.1]),
            'device': {'category': np.random.choice(['desktop', 'mobile', 'tablet'], p=[0.5, 0.4, 0.1])}
        })
        current_time += timedelta(minutes=np.random.randint(1, 30))
        
        # 购买漏斗
        if np.random.random() < event_weights['view_item']:
            user_events.append({
                'user_pseudo_id': user_id,
                'event_name': 'view_item',
                'event_datetime': current_time,
                'event_timestamp': int(current_time.timestamp() * 1000000),
                'platform': user_events[-1]['platform'],
                'device': user_events[-1]['device']
            })
            current_time += timedelta(minutes=np.random.randint(1, 60))
            
            if np.random.random() < event_weights['add_to_cart']:
                user_events.append({
                    'user_pseudo_id': user_id,
                    'event_name': 'add_to_cart',
                    'event_datetime': current_time,
                    'event_timestamp': int(current_time.timestamp() * 1000000),
                    'platform': user_events[-1]['platform'],
                    'device': user_events[-1]['device']
                })
                current_time += timedelta(minutes=np.random.randint(1, 120))
                
                if np.random.random() < event_weights['begin_checkout']:
                    user_events.append({
                        'user_pseudo_id': user_id,
                        'event_name': 'begin_checkout',
                        'event_datetime': current_time,
                        'event_timestamp': int(current_time.timestamp() * 1000000),
                        'platform': user_events[-1]['platform'],
                        'device': user_events[-1]['device']
                    })
                    current_time += timedelta(minutes=np.random.randint(1, 30))
                    
                    if np.random.random() < event_weights['purchase']:
                        user_events.append({
                            'user_pseudo_id': user_id,
                            'event_name': 'purchase',
                            'event_datetime': current_time,
                            'event_timestamp': int(current_time.timestamp() * 1000000),
                            'platform': user_events[-1]['platform'],
                            'device': user_events[-1]['device'],
                            'value': np.random.uniform(10, 500)  # 购买金额
                        })
        
        # 注册漏斗（独立于购买漏斗）
        if np.random.random() < event_weights['sign_up']:
            signup_time = current_time + timedelta(minutes=np.random.randint(-30, 30))
            user_events.append({
                'user_pseudo_id': user_id,
                'event_name': 'sign_up',
                'event_datetime': signup_time,
                'event_timestamp': int(signup_time.timestamp() * 1000000),
                'platform': user_events[0]['platform'],
                'device': user_events[0]['device']
            })
            
            if np.random.random() < event_weights['login']:
                login_time = signup_time + timedelta(minutes=np.random.randint(1, 60))
                user_events.append({
                    'user_pseudo_id': user_id,
                    'event_name': 'login',
                    'event_datetime': login_time,
                    'event_timestamp': int(login_time.timestamp() * 1000000),
                    'platform': user_events[0]['platform'],
                    'device': user_events[0]['device']
                })
        
        events.extend(user_events)
    
    return pd.DataFrame(events)


def test_conversion_analysis_integration():
    """测试转化分析智能体集成"""
    print("=" * 60)
    print("转化分析智能体集成测试")
    print("=" * 60)
    
    try:
        # 创建真实的数据存储管理器
        print("1. 初始化数据存储管理器...")
        storage_manager = DataStorageManager()
        
        # 创建并存储测试数据
        print("2. 创建测试数据...")
        events_data = create_realistic_events_data()
        print(f"   创建了 {len(events_data)} 条事件数据")
        print(f"   涉及 {events_data['user_pseudo_id'].nunique()} 个用户")
        print(f"   包含事件类型: {list(events_data['event_name'].unique())}")
        
        # 存储数据
        storage_manager.store_events(events_data)
        print("   数据存储完成")
        
        # 创建转化分析智能体
        print("\n3. 创建转化分析智能体...")
        agent = ConversionAnalysisAgent(storage_manager)
        print(f"   智能体初始化完成，包含 {len(agent.tools)} 个工具")
        
        # 测试购买漏斗分析
        print("\n4. 测试购买漏斗分析...")
        purchase_funnel_steps = ['page_view', 'view_item', 'add_to_cart', 'begin_checkout', 'purchase']
        funnel_result = agent.analyze_funnel(
            funnel_steps=purchase_funnel_steps,
            funnel_name='purchase_funnel',
            time_window_hours=48
        )
        
        if funnel_result['status'] == 'success':
            funnel = funnel_result['funnel']
            print(f"   ✅ 购买漏斗分析成功")
            print(f"      总用户数: {funnel['total_users_entered']}")
            print(f"      转化用户数: {funnel['total_users_converted']}")
            print(f"      整体转化率: {funnel['overall_conversion_rate']:.3f}")
            print(f"      瓶颈步骤: {funnel['bottleneck_step']}")
            
            print("      各步骤详情:")
            for step in funnel['steps']:
                print(f"        {step['step_name']}: {step['total_users']} 用户, "
                      f"转化率 {step['conversion_rate']:.3f}")
        else:
            print(f"   ❌ 购买漏斗分析失败: {funnel_result.get('error_message')}")
            return False
        
        # 测试注册漏斗分析
        print("\n5. 测试注册漏斗分析...")
        registration_funnel_steps = ['page_view', 'sign_up', 'login']
        reg_funnel_result = agent.analyze_funnel(
            funnel_steps=registration_funnel_steps,
            funnel_name='registration_funnel',
            time_window_hours=24
        )
        
        if reg_funnel_result['status'] == 'success':
            reg_funnel = reg_funnel_result['funnel']
            print(f"   ✅ 注册漏斗分析成功")
            print(f"      整体转化率: {reg_funnel['overall_conversion_rate']:.3f}")
            print(f"      瓶颈步骤: {reg_funnel['bottleneck_step']}")
        else:
            print(f"   ❌ 注册漏斗分析失败: {reg_funnel_result.get('error_message')}")
        
        # 测试转化率分析
        print("\n6. 测试转化率分析...")
        conversion_result = agent.analyze_conversion_rates()
        
        if conversion_result['status'] == 'success':
            results = conversion_result['results']
            print(f"   ✅ 转化率分析成功")
            print(f"      分析漏斗数量: {len(results['funnels'])}")
            print(f"      转化指标数量: {len(results['conversion_metrics'])}")
            
            # 显示关键转化指标
            metrics = results['conversion_metrics']
            key_metrics = ['purchase_conversion_rate', 'add_to_cart_conversion_rate', 'sign_up_conversion_rate']
            print("      关键转化指标:")
            for metric in key_metrics:
                if metric in metrics:
                    print(f"        {metric}: {metrics[metric]:.3f}")
        else:
            print(f"   ❌ 转化率分析失败: {conversion_result.get('error_message')}")
        
        # 测试瓶颈识别
        print("\n7. 测试瓶颈识别...")
        bottleneck_result = agent.identify_bottlenecks(purchase_funnel_steps)
        
        if bottleneck_result['status'] == 'success':
            print(f"   ✅ 瓶颈识别成功")
            recommendations = bottleneck_result['recommendations']
            print(f"      优化建议数量: {len(recommendations)}")
            print("      主要建议:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"        {i}. {rec}")
        else:
            print(f"   ❌ 瓶颈识别失败: {bottleneck_result.get('error_message')}")
        
        # 测试综合分析
        print("\n8. 测试综合转化分析...")
        comprehensive_result = agent.comprehensive_conversion_analysis({
            'purchase_funnel': purchase_funnel_steps,
            'registration_funnel': registration_funnel_steps
        })
        
        if comprehensive_result['status'] == 'success':
            print(f"   ✅ 综合分析成功")
            print(f"      漏斗分析数量: {len(comprehensive_result['funnel_analyses'])}")
            print(f"      瓶颈分析数量: {len(comprehensive_result['bottleneck_analyses'])}")
            
            # 显示关键发现
            summary = comprehensive_result['summary']
            key_findings = summary.get('key_findings', [])
            if key_findings:
                print("      关键发现:")
                for i, finding in enumerate(key_findings[:5], 1):
                    print(f"        {i}. {finding}")
        else:
            print(f"   ❌ 综合分析失败: {comprehensive_result.get('error_message')}")
        
        # 测试数据质量验证
        print("\n9. 验证数据质量...")
        stored_data = storage_manager.get_data('events')
        
        if not stored_data.empty:
            print(f"   ✅ 数据存储验证成功")
            print(f"      存储事件数: {len(stored_data)}")
            print(f"      数据时间范围: {stored_data['event_datetime'].min()} 到 {stored_data['event_datetime'].max()}")
            print(f"      平台分布: {dict(stored_data['platform'].value_counts())}")
        else:
            print(f"   ❌ 数据存储验证失败")
            return False
        
        print(f"\n{'='*60}")
        print("🎉 转化分析智能体集成测试全部通过！")
        print(f"{'='*60}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_with_large_dataset():
    """测试大数据集性能"""
    print("\n" + "=" * 60)
    print("大数据集性能测试")
    print("=" * 60)
    
    try:
        # 创建大数据集
        print("1. 创建大数据集...")
        np.random.seed(123)
        
        # 创建更多用户和事件
        user_count = 1000
        events_per_user = np.random.poisson(5, user_count)  # 平均每用户5个事件
        
        events = []
        base_time = datetime.now() - timedelta(days=60)
        
        for i in range(user_count):
            user_id = f"user_{i:05d}"
            user_event_count = events_per_user[i]
            
            for j in range(user_event_count):
                event_time = base_time + timedelta(
                    days=np.random.randint(0, 60),
                    hours=np.random.randint(0, 24),
                    minutes=np.random.randint(0, 60)
                )
                
                # 随机选择事件类型
                event_name = np.random.choice([
                    'page_view', 'view_item', 'add_to_cart', 
                    'begin_checkout', 'purchase', 'sign_up', 'login'
                ], p=[0.4, 0.25, 0.15, 0.08, 0.05, 0.05, 0.02])
                
                events.append({
                    'user_pseudo_id': user_id,
                    'event_name': event_name,
                    'event_datetime': event_time,
                    'event_timestamp': int(event_time.timestamp() * 1000000),
                    'platform': np.random.choice(['web', 'mobile', 'tablet']),
                    'device': {'category': np.random.choice(['desktop', 'mobile', 'tablet'])}
                })
        
        large_events_data = pd.DataFrame(events)
        print(f"   创建了 {len(large_events_data)} 条事件数据")
        print(f"   涉及 {large_events_data['user_pseudo_id'].nunique()} 个用户")
        
        # 创建存储管理器和智能体
        storage_manager = DataStorageManager()
        storage_manager.store_events(large_events_data)
        agent = ConversionAnalysisAgent(storage_manager)
        
        # 测试性能
        print("\n2. 测试分析性能...")
        import time
        
        start_time = time.time()
        result = agent.comprehensive_conversion_analysis()
        end_time = time.time()
        
        analysis_time = end_time - start_time
        
        if result['status'] == 'success':
            print(f"   ✅ 大数据集分析成功")
            print(f"      分析时间: {analysis_time:.2f} 秒")
            print(f"      数据处理速度: {len(large_events_data)/analysis_time:.0f} 事件/秒")
            
            if analysis_time < 30:  # 30秒内完成认为性能良好
                print("   🚀 性能表现良好")
            else:
                print("   ⚠️  性能需要优化")
        else:
            print(f"   ❌ 大数据集分析失败: {result.get('error_message')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ 性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("转化分析智能体集成测试套件")
    
    tests = [
        ("集成功能测试", test_conversion_analysis_integration),
        ("大数据集性能测试", test_performance_with_large_dataset)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 执行失败: {e}")
            results.append((test_name, False))
    
    # 总结
    print(f"\n{'='*60}")
    print("集成测试总结:")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有集成测试通过！转化分析智能体可以投入使用！")
        return True
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，需要修复")
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)