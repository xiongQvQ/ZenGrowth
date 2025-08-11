"""
转化分析智能体独立测试

不依赖CrewAI的独立测试，验证转化分析智能体的核心功能。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock

# 直接导入引擎和存储管理器
from engines.conversion_analysis_engine import ConversionAnalysisEngine
from tools.data_storage_manager import DataStorageManager


def create_sample_events_data():
    """创建示例事件数据"""
    np.random.seed(42)
    
    # 创建用户ID
    user_ids = [f"user_{i}" for i in range(100)]
    
    events = []
    base_time = datetime.now() - timedelta(days=7)
    
    for user_id in user_ids:
        user_events = []
        current_time = base_time + timedelta(hours=np.random.randint(0, 168))
        
        # 模拟转化漏斗：page_view -> view_item -> add_to_cart -> begin_checkout -> purchase
        funnel_steps = ['page_view', 'view_item', 'add_to_cart', 'begin_checkout', 'purchase']
        
        # 每个用户都有page_view
        user_events.append({
            'user_pseudo_id': user_id,
            'event_name': 'page_view',
            'event_datetime': current_time,
            'event_timestamp': int(current_time.timestamp() * 1000000)
        })
        current_time += timedelta(minutes=np.random.randint(1, 30))
        
        # 80%的用户会view_item
        if np.random.random() < 0.8:
            user_events.append({
                'user_pseudo_id': user_id,
                'event_name': 'view_item',
                'event_datetime': current_time,
                'event_timestamp': int(current_time.timestamp() * 1000000)
            })
            current_time += timedelta(minutes=np.random.randint(1, 60))
            
            # 50%的view_item用户会add_to_cart
            if np.random.random() < 0.5:
                user_events.append({
                    'user_pseudo_id': user_id,
                    'event_name': 'add_to_cart',
                    'event_datetime': current_time,
                    'event_timestamp': int(current_time.timestamp() * 1000000)
                })
                current_time += timedelta(minutes=np.random.randint(1, 120))
                
                # 60%的add_to_cart用户会begin_checkout
                if np.random.random() < 0.6:
                    user_events.append({
                        'user_pseudo_id': user_id,
                        'event_name': 'begin_checkout',
                        'event_datetime': current_time,
                        'event_timestamp': int(current_time.timestamp() * 1000000)
                    })
                    current_time += timedelta(minutes=np.random.randint(1, 30))
                    
                    # 70%的begin_checkout用户会purchase
                    if np.random.random() < 0.7:
                        user_events.append({
                            'user_pseudo_id': user_id,
                            'event_name': 'purchase',
                            'event_datetime': current_time,
                            'event_timestamp': int(current_time.timestamp() * 1000000)
                        })
        
        events.extend(user_events)
    
    return pd.DataFrame(events)


def test_conversion_analysis_engine():
    """测试转化分析引擎基本功能"""
    print("测试转化分析引擎...")
    
    # 创建示例数据
    events_data = create_sample_events_data()
    print(f"创建了 {len(events_data)} 条事件数据")
    
    # 创建模拟存储管理器
    mock_storage = Mock(spec=DataStorageManager)
    mock_storage.get_data.return_value = events_data
    
    # 创建转化分析引擎
    engine = ConversionAnalysisEngine(mock_storage)
    
    # 测试漏斗构建
    print("\n1. 测试漏斗构建...")
    funnel_steps = ['page_view', 'view_item', 'add_to_cart', 'begin_checkout', 'purchase']
    funnel = engine.build_conversion_funnel(
        funnel_steps=funnel_steps,
        funnel_name="purchase_funnel"
    )
    
    print(f"漏斗名称: {funnel.funnel_name}")
    print(f"总用户数: {funnel.total_users_entered}")
    print(f"转化用户数: {funnel.total_users_converted}")
    print(f"整体转化率: {funnel.overall_conversion_rate:.3f}")
    print(f"瓶颈步骤: {funnel.bottleneck_step}")
    
    print("\n漏斗步骤详情:")
    for step in funnel.steps:
        print(f"  {step.step_name}: {step.total_users} 用户, 转化率 {step.conversion_rate:.3f}, 流失率 {step.drop_off_rate:.3f}")
    
    # 测试转化率计算
    print("\n2. 测试转化率计算...")
    conversion_result = engine.calculate_conversion_rates()
    
    print(f"分析了 {len(conversion_result.funnels)} 个漏斗")
    print("转化指标:")
    for metric, value in conversion_result.conversion_metrics.items():
        print(f"  {metric}: {value:.3f}")
    
    # 测试流失点识别
    print("\n3. 测试流失点识别...")
    drop_off_analysis = engine.identify_drop_off_points(funnel_steps=funnel_steps)
    
    print("主要流失点:")
    for drop_off in drop_off_analysis.get('major_drop_off_points', []):
        print(f"  {drop_off['step_name']}: 流失率 {drop_off['drop_off_rate']:.3f}")
    
    print("流失洞察:")
    for insight in drop_off_analysis.get('drop_off_insights', []):
        print(f"  - {insight}")
    
    return True


def test_conversion_analysis_agent_tools():
    """测试转化分析智能体工具（不依赖CrewAI）"""
    print("\n测试转化分析智能体工具...")
    
    # 创建示例数据
    events_data = create_sample_events_data()
    
    # 创建模拟存储管理器
    mock_storage = Mock(spec=DataStorageManager)
    mock_storage.get_data.return_value = events_data
    
    # 导入工具类（避免CrewAI依赖）
    try:
        from agents.conversion_analysis_agent_standalone import (
            FunnelAnalysisTool,
            ConversionRateAnalysisTool,
            BottleneckIdentificationTool,
            ConversionPathAnalysisTool
        )
        
        # 测试漏斗分析工具
        print("\n1. 测试漏斗分析工具...")
        funnel_tool = FunnelAnalysisTool(mock_storage)
        funnel_result = funnel_tool.run(
            funnel_steps=['page_view', 'view_item', 'add_to_cart', 'purchase'],
            funnel_name='test_funnel'
        )
        
        print(f"状态: {funnel_result['status']}")
        print(f"分析类型: {funnel_result['analysis_type']}")
        if funnel_result['status'] == 'success':
            funnel = funnel_result['funnel']
            print(f"漏斗转化率: {funnel['overall_conversion_rate']:.3f}")
            print(f"洞察数量: {len(funnel_result['insights'])}")
            for insight in funnel_result['insights'][:3]:
                print(f"  - {insight}")
        
        # 测试转化率分析工具
        print("\n2. 测试转化率分析工具...")
        conversion_tool = ConversionRateAnalysisTool(mock_storage)
        conversion_result = conversion_tool.run()
        
        print(f"状态: {conversion_result['status']}")
        if conversion_result['status'] == 'success':
            results = conversion_result['results']
            print(f"分析漏斗数量: {len(results['funnels'])}")
            print(f"转化指标数量: {len(results['conversion_metrics'])}")
        
        # 测试瓶颈识别工具
        print("\n3. 测试瓶颈识别工具...")
        bottleneck_tool = BottleneckIdentificationTool(mock_storage)
        bottleneck_result = bottleneck_tool.run(['page_view', 'view_item', 'purchase'])
        
        print(f"状态: {bottleneck_result['status']}")
        if bottleneck_result['status'] == 'success':
            print(f"建议数量: {len(bottleneck_result['recommendations'])}")
            for rec in bottleneck_result['recommendations'][:2]:
                print(f"  - {rec}")
        
        # 测试转化路径分析工具
        print("\n4. 测试转化路径分析工具...")
        path_tool = ConversionPathAnalysisTool(mock_storage)
        path_result = path_tool.run(['page_view', 'purchase'])
        
        print(f"状态: {path_result['status']}")
        if path_result['status'] == 'success':
            path_analysis = path_result['path_analysis']
            print(f"最优路径步骤数: {len(path_analysis['optimal_path']['steps'])}")
        
        return True
        
    except ImportError as e:
        print(f"导入工具类失败: {e}")
        return False


def test_conversion_analysis_agent_standalone():
    """测试转化分析智能体独立模式"""
    print("\n测试转化分析智能体独立模式...")
    
    try:
        # 创建示例数据
        events_data = create_sample_events_data()
        
        # 创建模拟存储管理器
        mock_storage = Mock(spec=DataStorageManager)
        mock_storage.get_data.return_value = events_data
        
        # 创建智能体（独立模式）
        from agents.conversion_analysis_agent_standalone import ConversionAnalysisAgent
        agent = ConversionAnalysisAgent(mock_storage)
        
        print(f"智能体工具数量: {len(agent.tools)}")
        
        # 测试漏斗分析
        print("\n1. 测试智能体漏斗分析...")
        funnel_result = agent.analyze_funnel(
            funnel_steps=['page_view', 'view_item', 'add_to_cart', 'purchase'],
            funnel_name='agent_test_funnel'
        )
        
        print(f"状态: {funnel_result['status']}")
        if funnel_result['status'] == 'success':
            print(f"转化率: {funnel_result['funnel']['overall_conversion_rate']:.3f}")
        
        # 测试转化率分析
        print("\n2. 测试智能体转化率分析...")
        conversion_result = agent.analyze_conversion_rates()
        
        print(f"状态: {conversion_result['status']}")
        if conversion_result['status'] == 'success':
            print(f"分析漏斗数量: {len(conversion_result['results']['funnels'])}")
        
        # 测试瓶颈识别
        print("\n3. 测试智能体瓶颈识别...")
        bottleneck_result = agent.identify_bottlenecks(['page_view', 'purchase'])
        
        print(f"状态: {bottleneck_result['status']}")
        if bottleneck_result['status'] == 'success':
            print(f"建议数量: {len(bottleneck_result['recommendations'])}")
        
        # 测试综合分析
        print("\n4. 测试智能体综合分析...")
        comprehensive_result = agent.comprehensive_conversion_analysis()
        
        print(f"状态: {comprehensive_result['status']}")
        if comprehensive_result['status'] == 'success':
            print(f"漏斗分析数量: {len(comprehensive_result['funnel_analyses'])}")
            print(f"瓶颈分析数量: {len(comprehensive_result['bottleneck_analyses'])}")
        
        return True
        
    except Exception as e:
        print(f"智能体测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("转化分析智能体独立测试")
    print("=" * 60)
    
    tests = [
        ("转化分析引擎", test_conversion_analysis_engine),
        ("转化分析工具", test_conversion_analysis_agent_tools),
        ("转化分析智能体", test_conversion_analysis_agent_standalone)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"\n✅ {test_name} 测试完成: {'通过' if result else '失败'}")
        except Exception as e:
            results.append((test_name, False))
            print(f"\n❌ {test_name} 测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    # 总结
    print(f"\n{'='*60}")
    print("测试总结:")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！转化分析智能体实现成功！")
        return True
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，需要修复")
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)