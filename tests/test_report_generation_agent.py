"""
报告生成智能体测试模块

测试ReportGenerationAgent类的各项功能，包括报告编译、洞察生成和建议生成。
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

from agents.report_generation_agent import (
    ReportGenerationAgent,
    ReportCompilerTool,
    InsightGeneratorTool,
    RecommendationEngineTool
)
from tools.data_storage_manager import DataStorageManager


class TestReportCompilerTool:
    """测试报告编译工具"""
    
    def setup_method(self):
        """测试前置设置"""
        self.mock_storage = Mock(spec=DataStorageManager)
        self.compiler_tool = ReportCompilerTool(self.mock_storage)
    
    def test_init(self):
        """测试初始化"""
        assert self.compiler_tool.name == "report_compiler"
        assert "编译和汇总" in self.compiler_tool.description
        assert self.compiler_tool.storage_manager is not None
    
    @patch('agents.report_generation_agent.EventAnalysisEngine')
    @patch('agents.report_generation_agent.ConversionAnalysisEngine')
    @patch('agents.report_generation_agent.RetentionAnalysisEngine')
    @patch('agents.report_generation_agent.UserSegmentationEngine')
    @patch('agents.report_generation_agent.PathAnalysisEngine')
    def test_run_success(self, mock_path_engine, mock_seg_engine, mock_ret_engine, 
                        mock_conv_engine, mock_event_engine):
        """测试成功编译报告"""
        # 设置mock返回值
        self.mock_storage.get_statistics.return_value = {
            'events_count': 1000,
            'users_count': 100,
            'sessions_count': 200,
            'date_range': '2024-01-01 to 2024-01-31'
        }
        
        # 设置各个引擎的mock返回值
        mock_event_engine.return_value.analyze_event_frequency.return_value = {
            'top_events': [{'event_name': 'page_view', 'count': 500, 'percentage': 0.5}]
        }
        mock_event_engine.return_value.analyze_event_trends.return_value = {
            'trending_events': [{'event_name': 'click', 'trend': 'up'}]
        }
        mock_event_engine.return_value.analyze_event_correlation.return_value = {
            'strong_correlations': [{'events': ['A', 'B'], 'correlation': 0.8}]
        }
        
        mock_conv_engine.return_value.analyze_conversion_funnel.return_value = {
            'overall_conversion_rate': 0.15,
            'bottleneck_step': 'checkout'
        }
        mock_conv_engine.return_value.analyze_conversion_paths.return_value = {
            'top_paths': [{'path': ['A', 'B', 'C'], 'conversion_rate': 0.2}]
        }
        
        mock_ret_engine.return_value.analyze_retention_rate.return_value = {
            'day1_retention': 0.4,
            'day7_retention': 0.2,
            'day30_retention': 0.1
        }
        mock_ret_engine.return_value.analyze_cohort_retention.return_value = {
            'best_performing_cohort': '2024-01'
        }
        
        mock_seg_engine.return_value.segment_users.return_value = {
            'segments': {'segment_1': [], 'segment_2': []}
        }
        mock_seg_engine.return_value.profile_segments.return_value = {
            'largest_segment': 'segment_1',
            'most_valuable_segment': 'segment_2'
        }
        
        mock_path_engine.return_value.mine_user_paths.return_value = {
            'common_paths': [{'path': ['A', 'B'], 'support': 0.1}],
            'optimal_paths': [{'path': ['A', 'C'], 'efficiency': 0.9}]
        }
        mock_path_engine.return_value.analyze_user_flow.return_value = {
            'drop_off_points': ['step_2', 'step_4']
        }
        
        # 执行测试
        result = self.compiler_tool._run()
        
        # 验证结果
        assert result['status'] == 'success'
        assert 'report' in result
        assert 'metadata' in result['report']
        assert 'executive_summary' in result['report']
        assert 'detailed_analysis' in result['report']
        
        # 验证详细分析包含所有模块
        detailed = result['report']['detailed_analysis']
        assert 'event_analysis' in detailed
        assert 'conversion_analysis' in detailed
        assert 'retention_analysis' in detailed
        assert 'user_segmentation' in detailed
        assert 'path_analysis' in detailed
    
    def test_run_with_analysis_scope(self):
        """测试带分析范围的报告编译"""
        analysis_scope = {
            'date_range': ('2024-01-01', '2024-01-31'),
            'event_types': ['page_view', 'click'],
            'user_segments': ['segment_1']
        }
        
        self.mock_storage.get_statistics.return_value = {
            'events_count': 500,
            'users_count': 50,
            'sessions_count': 100
        }
        
        with patch.multiple(
            'agents.report_generation_agent',
            EventAnalysisEngine=Mock(),
            ConversionAnalysisEngine=Mock(),
            RetentionAnalysisEngine=Mock(),
            UserSegmentationEngine=Mock(),
            PathAnalysisEngine=Mock()
        ):
            result = self.compiler_tool._run(analysis_scope)
            
            assert result['status'] == 'success'
            assert result['report']['metadata']['analysis_scope'] == analysis_scope
    
    def test_get_data_summary(self):
        """测试数据概览获取"""
        self.mock_storage.get_statistics.return_value = {
            'events_count': 1000,
            'users_count': 100,
            'sessions_count': 200,
            'date_range': '2024-01-01 to 2024-01-31'
        }
        
        summary = self.compiler_tool._get_data_summary()
        
        assert summary['total_events'] == 1000
        assert summary['unique_users'] == 100
        assert summary['total_sessions'] == 200
        assert summary['date_range'] == '2024-01-01 to 2024-01-31'
    
    def test_get_data_summary_error(self):
        """测试数据概览获取错误处理"""
        self.mock_storage.get_statistics.side_effect = Exception("Database error")
        
        summary = self.compiler_tool._get_data_summary()
        
        assert summary == {}
    
    def test_calculate_data_quality_score(self):
        """测试数据质量评分计算"""
        report = {
            'metadata': {
                'data_summary': {
                    'total_events': 1000,
                    'unique_users': 100,
                    'total_sessions': 200,
                    'date_range': '2024-01-01 to 2024-01-31'
                }
            }
        }
        
        score = self.compiler_tool._calculate_data_quality_score(report)
        
        assert 0.0 <= score <= 1.0
        assert score == 1.0  # 所有数据都存在
    
    def test_calculate_analysis_completeness(self):
        """测试分析完整性评分计算"""
        detailed = {
            'event_analysis': {'data': 'test'},
            'conversion_analysis': {'data': 'test'},
            'retention_analysis': {'error': 'failed'},
            'user_segmentation': {'data': 'test'},
            'path_analysis': {'data': 'test'}
        }
        
        score = self.compiler_tool._calculate_analysis_completeness(detailed)
        
        assert score == 0.8  # 4/5 成功


class TestInsightGeneratorTool:
    """测试洞察生成工具"""
    
    def setup_method(self):
        """测试前置设置"""
        self.insight_tool = InsightGeneratorTool()
    
    def test_init(self):
        """测试初始化"""
        assert self.insight_tool.name == "insight_generator"
        assert "业务洞察" in self.insight_tool.description
    
    def test_run_success(self):
        """测试成功生成洞察"""
        compiled_report = {
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
        
        result = self.insight_tool._run(compiled_report)
        
        assert result['status'] == 'success'
        assert 'insights' in result
        assert 'quality_score' in result
        assert 'total_insights' in result
        
        insights = result['insights']
        assert 'key_insights' in insights
        assert 'performance_insights' in insights
        assert 'user_behavior_insights' in insights
        assert 'opportunity_insights' in insights
        assert 'risk_insights' in insights
    
    def test_generate_key_insights(self):
        """测试关键洞察生成"""
        executive = {
            'key_metrics': {
                'unique_users': 1000,
                'conversion_rate': 0.15,
                'day1_retention': 0.4
            }
        }
        detailed = {}
        
        insights = self.insight_tool._generate_key_insights(executive, detailed)
        
        assert len(insights) > 0
        assert any(insight['type'] == 'user_scale' for insight in insights)
        assert any(insight['type'] == 'conversion_performance' for insight in insights)
        assert any(insight['type'] == 'retention_strength' for insight in insights)
    
    def test_generate_key_insights_low_performance(self):
        """测试低性能指标的关键洞察生成"""
        executive = {
            'key_metrics': {
                'unique_users': 100,
                'conversion_rate': 0.02,  # 低转化率
                'day1_retention': 0.15    # 低留存率
            }
        }
        detailed = {}
        
        insights = self.insight_tool._generate_key_insights(executive, detailed)
        
        assert any(insight['type'] == 'conversion_concern' for insight in insights)
        assert any(insight['type'] == 'retention_weakness' for insight in insights)
    
    def test_calculate_insight_quality(self):
        """测试洞察质量评分计算"""
        insights = {
            'key_insights': [{'type': 'test1'}, {'type': 'test2'}],
            'performance_insights': [{'type': 'test3'}],
            'user_behavior_insights': [],
            'opportunity_insights': [{'type': 'test4'}],
            'risk_insights': []
        }
        
        score = self.insight_tool._calculate_insight_quality(insights)
        
        assert 0.0 <= score <= 1.0
        assert score > 0  # 有洞察存在


class TestRecommendationEngineTool:
    """测试建议生成工具"""
    
    def setup_method(self):
        """测试前置设置"""
        self.recommendation_tool = RecommendationEngineTool()
    
    def test_init(self):
        """测试初始化"""
        assert self.recommendation_tool.name == "recommendation_engine"
        assert "行动建议" in self.recommendation_tool.description
    
    def test_run_success(self):
        """测试成功生成建议"""
        insights = {
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
        
        compiled_report = {
            'executive_summary': {
                'data_quality_score': 0.7,
                'analysis_completeness': 0.6
            }
        }
        
        result = self.recommendation_tool._run(insights, compiled_report)
        
        assert result['status'] == 'success'
        assert 'recommendations' in result
        assert 'prioritized_recommendations' in result
        assert 'total_recommendations' in result
        
        recommendations = result['recommendations']
        assert 'immediate_actions' in recommendations
        assert 'short_term_improvements' in recommendations
        assert 'long_term_strategies' in recommendations
        assert 'technical_optimizations' in recommendations
        assert 'business_opportunities' in recommendations
    
    def test_generate_immediate_actions(self):
        """测试立即行动建议生成"""
        key_insights = [
            {'type': 'conversion_concern', 'impact': 'high'},
            {'type': 'retention_weakness', 'impact': 'high'},
            {'type': 'user_scale', 'impact': 'medium'}
        ]
        
        actions = self.recommendation_tool._generate_immediate_actions(key_insights)
        
        assert len(actions) >= 2  # 应该有转化和留存的建议
        assert any('转化' in action['title'] for action in actions)
        assert any('留存' in action['title'] for action in actions)
        
        for action in actions:
            assert 'title' in action
            assert 'description' in action
            assert 'priority' in action
            assert 'timeline' in action
    
    def test_prioritize_recommendations(self):
        """测试建议优先级排序"""
        recommendations = {
            'immediate_actions': [
                {'title': 'High Priority', 'priority': 'high', 'expected_impact': 'high', 'effort': 'low'},
                {'title': 'Low Priority', 'priority': 'low', 'expected_impact': 'low', 'effort': 'high'}
            ],
            'short_term_improvements': [
                {'title': 'Medium Priority', 'priority': 'medium', 'expected_impact': 'medium', 'effort': 'medium'}
            ],
            'long_term_strategies': [],
            'technical_optimizations': [],
            'business_opportunities': []
        }
        
        prioritized = self.recommendation_tool._prioritize_recommendations(recommendations)
        
        assert len(prioritized) <= 10
        assert prioritized[0]['title'] == 'High Priority'  # 最高优先级应该排在前面
        
        for rec in prioritized:
            assert 'category' in rec


class TestReportGenerationAgent:
    """测试报告生成智能体"""
    
    def setup_method(self):
        """测试前置设置"""
        self.mock_storage = Mock(spec=DataStorageManager)
        self.agent = ReportGenerationAgent(self.mock_storage)
    
    def test_init(self):
        """测试初始化"""
        assert self.agent.storage_manager is not None
        assert len(self.agent.tools) == 3
        assert any(tool.name == "report_compiler" for tool in self.agent.tools)
        assert any(tool.name == "insight_generator" for tool in self.agent.tools)
        assert any(tool.name == "recommendation_engine" for tool in self.agent.tools)
    
    @patch('agents.report_generation_agent.ReportCompilerTool')
    @patch('agents.report_generation_agent.InsightGeneratorTool')
    @patch('agents.report_generation_agent.RecommendationEngineTool')
    def test_generate_comprehensive_report_success(self, mock_rec_tool, mock_insight_tool, mock_compiler_tool):
        """测试成功生成综合报告"""
        # 设置mock返回值
        mock_compiled_report = {
            'metadata': {'generated_at': '2024-01-01T00:00:00'},
            'executive_summary': {'key_metrics': {}},
            'detailed_analysis': {},
            'raw_results': {}
        }
        
        mock_compiler_tool.return_value._run.return_value = {
            'status': 'success',
            'report': mock_compiled_report
        }
        
        mock_insights_result = {
            'status': 'success',
            'insights': {'key_insights': []}
        }
        
        mock_insight_tool.return_value._run.return_value = mock_insights_result
        
        mock_recommendations_result = {
            'status': 'success',
            'recommendations': {'immediate_actions': []},
            'prioritized_recommendations': []
        }
        
        mock_rec_tool.return_value._run.return_value = mock_recommendations_result
        
        # 执行测试
        result = self.agent.generate_comprehensive_report()
        
        # 验证结果
        assert result['status'] == 'success'
        assert 'report' in result
        assert 'summary' in result
        assert 'export_formats' in result
        
        report = result['report']
        assert 'metadata' in report
        assert 'executive_summary' in report
        assert 'business_insights' in report
        assert 'recommendations' in report
        assert 'prioritized_actions' in report
        assert 'detailed_analysis' in report
        assert 'raw_results' in report
    
    @patch('agents.report_generation_agent.ReportCompilerTool')
    def test_generate_comprehensive_report_compiler_error(self, mock_compiler_tool):
        """测试编译器错误处理"""
        mock_compiler_tool.return_value._run.return_value = {
            'status': 'error',
            'error_message': 'Compilation failed'
        }
        
        result = self.agent.generate_comprehensive_report()
        
        assert result['status'] == 'error'
        assert 'error_message' in result
    
    def test_export_report_json(self):
        """测试JSON格式报告导出"""
        report = {
            'metadata': {'generated_at': '2024-01-01T00:00:00'},
            'summary': {'total_users': 100}
        }
        
        with patch('builtins.open', create=True) as mock_open:
            with patch('os.makedirs'):
                with patch('json.dump') as mock_json_dump:
                    result = self.agent.export_report(report, 'json', 'test_report.json')
                    
                    assert result['status'] == 'success'
                    assert result['format'] == 'json'
                    assert 'output_path' in result
                    mock_json_dump.assert_called_once()
    
    def test_export_report_unsupported_format(self):
        """测试不支持的导出格式"""
        report = {'data': 'test'}
        
        result = self.agent.export_report(report, 'xml')
        
        assert result['status'] == 'error'
        assert '不支持的导出格式' in result['error_message']
    
    def test_generate_report_summary(self):
        """测试报告摘要生成"""
        report = {
            'metadata': {
                'generated_at': '2024-01-01T00:00:00',
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
        
        summary = self.agent._generate_report_summary(report)
        
        assert summary['generated_at'] == '2024-01-01T00:00:00'
        assert summary['data_period'] == '2024-01-01 to 2024-01-31'
        assert summary['total_users'] == 1000
        assert summary['total_events'] == 5000
        assert summary['total_insights'] == 2
        assert summary['total_recommendations'] == 2
        assert summary['data_quality_score'] == 0.8
        assert summary['analysis_completeness'] == 0.9
    
    def test_get_tools(self):
        """测试获取工具列表"""
        tools = self.agent.get_tools()
        
        assert len(tools) == 3
        assert all(hasattr(tool, 'name') for tool in tools)
        assert all(hasattr(tool, 'description') for tool in tools)


if __name__ == '__main__':
    pytest.main([__file__])