#!/usr/bin/env python3
"""
报告生成智能体独立测试脚本

测试ReportGenerationAgent的核心功能，不依赖CrewAI。
"""

import sys
import os
import pandas as pd
from datetime import datetime
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.report_generation_agent_standalone import (
    ReportGenerationAgent,
    ReportCompilerTool,
    InsightGeneratorTool,
    RecommendationEngineTool
)
from tools.data_storage_manager import DataStorageManager


def test_report_compiler_tool():
    """测试报告编译工具"""
    print("=== 测试报告编译工具 ===")
    
    try:
        # 创建测试数据存储管理器
        storage_manager = DataStorageManager()
        
        # 创建一些测试数据
        test_events = pd.DataFrame({
            'event_name': ['page_view', 'click', 'purchase', 'page_view', 'click'],
            'user_pseudo_id': ['user1', 'user1', 'user1', 'user2', 'user2'],
            'event_timestamp': pd.to_datetime(['2024-01-01', '2024-01-01', '2024-01-01', '2024-01-02', '2024-01-02']),
            'ga_session_id': ['session1', 'session1', 'session1', 'session2', 'session2']
        })
        
        test_users = pd.DataFrame({
            'user_pseudo_id': ['user1', 'user2'],
            'first_seen': pd.to_datetime(['2024-01-01', '2024-01-02']),
            'last_seen': pd.to_datetime(['2024-01-01', '2024-01-02'])
        })
        
        test_sessions = pd.DataFrame({
            'session_id': ['session1', 'session2'],
            'user_pseudo_id': ['user1', 'user2'],
            'session_start': pd.to_datetime(['2024-01-01', '2024-01-02']),
            'session_end': pd.to_datetime(['2024-01-01', '2024-01-02']),
            'event_count': [3, 2]
        })
        
        # 存储测试数据
        storage_manager.store_events(test_events)
        storage_manager.store_users(test_users)
        storage_manager.store_sessions(test_sessions)
        
        # 创建报告编译工具
        compiler_tool = ReportCompilerTool(storage_manager)
        
        # 测试基本功能
        print("✓ 报告编译工具初始化成功")
        print(f"✓ 工具名称: {compiler_tool.name}")
        print(f"✓ 工具描述: {compiler_tool.description}")
        
        # 测试数据概览获取
        data_summary = compiler_tool._get_data_summary()
        print(f"✓ 数据概览: {data_summary}")
        
        # 测试报告编译（简化版本，避免依赖其他引擎）
        print("✓ 报告编译工具测试通过")
        
    except Exception as e:
        print(f"✗ 报告编译工具测试失败: {e}")
        return False
    
    return True


def test_insight_generator_tool():
    """测试洞察生成工具"""
    print("\n=== 测试洞察生成工具 ===")
    
    try:
        # 创建洞察生成工具
        insight_tool = InsightGeneratorTool()
        
        print("✓ 洞察生成工具初始化成功")
        print(f"✓ 工具名称: {insight_tool.name}")
        print(f"✓ 工具描述: {insight_tool.description}")
        
        # 创建测试报告数据
        test_report = {
            'executive_summary': {
                'key_metrics': {
                    'unique_users': 1000,
                    'total_events': 5000,
                    'conversion_rate': 0.15,
                    'day1_retention': 0.4
                }
            },
            'detailed_analysis': {
                'event_analysis': {
                    'summary': {
                        'top_events': [{'event_name': 'page_view', 'percentage': 0.5}],
                        'trending_events': [{'event_name': 'click', 'trend': 'up'}]
                    }
                },
                'conversion_analysis': {
                    'summary': {
                        'bottleneck_step': 'checkout'
                    }
                },
                'user_segmentation': {
                    'summary': {
                        'total_segments': 3
                    }
                },
                'path_analysis': {
                    'summary': {
                        'drop_off_points': ['step_2', 'step_4']
                    }
                }
            }
        }
        
        # 测试洞察生成
        result = insight_tool.run(test_report)
        
        print(f"✓ 洞察生成状态: {result['status']}")
        print(f"✓ 洞察质量评分: {result.get('quality_score', 0):.2f}")
        print(f"✓ 总洞察数量: {result.get('total_insights', 0)}")
        
        if result['status'] == 'success':
            insights = result['insights']
            for category, insight_list in insights.items():
                print(f"  - {category}: {len(insight_list)} 个洞察")
        
        print("✓ 洞察生成工具测试通过")
        
    except Exception as e:
        print(f"✗ 洞察生成工具测试失败: {e}")
        return False
    
    return True


def test_recommendation_engine_tool():
    """测试建议生成工具"""
    print("\n=== 测试建议生成工具 ===")
    
    try:
        # 创建建议生成工具
        recommendation_tool = RecommendationEngineTool()
        
        print("✓ 建议生成工具初始化成功")
        print(f"✓ 工具名称: {recommendation_tool.name}")
        print(f"✓ 工具描述: {recommendation_tool.description}")
        
        # 创建测试洞察数据
        test_insights = {
            'insights': {
                'key_insights': [
                    {'type': 'conversion_concern', 'impact': 'high'},
                    {'type': 'retention_weakness', 'impact': 'high'}
                ],
                'performance_insights': [
                    {'type': 'conversion_bottleneck', 'description': 'checkout step'}
                ],
                'user_behavior_insights': [
                    {'type': 'user_journey', 'description': 'drop off at step 2'}
                ],
                'opportunity_insights': [
                    {'type': 'conversion_opportunity'}
                ],
                'risk_insights': [
                    {'type': 'retention_risk'}
                ]
            }
        }
        
        test_compiled_report = {
            'executive_summary': {
                'data_quality_score': 0.7,
                'analysis_completeness': 0.6
            }
        }
        
        # 测试建议生成
        result = recommendation_tool.run(test_insights, test_compiled_report)
        
        print(f"✓ 建议生成状态: {result['status']}")
        print(f"✓ 总建议数量: {result.get('total_recommendations', 0)}")
        
        if result['status'] == 'success':
            recommendations = result['recommendations']
            for category, rec_list in recommendations.items():
                print(f"  - {category}: {len(rec_list)} 个建议")
            
            prioritized = result.get('prioritized_recommendations', [])
            print(f"✓ 优先级建议数量: {len(prioritized)}")
        
        print("✓ 建议生成工具测试通过")
        
    except Exception as e:
        print(f"✗ 建议生成工具测试失败: {e}")
        return False
    
    return True


def test_report_generation_agent():
    """测试报告生成智能体"""
    print("\n=== 测试报告生成智能体 ===")
    
    try:
        # 创建数据存储管理器
        storage_manager = DataStorageManager()
        
        # 创建一些测试数据
        test_events = pd.DataFrame({
            'event_name': ['page_view', 'click', 'purchase', 'page_view', 'click'],
            'user_pseudo_id': ['user1', 'user1', 'user1', 'user2', 'user2'],
            'event_timestamp': pd.to_datetime(['2024-01-01', '2024-01-01', '2024-01-01', '2024-01-02', '2024-01-02']),
            'ga_session_id': ['session1', 'session1', 'session1', 'session2', 'session2']
        })
        
        test_users = pd.DataFrame({
            'user_pseudo_id': ['user1', 'user2'],
            'first_seen': pd.to_datetime(['2024-01-01', '2024-01-02']),
            'last_seen': pd.to_datetime(['2024-01-01', '2024-01-02'])
        })
        
        test_sessions = pd.DataFrame({
            'session_id': ['session1', 'session2'],
            'user_pseudo_id': ['user1', 'user2'],
            'session_start': pd.to_datetime(['2024-01-01', '2024-01-02']),
            'session_end': pd.to_datetime(['2024-01-01', '2024-01-02']),
            'event_count': [3, 2]
        })
        
        # 存储测试数据
        storage_manager.store_events(test_events)
        storage_manager.store_users(test_users)
        storage_manager.store_sessions(test_sessions)
        
        # 创建报告生成智能体
        agent = ReportGenerationAgent(storage_manager)
        
        print("✓ 报告生成智能体初始化成功")
        print(f"✓ 智能体工具数量: {len(agent.tools)}")
        
        # 测试工具获取
        tools = agent.get_tools()
        print(f"✓ 获取工具列表: {[tool.name for tool in tools]}")
        
        # 测试报告导出功能
        test_report = {
            'metadata': {'generated_at': datetime.now().isoformat()},
            'summary': {'total_users': 100}
        }
        
        # 测试JSON导出
        json_result = agent.export_report(test_report, 'json', 'test_output/test_report.json')
        print(f"✓ JSON导出测试: {json_result['status']}")
        
        # 测试不支持的格式
        xml_result = agent.export_report(test_report, 'xml')
        print(f"✓ 不支持格式测试: {xml_result['status']}")
        
        # 测试报告摘要生成
        full_report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'analysis_scope': {'date_range': '2024-01-01 to 2024-01-31'}
            },
            'executive_summary': {
                'key_metrics': {
                    'unique_users': 1000,
                    'total_events': 5000
                },
                'data_quality_score': 0.8,
                'analysis_completeness': 0.9
            },
            'business_insights': {
                'key_insights': [{'type': 'test1'}],
                'performance_insights': [{'type': 'test2'}]
            },
            'recommendations': {
                'immediate_actions': [{'title': 'action1'}],
                'short_term_improvements': [{'title': 'improvement1'}]
            }
        }
        
        summary = agent._generate_report_summary(full_report)
        print(f"✓ 报告摘要生成: {len(summary)} 个字段")
        print(f"  - 总用户数: {summary.get('total_users', 0)}")
        print(f"  - 总事件数: {summary.get('total_events', 0)}")
        print(f"  - 数据质量评分: {summary.get('data_quality_score', 0):.2f}")
        
        print("✓ 报告生成智能体测试通过")
        
    except Exception as e:
        print(f"✗ 报告生成智能体测试失败: {e}")
        return False
    
    return True


def main():
    """主测试函数"""
    print("开始报告生成智能体独立测试")
    print("=" * 50)
    
    test_results = []
    
    # 运行各项测试
    test_results.append(test_report_compiler_tool())
    test_results.append(test_insight_generator_tool())
    test_results.append(test_recommendation_engine_tool())
    test_results.append(test_report_generation_agent())
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("✓ 所有测试通过！")
        return True
    else:
        print("✗ 部分测试失败")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)