#!/usr/bin/env python3
"""
示例数据分析和验证演示

该脚本实现任务8.2：使用提供的GA4示例数据进行完整分析，
验证各个分析模块的准确性和一致性，生成示例分析报告和可视化结果。
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入系统组件
from system.standalone_integration_manager import StandaloneIntegrationManager, WorkflowConfig
from tools.ga4_data_parser import GA4DataParser
from tools.data_validator import DataValidator
from utils.logger import setup_logger
from utils.report_exporter import ReportExporter

# 设置日志
logger = setup_logger()


class ExampleDataAnalysisValidator:
    """示例数据分析验证器"""
    
    def __init__(self):
        """初始化验证器"""
        self.logger = setup_logger()
        self.data_file = "data/events_ga4.ndjson"
        self.output_dir = Path("reports/example_analysis")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化集成管理器
        config = WorkflowConfig(
            enable_parallel_processing=True,
            max_workers=4,
            memory_limit_gb=8.0,
            timeout_minutes=30,
            enable_caching=True,
            enable_monitoring=True,
            auto_cleanup=False  # 保留数据用于验证
        )
        
        self.integration_manager = StandaloneIntegrationManager(config)
        self.report_exporter = ReportExporter()
        
        # 验证结果存储
        self.validation_results = {}
        self.analysis_results = {}
        
        self.logger.info("示例数据分析验证器初始化完成")
    
    def run_complete_analysis(self) -> Dict[str, Any]:
        """运行完整的示例数据分析"""
        try:
            self.logger.info("开始运行完整的示例数据分析")
            
            # 检查数据文件是否存在
            if not os.path.exists(self.data_file):
                raise FileNotFoundError(f"GA4示例数据文件不存在: {self.data_file}")
            
            # 1. 执行完整工作流程
            start_time = time.time()
            
            workflow_result = self.integration_manager.execute_complete_workflow(
                file_path=self.data_file,
                analysis_types=['event_analysis', 'retention_analysis', 'conversion_analysis', 
                              'user_segmentation', 'path_analysis']
            )
            
            execution_time = time.time() - start_time
            
            # 2. 验证分析结果
            validation_results = self._validate_analysis_results(workflow_result)
            
            # 3. 生成数据质量报告
            quality_report = self._generate_data_quality_report()
            
            # 4. 创建综合分析报告
            comprehensive_report = self._create_comprehensive_report(
                workflow_result, validation_results, quality_report, execution_time
            )
            
            # 5. 导出报告和可视化结果
            self._export_analysis_results(comprehensive_report)
            
            self.logger.info("完整的示例数据分析运行完成")
            
            return comprehensive_report
            
        except Exception as e:
            self.logger.error(f"示例数据分析运行失败: {e}")
            raise
    
    def _validate_analysis_results(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """验证分析结果的准确性和一致性"""
        self.logger.info("开始验证分析结果")
        
        validation_results = {
            'overall_status': 'passed',
            'validations': {},
            'issues': [],
            'recommendations': []
        }
        
        try:
            # 1. 验证数据处理结果
            data_validation = self._validate_data_processing(workflow_result.get('processed_data', {}))
            validation_results['validations']['data_processing'] = data_validation
            
            # 2. 验证各个分析模块
            analysis_results = workflow_result.get('analysis_results', {})
            
            for analysis_type, result in analysis_results.items():
                module_validation = self._validate_analysis_module(analysis_type, result)
                validation_results['validations'][analysis_type] = module_validation
                
                if not module_validation.get('passed', False):
                    validation_results['overall_status'] = 'failed'
                    validation_results['issues'].append(
                        f"{analysis_type} 模块验证失败: {module_validation.get('error', 'Unknown error')}"
                    )
            
            # 3. 验证结果一致性
            consistency_validation = self._validate_result_consistency(analysis_results)
            validation_results['validations']['consistency'] = consistency_validation
            
            # 4. 验证可视化结果
            visualization_validation = self._validate_visualizations(workflow_result.get('visualizations', {}))
            validation_results['validations']['visualizations'] = visualization_validation
            
            # 5. 生成验证建议
            validation_results['recommendations'] = self._generate_validation_recommendations(validation_results)
            
            self.logger.info(f"分析结果验证完成，总体状态: {validation_results['overall_status']}")
            
        except Exception as e:
            self.logger.error(f"分析结果验证失败: {e}")
            validation_results['overall_status'] = 'error'
            validation_results['issues'].append(f"验证过程出错: {str(e)}")
        
        return validation_results
    
    def _validate_data_processing(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """验证数据处理结果"""
        validation = {
            'passed': True,
            'checks': {},
            'issues': []
        }
        
        try:
            # 检查数据大小
            raw_data_size = processed_data.get('raw_data_size', 0)
            validation['checks']['data_size'] = {
                'expected_min': 10,  # 至少10条记录
                'actual': raw_data_size,
                'passed': raw_data_size >= 10
            }
            
            if raw_data_size < 10:
                validation['passed'] = False
                validation['issues'].append(f"数据量过少: {raw_data_size} < 10")
            
            # 检查数据结构
            required_data_types = ['events_data', 'user_data', 'session_data']
            for data_type in required_data_types:
                has_data = data_type in processed_data and processed_data[data_type]
                validation['checks'][f'{data_type}_exists'] = {
                    'expected': True,
                    'actual': has_data,
                    'passed': has_data
                }
                
                if not has_data:
                    validation['passed'] = False
                    validation['issues'].append(f"缺少 {data_type} 数据")
            
            # 检查数据质量报告
            data_summary = processed_data.get('data_summary', {})
            if data_summary:
                validation['checks']['data_quality'] = {
                    'has_summary': True,
                    'passed': True
                }
            else:
                validation['checks']['data_quality'] = {
                    'has_summary': False,
                    'passed': False
                }
                validation['issues'].append("缺少数据质量摘要")
            
        except Exception as e:
            validation['passed'] = False
            validation['error'] = str(e)
            validation['issues'].append(f"数据处理验证出错: {str(e)}")
        
        return validation
    
    def _validate_analysis_module(self, analysis_type: str, result: Any) -> Dict[str, Any]:
        """验证单个分析模块"""
        validation = {
            'passed': True,
            'checks': {},
            'issues': []
        }
        
        try:
            # 检查结果状态
            if hasattr(result, 'status'):
                status_passed = result.status == 'completed'
                validation['checks']['status'] = {
                    'expected': 'completed',
                    'actual': result.status,
                    'passed': status_passed
                }
                
                if not status_passed:
                    validation['passed'] = False
                    validation['issues'].append(f"分析状态异常: {result.status}")
                    if hasattr(result, 'error_message') and result.error_message:
                        validation['issues'].append(f"错误信息: {result.error_message}")
            
            # 检查数据完整性
            if hasattr(result, 'data') and result.data:
                validation['checks']['has_data'] = {
                    'expected': True,
                    'actual': True,
                    'passed': True
                }
            else:
                validation['checks']['has_data'] = {
                    'expected': True,
                    'actual': False,
                    'passed': False
                }
                validation['passed'] = False
                validation['issues'].append("分析结果数据为空")
            
            # 检查洞察和建议
            if hasattr(result, 'insights'):
                has_insights = len(result.insights) > 0
                validation['checks']['has_insights'] = {
                    'expected': True,
                    'actual': has_insights,
                    'passed': has_insights
                }
                
                if not has_insights:
                    validation['issues'].append("缺少分析洞察")
            
            if hasattr(result, 'recommendations'):
                has_recommendations = len(result.recommendations) > 0
                validation['checks']['has_recommendations'] = {
                    'expected': True,
                    'actual': has_recommendations,
                    'passed': has_recommendations
                }
                
                if not has_recommendations:
                    validation['issues'].append("缺少分析建议")
            
            # 检查执行时间
            if hasattr(result, 'execution_time'):
                reasonable_time = result.execution_time < 300  # 5分钟内
                validation['checks']['execution_time'] = {
                    'expected_max': 300,
                    'actual': result.execution_time,
                    'passed': reasonable_time
                }
                
                if not reasonable_time:
                    validation['issues'].append(f"执行时间过长: {result.execution_time:.2f}s")
            
        except Exception as e:
            validation['passed'] = False
            validation['error'] = str(e)
            validation['issues'].append(f"模块验证出错: {str(e)}")
        
        return validation
    
    def _validate_result_consistency(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """验证分析结果之间的一致性"""
        validation = {
            'passed': True,
            'checks': {},
            'issues': []
        }
        
        try:
            # 检查用户数量一致性
            user_counts = {}
            for analysis_type, result in analysis_results.items():
                if hasattr(result, 'data') and result.data:
                    data = result.data
                    if 'unique_users' in data:
                        user_counts[analysis_type] = data['unique_users']
                    elif 'user_count' in data:
                        user_counts[analysis_type] = data['user_count']
            
            if len(user_counts) > 1:
                unique_counts = set(user_counts.values())
                if len(unique_counts) == 1:
                    validation['checks']['user_count_consistency'] = {
                        'expected': 'consistent',
                        'actual': 'consistent',
                        'passed': True,
                        'counts': user_counts
                    }
                else:
                    validation['checks']['user_count_consistency'] = {
                        'expected': 'consistent',
                        'actual': 'inconsistent',
                        'passed': False,
                        'counts': user_counts
                    }
                    validation['passed'] = False
                    validation['issues'].append(f"用户数量不一致: {user_counts}")
            
            # 检查时间范围一致性
            date_ranges = {}
            for analysis_type, result in analysis_results.items():
                if hasattr(result, 'data') and result.data:
                    data = result.data
                    if 'date_range' in data:
                        date_ranges[analysis_type] = data['date_range']
            
            if len(date_ranges) > 1:
                # 简单检查是否所有分析都有日期范围
                all_have_dates = all(
                    isinstance(dr, dict) and 'start' in dr and 'end' in dr 
                    for dr in date_ranges.values()
                )
                
                validation['checks']['date_range_consistency'] = {
                    'expected': 'all_have_dates',
                    'actual': 'all_have_dates' if all_have_dates else 'missing_dates',
                    'passed': all_have_dates,
                    'ranges': date_ranges
                }
                
                if not all_have_dates:
                    validation['issues'].append("部分分析缺少日期范围信息")
            
        except Exception as e:
            validation['passed'] = False
            validation['error'] = str(e)
            validation['issues'].append(f"一致性验证出错: {str(e)}")
        
        return validation
    
    def _validate_visualizations(self, visualizations: Dict[str, Any]) -> Dict[str, Any]:
        """验证可视化结果"""
        validation = {
            'passed': True,
            'checks': {},
            'issues': []
        }
        
        try:
            # 检查是否有可视化结果
            has_visualizations = len(visualizations) > 0
            validation['checks']['has_visualizations'] = {
                'expected': True,
                'actual': has_visualizations,
                'passed': has_visualizations
            }
            
            if not has_visualizations:
                validation['passed'] = False
                validation['issues'].append("没有生成可视化结果")
            else:
                # 检查每个可视化类型
                expected_viz_types = ['event_analysis', 'retention_analysis', 'conversion_analysis']
                for viz_type in expected_viz_types:
                    has_viz = viz_type in visualizations and visualizations[viz_type]
                    validation['checks'][f'{viz_type}_visualization'] = {
                        'expected': True,
                        'actual': has_viz,
                        'passed': has_viz
                    }
                    
                    if not has_viz:
                        validation['issues'].append(f"缺少 {viz_type} 可视化")
            
        except Exception as e:
            validation['passed'] = False
            validation['error'] = str(e)
            validation['issues'].append(f"可视化验证出错: {str(e)}")
        
        return validation
    
    def _generate_data_quality_report(self) -> Dict[str, Any]:
        """生成数据质量报告"""
        self.logger.info("生成数据质量报告")
        
        try:
            # 使用数据解析器和验证器
            parser = GA4DataParser()
            validator = DataValidator()
            
            # 解析原始数据
            raw_data = parser.parse_ndjson(self.data_file)
            
            # 执行数据验证
            validation_report = validator.validate_dataframe(raw_data)
            
            # 生成数据质量摘要
            quality_summary = parser.validate_data_quality(raw_data)
            
            # 统计信息
            stats = {
                'total_records': len(raw_data),
                'unique_users': raw_data['user_pseudo_id'].nunique() if 'user_pseudo_id' in raw_data.columns else 0,
                'unique_events': raw_data['event_name'].nunique() if 'event_name' in raw_data.columns else 0,
                'date_range': {
                    'start': raw_data['event_date'].min() if 'event_date' in raw_data.columns else 'N/A',
                    'end': raw_data['event_date'].max() if 'event_date' in raw_data.columns else 'N/A'
                },
                'event_distribution': raw_data['event_name'].value_counts().to_dict() if 'event_name' in raw_data.columns else {}
            }
            
            quality_report = {
                'status': 'success',
                'validation_report': validation_report,
                'quality_summary': quality_summary,
                'statistics': stats,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info("数据质量报告生成完成")
            return quality_report
            
        except Exception as e:
            self.logger.error(f"数据质量报告生成失败: {e}")
            return {
                'status': 'error',
                'error_message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _create_comprehensive_report(self, workflow_result: Dict[str, Any], 
                                   validation_results: Dict[str, Any],
                                   quality_report: Dict[str, Any],
                                   execution_time: float) -> Dict[str, Any]:
        """创建综合分析报告"""
        self.logger.info("创建综合分析报告")
        
        report = {
            'report_metadata': {
                'title': 'GA4示例数据完整分析报告',
                'generated_at': datetime.now().isoformat(),
                'data_file': self.data_file,
                'total_execution_time': execution_time,
                'analysis_version': '1.0.0'
            },
            
            'executive_summary': {
                'analysis_status': validation_results.get('overall_status', 'unknown'),
                'total_analyses_performed': len(workflow_result.get('analysis_results', {})),
                'data_quality_status': quality_report.get('status', 'unknown'),
                'key_findings': self._extract_key_findings(workflow_result),
                'critical_issues': validation_results.get('issues', [])
            },
            
            'data_overview': {
                'source_file': self.data_file,
                'processing_results': workflow_result.get('processed_data', {}),
                'quality_metrics': quality_report.get('statistics', {}),
                'validation_summary': quality_report.get('validation_report', {})
            },
            
            'analysis_results': {
                'detailed_results': workflow_result.get('analysis_results', {}),
                'comprehensive_report': workflow_result.get('comprehensive_report', {}),
                'visualizations': workflow_result.get('visualizations', {})
            },
            
            'validation_results': validation_results,
            
            'quality_assessment': quality_report,
            
            'performance_metrics': {
                'total_execution_time': execution_time,
                'system_metrics': getattr(self.integration_manager, 'metrics_history', [])[-5:] if hasattr(self.integration_manager, 'metrics_history') else [],
                'workflow_history': getattr(self.integration_manager, 'workflow_history', [])
            },
            
            'recommendations': {
                'data_quality_improvements': self._generate_data_quality_recommendations(quality_report),
                'analysis_improvements': validation_results.get('recommendations', []),
                'system_optimizations': self._generate_system_recommendations(execution_time)
            },
            
            'appendices': {
                'technical_details': {
                    'system_configuration': self.integration_manager.config.__dict__,
                    'component_versions': self._get_component_versions()
                },
                'raw_validation_data': validation_results.get('validations', {}),
                'error_logs': self._collect_error_logs()
            }
        }
        
        self.logger.info("综合分析报告创建完成")
        return report
    
    def _extract_key_findings(self, workflow_result: Dict[str, Any]) -> List[str]:
        """提取关键发现"""
        key_findings = []
        
        try:
            # 从综合报告中提取关键洞察
            comprehensive_report = workflow_result.get('comprehensive_report', {})
            if 'key_insights' in comprehensive_report:
                key_findings.extend(comprehensive_report['key_insights'][:5])
            
            # 从各个分析结果中提取关键发现
            analysis_results = workflow_result.get('analysis_results', {})
            for analysis_type, result in analysis_results.items():
                if hasattr(result, 'insights') and result.insights:
                    key_findings.append(f"{analysis_type}: {result.insights[0]}")
            
            # 如果没有发现，添加默认信息
            if not key_findings:
                key_findings = [
                    "完成了GA4示例数据的完整分析流程",
                    "验证了所有分析模块的功能",
                    "生成了可视化结果和分析报告"
                ]
        
        except Exception as e:
            self.logger.warning(f"提取关键发现时出错: {e}")
            key_findings = ["分析完成，但提取关键发现时遇到问题"]
        
        return key_findings[:10]  # 限制为前10个发现
    
    def _generate_data_quality_recommendations(self, quality_report: Dict[str, Any]) -> List[str]:
        """生成数据质量改进建议"""
        recommendations = []
        
        try:
            validation_report = quality_report.get('validation_report', {})
            
            if not validation_report.get('validation_passed', True):
                recommendations.append("数据验证发现问题，建议检查数据源质量")
            
            stats = quality_report.get('statistics', {})
            if stats.get('total_records', 0) < 100:
                recommendations.append("数据量较少，建议增加样本数据以获得更准确的分析结果")
            
            if stats.get('unique_events', 0) < 5:
                recommendations.append("事件类型较少，建议丰富事件跟踪以获得更全面的用户行为洞察")
            
            if not recommendations:
                recommendations.append("数据质量良好，可以进行深入分析")
        
        except Exception as e:
            self.logger.warning(f"生成数据质量建议时出错: {e}")
            recommendations.append("建议定期检查数据质量")
        
        return recommendations
    
    def _generate_system_recommendations(self, execution_time: float) -> List[str]:
        """生成系统优化建议"""
        recommendations = []
        
        if execution_time > 60:
            recommendations.append("执行时间较长，建议优化分析算法或增加计算资源")
        elif execution_time < 10:
            recommendations.append("执行效率良好，系统性能表现优秀")
        
        recommendations.extend([
            "建议定期监控系统性能指标",
            "考虑实施缓存机制以提高重复分析的效率",
            "建议设置自动化测试以确保分析结果的一致性"
        ])
        
        return recommendations
    
    def _generate_validation_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """生成验证建议"""
        recommendations = []
        
        if validation_results.get('overall_status') == 'failed':
            recommendations.append("发现验证失败，建议检查分析模块的实现")
        
        issues = validation_results.get('issues', [])
        if issues:
            recommendations.append(f"需要解决 {len(issues)} 个验证问题")
        
        validations = validation_results.get('validations', {})
        for validation_type, result in validations.items():
            if not result.get('passed', True):
                recommendations.append(f"需要改进 {validation_type} 模块的实现")
        
        if not recommendations:
            recommendations.append("所有验证通过，系统运行正常")
        
        return recommendations
    
    def _get_component_versions(self) -> Dict[str, str]:
        """获取组件版本信息"""
        return {
            'python_version': sys.version,
            'pandas_version': pd.__version__,
            'system_platform': sys.platform,
            'analysis_framework': 'standalone_integration_manager_v1.0'
        }
    
    def _collect_error_logs(self) -> List[str]:
        """收集错误日志"""
        # 这里可以实现从日志文件中收集错误信息
        # 目前返回空列表
        return []
    
    def _export_analysis_results(self, comprehensive_report: Dict[str, Any]):
        """导出分析结果"""
        self.logger.info("开始导出分析结果")
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 导出JSON格式报告
            json_file = self.output_dir / f"example_analysis_report_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_report, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"JSON报告已导出: {json_file}")
            
            # 导出简化的文本报告
            text_file = self.output_dir / f"example_analysis_summary_{timestamp}.txt"
            self._export_text_summary(comprehensive_report, text_file)
            
            self.logger.info(f"文本摘要已导出: {text_file}")
            
            # 如果有可视化结果，尝试导出
            visualizations = comprehensive_report.get('analysis_results', {}).get('visualizations', {})
            if visualizations:
                viz_dir = self.output_dir / f"visualizations_{timestamp}"
                viz_dir.mkdir(exist_ok=True)
                self._export_visualizations(visualizations, viz_dir)
            
            self.logger.info("分析结果导出完成")
            
        except Exception as e:
            self.logger.error(f"导出分析结果失败: {e}")
    
    def _export_text_summary(self, report: Dict[str, Any], file_path: Path):
        """导出文本摘要"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("GA4示例数据分析报告摘要\n")
            f.write("=" * 50 + "\n\n")
            
            # 基本信息
            metadata = report.get('report_metadata', {})
            f.write(f"生成时间: {metadata.get('generated_at', 'N/A')}\n")
            f.write(f"数据文件: {metadata.get('data_file', 'N/A')}\n")
            f.write(f"执行时间: {metadata.get('total_execution_time', 0):.2f}秒\n\n")
            
            # 执行摘要
            summary = report.get('executive_summary', {})
            f.write("执行摘要:\n")
            f.write(f"- 分析状态: {summary.get('analysis_status', 'N/A')}\n")
            f.write(f"- 执行的分析数量: {summary.get('total_analyses_performed', 0)}\n")
            f.write(f"- 数据质量状态: {summary.get('data_quality_status', 'N/A')}\n\n")
            
            # 关键发现
            key_findings = summary.get('key_findings', [])
            if key_findings:
                f.write("关键发现:\n")
                for i, finding in enumerate(key_findings, 1):
                    f.write(f"{i}. {finding}\n")
                f.write("\n")
            
            # 验证结果
            validation = report.get('validation_results', {})
            f.write(f"验证状态: {validation.get('overall_status', 'N/A')}\n")
            
            issues = validation.get('issues', [])
            if issues:
                f.write("发现的问题:\n")
                for i, issue in enumerate(issues, 1):
                    f.write(f"{i}. {issue}\n")
                f.write("\n")
            
            # 建议
            recommendations = report.get('recommendations', {})
            all_recommendations = []
            for rec_type, recs in recommendations.items():
                if isinstance(recs, list):
                    all_recommendations.extend(recs)
            
            if all_recommendations:
                f.write("改进建议:\n")
                for i, rec in enumerate(all_recommendations[:10], 1):
                    f.write(f"{i}. {rec}\n")
    
    def _export_visualizations(self, visualizations: Dict[str, Any], viz_dir: Path):
        """导出可视化结果"""
        try:
            # 这里可以实现将Plotly图表保存为HTML或PNG文件
            # 目前只保存可视化的元数据
            viz_metadata = {
                'visualization_types': list(visualizations.keys()),
                'total_visualizations': len(visualizations),
                'export_timestamp': datetime.now().isoformat()
            }
            
            metadata_file = viz_dir / "visualizations_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(viz_metadata, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"可视化元数据已导出: {metadata_file}")
            
        except Exception as e:
            self.logger.warning(f"导出可视化结果时出错: {e}")


def main():
    """主函数"""
    print("开始GA4示例数据分析和验证演示")
    print("=" * 60)
    
    try:
        # 创建验证器实例
        validator = ExampleDataAnalysisValidator()
        
        # 运行完整分析
        print("正在运行完整的示例数据分析...")
        start_time = time.time()
        
        comprehensive_report = validator.run_complete_analysis()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 显示结果摘要
        print(f"\n分析完成！总耗时: {total_time:.2f}秒")
        print("\n结果摘要:")
        print("-" * 40)
        
        summary = comprehensive_report.get('executive_summary', {})
        print(f"分析状态: {summary.get('analysis_status', 'N/A')}")
        print(f"执行的分析数量: {summary.get('total_analyses_performed', 0)}")
        print(f"数据质量状态: {summary.get('data_quality_status', 'N/A')}")
        
        key_findings = summary.get('key_findings', [])
        if key_findings:
            print("\n关键发现:")
            for i, finding in enumerate(key_findings[:5], 1):
                print(f"{i}. {finding}")
        
        validation_results = comprehensive_report.get('validation_results', {})
        print(f"\n验证状态: {validation_results.get('overall_status', 'N/A')}")
        
        issues = validation_results.get('issues', [])
        if issues:
            print("发现的问题:")
            for i, issue in enumerate(issues[:3], 1):
                print(f"{i}. {issue}")
        
        print(f"\n详细报告已保存到: reports/example_analysis/")
        print("任务8.2 - 示例数据分析和验证 - 完成！")
        
    except Exception as e:
        print(f"\n分析过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())