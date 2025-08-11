#!/usr/bin/env python3
"""
报告生成智能体版本对比测试

比较CrewAI版本和独立版本的功能差异和性能表现。
"""

import sys
import os
import pandas as pd
from datetime import datetime
import time
import traceback

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


def test_crewai_version():
    """测试CrewAI原版本"""
    print("=== 测试CrewAI原版本 ===")
    
    try:
        from agents.report_generation_agent import ReportGenerationAgent
        
        storage_manager = prepare_test_data()
        
        # 记录开始时间
        start_time = time.time()
        
        # 创建智能体
        agent = ReportGenerationAgent(storage_manager)
        
        print(f"✓ CrewAI版本初始化成功")
        print(f"✓ 工具数量: {len(agent.tools)}")
        print(f"✓ 是否有CrewAI Agent: {agent.agent is not None}")
        
        # 测试基本功能
        tools = agent.get_tools()
        print(f"✓ 工具列表: {[tool.name for tool in tools]}")
        
        # 测试报告导出功能
        test_report = {
            'metadata': {'generated_at': datetime.now().isoformat()},
            'summary': {'total_users': 100}
        }
        
        export_result = agent.export_report(test_report, 'json', 'test_output/crewai_report.json')
        print(f"✓ 导出功能: {export_result['status']}")
        
        # 记录结束时间
        end_time = time.time()
        execution_time = end_time - start_time
        
        return {
            'status': 'success',
            'execution_time': execution_time,
            'features': {
                'crewai_integration': agent.agent is not None,
                'tools_count': len(agent.tools),
                'export_support': export_result['status'] == 'success'
            }
        }
        
    except Exception as e:
        print(f"✗ CrewAI版本测试失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        return {
            'status': 'error',
            'error_message': str(e),
            'execution_time': 0
        }


def test_standalone_version():
    """测试独立版本"""
    print("\n=== 测试独立版本 ===")
    
    try:
        from agents.report_generation_agent_standalone import ReportGenerationAgent
        
        storage_manager = prepare_test_data()
        
        # 记录开始时间
        start_time = time.time()
        
        # 创建智能体
        agent = ReportGenerationAgent(storage_manager)
        
        print(f"✓ 独立版本初始化成功")
        print(f"✓ 工具数量: {len(agent.tools)}")
        
        # 测试基本功能
        tools = agent.get_tools()
        print(f"✓ 工具列表: {[tool.name for tool in tools]}")
        
        # 测试报告导出功能
        test_report = {
            'metadata': {'generated_at': datetime.now().isoformat()},
            'summary': {'total_users': 100}
        }
        
        export_result = agent.export_report(test_report, 'json', 'test_output/standalone_report.json')
        print(f"✓ 导出功能: {export_result['status']}")
        
        # 测试完整的报告生成流程
        print("测试完整报告生成...")
        report_result = agent.generate_comprehensive_report()
        print(f"✓ 完整报告生成: {report_result['status']}")
        
        if report_result['status'] == 'success':
            summary = report_result['summary']
            print(f"  - 数据质量评分: {summary.get('data_quality_score', 0):.2f}")
            print(f"  - 分析完整性: {summary.get('analysis_completeness', 0):.2f}")
            print(f"  - 总洞察数: {summary.get('total_insights', 0)}")
            print(f"  - 总建议数: {summary.get('total_recommendations', 0)}")
        
        # 记录结束时间
        end_time = time.time()
        execution_time = end_time - start_time
        
        return {
            'status': 'success',
            'execution_time': execution_time,
            'features': {
                'crewai_integration': False,
                'tools_count': len(agent.tools),
                'export_support': export_result['status'] == 'success',
                'full_report_generation': report_result['status'] == 'success'
            },
            'report_summary': report_result.get('summary', {}) if report_result['status'] == 'success' else {}
        }
        
    except Exception as e:
        print(f"✗ 独立版本测试失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        return {
            'status': 'error',
            'error_message': str(e),
            'execution_time': 0
        }


def test_crewai_fixed_version():
    """测试CrewAI修复版本"""
    print("\n=== 测试CrewAI修复版本 ===")
    
    try:
        from agents.report_generation_agent_fixed import ReportGenerationAgent
        
        storage_manager = prepare_test_data()
        
        # 记录开始时间
        start_time = time.time()
        
        # 创建智能体
        agent = ReportGenerationAgent(storage_manager)
        
        print(f"✓ CrewAI修复版本初始化成功")
        print(f"✓ 工具数量: {len(agent.tools)}")
        print(f"✓ CrewAI可用性: {agent.is_crewai_available()}")
        
        # 测试基本功能
        tools = agent.get_tools()
        print(f"✓ 工具列表: {[tool.name for tool in tools]}")
        
        # 测试报告导出功能
        test_report = {
            'metadata': {'generated_at': datetime.now().isoformat()},
            'summary': {'total_users': 100}
        }
        
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
        
        # 记录结束时间
        end_time = time.time()
        execution_time = end_time - start_time
        
        return {
            'status': 'success',
            'execution_time': execution_time,
            'features': {
                'crewai_integration': agent.is_crewai_available(),
                'tools_count': len(agent.tools),
                'export_support': export_result['status'] == 'success',
                'full_report_generation': report_result['status'] == 'success'
            },
            'report_summary': report_result.get('summary', {}) if report_result['status'] == 'success' else {}
        }
        
    except Exception as e:
        print(f"✗ CrewAI修复版本测试失败: {e}")
        print(f"错误详情: {traceback.format_exc()}")
        return {
            'status': 'error',
            'error_message': str(e),
            'execution_time': 0
        }


def compare_versions():
    """比较三个版本"""
    print("\n" + "="*60)
    print("版本对比分析")
    print("="*60)
    
    # 测试三个版本
    crewai_result = test_crewai_version()
    crewai_fixed_result = test_crewai_fixed_version()
    standalone_result = test_standalone_version()
    
    print("\n" + "="*60)
    print("对比结果汇总")
    print("="*60)
    
    # 功能对比
    print("\n📊 功能对比:")
    print(f"{'特性':<25} {'CrewAI原版':<15} {'CrewAI修复版':<15} {'独立版本':<15}")
    print("-" * 70)
    
    # 状态汇总
    versions = {
        'crewai': crewai_result,
        'crewai_fixed': crewai_fixed_result,
        'standalone': standalone_result
    }
    
    success_versions = [name for name, result in versions.items() if result['status'] == 'success']
    
    if len(success_versions) >= 2:
        # 显示成功版本的功能对比
        for feature in ['初始化成功', 'CrewAI集成', '工具数量', '导出支持', '完整报告生成']:
            row = f"{feature:<25}"
            
            # CrewAI原版
            if crewai_result['status'] == 'success':
                features = crewai_result['features']
                if feature == '初始化成功':
                    row += f"{'✓':<15}"
                elif feature == 'CrewAI集成':
                    row += f"{'✓' if features.get('crewai_integration', False) else '✗':<15}"
                elif feature == '工具数量':
                    row += f"{features.get('tools_count', 0):<15}"
                elif feature == '导出支持':
                    row += f"{'✓' if features.get('export_support', False) else '✗':<15}"
                elif feature == '完整报告生成':
                    row += f"{'✓' if features.get('full_report_generation', False) else '未测试':<15}"
            else:
                row += f"{'✗':<15}"
            
            # CrewAI修复版
            if crewai_fixed_result['status'] == 'success':
                features = crewai_fixed_result['features']
                if feature == '初始化成功':
                    row += f"{'✓':<15}"
                elif feature == 'CrewAI集成':
                    row += f"{'✓' if features.get('crewai_integration', False) else '兼容模式':<15}"
                elif feature == '工具数量':
                    row += f"{features.get('tools_count', 0):<15}"
                elif feature == '导出支持':
                    row += f"{'✓' if features.get('export_support', False) else '✗':<15}"
                elif feature == '完整报告生成':
                    row += f"{'✓' if features.get('full_report_generation', False) else '✗':<15}"
            else:
                row += f"{'✗':<15}"
            
            # 独立版本
            if standalone_result['status'] == 'success':
                features = standalone_result['features']
                if feature == '初始化成功':
                    row += f"{'✓':<15}"
                elif feature == 'CrewAI集成':
                    row += f"{'N/A':<15}"
                elif feature == '工具数量':
                    row += f"{features.get('tools_count', 0):<15}"
                elif feature == '导出支持':
                    row += f"{'✓' if features.get('export_support', False) else '✗':<15}"
                elif feature == '完整报告生成':
                    row += f"{'✓' if features.get('full_report_generation', False) else '✗':<15}"
            else:
                row += f"{'✗':<15}"
            
            print(row)
        
        # 性能对比
        print(f"\n⚡ 性能对比:")
        print(f"{'版本':<15} {'执行时间(秒)':<15} {'状态':<15}")
        print("-" * 45)
        print(f"{'CrewAI原版':<15} {crewai_result['execution_time']:.3f}s{'':<8} {crewai_result['status']:<15}")
        print(f"{'CrewAI修复版':<15} {crewai_fixed_result['execution_time']:.3f}s{'':<8} {crewai_fixed_result['status']:<15}")
        print(f"{'独立版本':<15} {standalone_result['execution_time']:.3f}s{'':<8} {standalone_result['status']:<15}")
        
    else:
        # 显示错误状态
        print(f"{'CrewAI原版状态':<25} {crewai_result['status']:<30}")
        print(f"{'CrewAI修复版状态':<25} {crewai_fixed_result['status']:<30}")
        print(f"{'独立版本状态':<25} {standalone_result['status']:<30}")
        
        for name, result in versions.items():
            if result['status'] == 'error':
                print(f"{name}错误: {result['error_message']}")
    
    # 使用建议
    print(f"\n💡 使用建议:")
    print("="*60)
    
    success_count = len(success_versions)
    
    if success_count == 3:
        print("✅ 三个版本都可以正常使用")
        print("\n🎯 选择建议:")
        print("• CrewAI修复版本（推荐）:")
        print("  - 解决了依赖兼容性问题")
        print("  - 支持CrewAI功能（如果环境允许）")
        print("  - 具备兼容模式，确保稳定运行")
        print("  - 功能最完整")
        print("\n• 独立版本:")
        print("  - 轻量级部署环境")
        print("  - 避免外部依赖冲突")
        print("  - 纯数据分析场景")
        print("  - 最快的启动和执行速度")
        print("\n• CrewAI原版本:")
        print("  - 仅在依赖环境完全兼容时使用")
        
    elif 'crewai_fixed' in success_versions and 'standalone' in success_versions:
        print("✅ CrewAI修复版本和独立版本都可以正常使用")
        print("🎯 推荐使用CrewAI修复版本:")
        print("  - 解决了原版本的依赖问题")
        print("  - 提供更好的错误处理")
        print("  - 支持CrewAI功能扩展")
        
    elif 'crewai_fixed' in success_versions:
        print("✅ 推荐使用CrewAI修复版本")
        print("  - 成功解决了依赖兼容性问题")
        print("  - 功能完整，性能稳定")
        
    elif 'standalone' in success_versions:
        print("✅ 推荐使用独立版本")
        print("  - 避免了CrewAI的依赖问题")
        print("  - 功能完整，性能稳定")
        
    else:
        print("❌ 所有版本都存在问题，需要进一步调试")
    
    return {
        'crewai_result': crewai_result,
        'crewai_fixed_result': crewai_fixed_result,
        'standalone_result': standalone_result
    }


def main():
    """主函数"""
    print("报告生成智能体版本对比测试")
    print("="*60)
    
    # 确保输出目录存在
    os.makedirs('test_output', exist_ok=True)
    
    # 执行对比测试
    results = compare_versions()
    
    # 输出最终结论
    print(f"\n🏁 测试完成!")
    
    crewai_success = results['crewai_result']['status'] == 'success'
    crewai_fixed_success = results['crewai_fixed_result']['status'] == 'success'
    standalone_success = results['standalone_result']['status'] == 'success'
    
    success_count = sum([crewai_success, crewai_fixed_success, standalone_success])
    
    if success_count == 3:
        print("✅ 三个版本都可以正常使用，推荐使用CrewAI修复版本")
        return True
    elif crewai_fixed_success and standalone_success:
        print("✅ CrewAI修复版本和独立版本都可以正常使用，推荐使用CrewAI修复版本")
        return True
    elif crewai_fixed_success:
        print("✅ CrewAI修复版本可以正常使用，问题已解决！")
        return True
    elif standalone_success:
        print("✅ 独立版本可以正常使用")
        return True
    elif crewai_success:
        print("✅ CrewAI原版本可以正常使用")
        return True
    else:
        print("❌ 所有版本都存在问题")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)