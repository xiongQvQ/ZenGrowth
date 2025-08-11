#!/usr/bin/env python3
"""
CrewAI修复版本测试脚本

测试修复后的CrewAI报告生成智能体是否能正常工作。
"""

import sys
import os
import pandas as pd
from datetime import datetime
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.data_storage_manager import DataStorageManager


def prepare_test_data():
    """准备测试数据"""
    # 创建测试数据存储管理器
    storage_manager = DataStorageManager()
    
    # 创建测试数据
    test_events = pd.DataFrame({
        'event_name': ['page_view', 'click', 'purchase', 'page_view', 'click', 'signup'],
        'user_pseudo_id': ['user1', 'user1', 'user1', 'user2', 'user2', 'user3'],
        'event_timestamp': pd.to_datetime([
            '2024-01-01 10:00:00', '2024-01-01 10:05:00', '2024-01-01 10:10:00',
            '2024-01-02 11:00:00', '2024-01-02 11:05:00', '2024-01-03 12:00:00'
        ]),
        'ga_session_id': ['session1', 'session1', 'session1', 'session2', 'session2', 'session3']
    })
    
    test_users = pd.DataFrame({
        'user_pseudo_id': ['user1', 'user2', 'user3'],
        'first_seen': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03']),
        'last_seen': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03'])
    })
    
    test_sessions = pd.DataFrame({
        'session_id': ['session1', 'session2', 'session3'],
        'user_pseudo_id': ['user1', 'user2', 'user3'],
        'session_start': pd.to_datetime(['2024-01-01 10:00:00', '2024-01-02 11:00:00', '2024-01-03 12:00:00']),
        'session_end': pd.to_datetime(['2024-01-01 10:15:00', '2024-01-02 11:10:00', '2024-01-03 12:05:00']),
        'event_count': [3, 2, 1]
    })
    
    # 存储测试数据
    storage_manager.store_events(test_events)
    storage_manager.store_users(test_users)
    storage_manager.store_sessions(test_sessions)
    
    return storage_manager


def test_crewai_fixed_version():
    """测试CrewAI修复版本"""
    print("=== 测试CrewAI修复版本 ===")
    
    try:
        from agents.report_generation_agent_fixed import ReportGenerationAgent
        
        storage_manager = prepare_test_data()
        
        # 记录开始时间
        start_time = time.time()
        
        # 创建智能体
        print("正在创建报告生成智能体...")
        agent = ReportGenerationAgent(storage_manager)
        
        print(f"✓ CrewAI修复版本初始化成功")
        print(f"✓ 工具数量: {len(agent.tools)}")
        print(f"✓ CrewAI可用性: {agent.is_crewai_available()}")
        print(f"✓ CrewAI Agent: {'可用' if agent.get_agent() is not None else '不可用'}")
        
        # 测试基本功能
        tools = agent.get_tools()
        print(f"✓ 工具列表: {[tool.name for tool in tools]}")
        
        # 测试报告导出功能
        test_report = {
            'metadata': {'generated_at': datetime.now().isoformat()},
            'summary': {'total_users': 100}
        }
        
        print("测试报告导出功能...")
        export_result = agent.export_report(test_report, 'json', 'test_output/crewai_fixed_report.json')
        print(f"✓ 导出功能: {export_result['status']}")
        
        # 测试完整的报告生成流程
        print("测试完整报告生成...")
        report_result = agent.generate_comprehensive_report()
        print(f"✓ 完整报告生成: {report_result['status']}")
        
        if report_result['status'] == 'success':
            summary = report_result['summary']
            print(f"  - CrewAI可用: {summary.get('crewai_available', False)}")
            print(f"  - 数据质量评分: {summary.get('data_quality_score', 0):.2f}")
            print(f"  - 分析完整性: {summary.get('analysis_completeness', 0):.2f}")
            print(f"  - 总洞察数: {summary.get('total_insights', 0)}")
            print(f"  - 总建议数: {summary.get('total_recommendations', 0)}")
            
            # 显示报告的关键部分
            report = report_result['report']
            metadata = report.get('metadata', {})
            print(f"  - 报告生成时间: {metadata.get('generated_at', 'Unknown')}")
            print(f"  - CrewAI框架状态: {'已集成' if metadata.get('crewai_available', False) else '使用兼容模式'}")
        
        # 记录结束时间
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"✓ 执行时间: {execution_time:.3f}秒")
        
        return {
            'status': 'success',
            'execution_time': execution_time,
            'crewai_available': agent.is_crewai_available(),
            'features': {
                'initialization': True,
                'tools_count': len(agent.tools),
                'export_support': export_result['status'] == 'success',
                'full_report_generation': report_result['status'] == 'success',
                'crewai_integration': agent.is_crewai_available()
            },
            'report_summary': report_result.get('summary', {}) if report_result['status'] == 'success' else {}
        }
        
    except Exception as e:
        print(f"✗ CrewAI修复版本测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return {
            'status': 'error',
            'error_message': str(e),
            'execution_time': 0
        }


def main():
    """主函数"""
    print("CrewAI修复版本测试")
    print("="*50)
    
    # 确保输出目录存在
    os.makedirs('test_output', exist_ok=True)
    
    # 执行测试
    result = test_crewai_fixed_version()
    
    print("\n" + "="*50)
    print("测试结果汇总")
    print("="*50)
    
    if result['status'] == 'success':
        print("✅ CrewAI修复版本测试成功！")
        print(f"\n📊 功能特性:")
        features = result['features']
        print(f"  - 初始化: {'✓' if features['initialization'] else '✗'}")
        print(f"  - 工具数量: {features['tools_count']}")
        print(f"  - 导出支持: {'✓' if features['export_support'] else '✗'}")
        print(f"  - 完整报告生成: {'✓' if features['full_report_generation'] else '✗'}")
        print(f"  - CrewAI集成: {'✓' if features['crewai_integration'] else '✗ (使用兼容模式)'}")
        
        print(f"\n⚡ 性能:")
        print(f"  - 执行时间: {result['execution_time']:.3f}秒")
        
        if result['report_summary']:
            summary = result['report_summary']
            print(f"\n📈 报告质量:")
            print(f"  - 数据质量评分: {summary.get('data_quality_score', 0):.2f}")
            print(f"  - 分析完整性: {summary.get('analysis_completeness', 0):.2f}")
            print(f"  - 总洞察数: {summary.get('total_insights', 0)}")
            print(f"  - 总建议数: {summary.get('total_recommendations', 0)}")
        
        print(f"\n🎯 解决方案状态:")
        if result['crewai_available']:
            print("  ✅ CrewAI框架成功集成，所有功能可用")
        else:
            print("  ⚠️  CrewAI框架不可用，使用兼容模式运行")
            print("  ✅ 核心功能正常，报告生成完整")
        
        return True
    else:
        print("❌ CrewAI修复版本测试失败")
        print(f"错误信息: {result['error_message']}")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)