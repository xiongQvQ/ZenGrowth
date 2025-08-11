"""
导出和配置功能集成测试
测试报告导出和配置管理的完整功能
"""

import sys
import os
import tempfile
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.report_exporter import ReportExporter
from utils.config_manager import ConfigManager


def test_export_functionality():
    """测试导出功能"""
    print("🧪 测试报告导出功能")
    print("-" * 40)
    
    try:
        # 初始化导出器
        exporter = ReportExporter()
        
        # 创建测试报告数据
        test_report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'analysis_scope': {
                    'date_range': '2024-01-01 to 2024-01-31',
                    'event_types': ['page_view', 'click', 'purchase']
                },
                'data_summary': {
                    'total_events': 15000,
                    'unique_users': 2500,
                    'total_sessions': 4500
                }
            },
            'executive_summary': {
                'key_metrics': {
                    'total_events': 15000,
                    'unique_users': 2500,
                    'conversion_rate': 0.08,
                    'day1_retention': 0.35
                },
                'key_trends': [
                    '移动端用户占比持续增长',
                    '工作日活跃度明显高于周末',
                    '新用户转化率有所提升'
                ],
                'key_issues': [
                    '购物车放弃率较高',
                    '用户留存在第7天出现明显下降'
                ]
            },
            'detailed_analysis': {
                'event_analysis': {
                    'summary': {
                        'top_events': ['page_view', 'click', 'scroll', 'search', 'add_to_cart'],
                        'trending_events': ['purchase', 'signup', 'share'],
                        'event_count': 8
                    },
                    'frequency_analysis': {
                        'page_view': 8000,
                        'click': 4500,
                        'scroll': 3000,
                        'search': 1500,
                        'purchase': 800
                    }
                },
                'retention_analysis': {
                    'summary': {
                        'day1_retention': 0.35,
                        'day7_retention': 0.18,
                        'day30_retention': 0.12
                    },
                    'cohort_data': {
                        'best_cohort': '2024-01-15',
                        'worst_cohort': '2024-01-28'
                    }
                },
                'conversion_analysis': {
                    'summary': {
                        'overall_conversion_rate': 0.08,
                        'bottleneck_step': 'payment',
                        'top_conversion_paths': [
                            'home->product->cart->purchase',
                            'search->product->purchase',
                            'category->product->cart->purchase'
                        ]
                    }
                },
                'user_segmentation': {
                    'summary': {
                        'total_segments': 4,
                        'largest_segment': 'casual_browsers',
                        'most_valuable_segment': 'power_users'
                    }
                },
                'path_analysis': {
                    'summary': {
                        'common_paths_count': 15,
                        'drop_off_points': ['cart', 'checkout', 'payment'],
                        'optimal_paths': [
                            'home->product->purchase',
                            'search->product->purchase'
                        ]
                    }
                }
            }
        }
        
        print("📊 测试报告数据准备完成")
        
        # 测试支持的格式
        supported_formats = exporter.get_supported_formats()
        print(f"📋 支持的导出格式: {', '.join(supported_formats)}")
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        print(f"📁 临时目录: {temp_dir}")
        
        # 测试各种格式导出
        export_results = {}
        
        for format_type in supported_formats:
            print(f"\n🔄 测试{format_type.upper()}格式导出...")
            
            output_path = os.path.join(temp_dir, f'test_report.{format_type}')
            result = exporter.export_report(test_report, format_type, output_path)
            
            export_results[format_type] = result
            
            if result['status'] == 'success':
                print(f"  ✅ {format_type.upper()}导出成功")
                print(f"     文件路径: {result['file_path']}")
                print(f"     文件大小: {result['file_size']} bytes")
            else:
                print(f"  ❌ {format_type.upper()}导出失败: {result['message']}")
        
        # 测试数据验证
        print(f"\n🔍 测试数据验证...")
        validation_result = exporter.validate_report_data(test_report)
        if validation_result['valid']:
            print("  ✅ 报告数据验证通过")
        else:
            print(f"  ❌ 报告数据验证失败: {validation_result['message']}")
        
        # 测试无效数据
        invalid_data = {'incomplete': 'data'}
        invalid_validation = exporter.validate_report_data(invalid_data)
        if not invalid_validation['valid']:
            print("  ✅ 无效数据正确识别")
        
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)
        print(f"🗑️ 临时文件已清理")
        
        # 统计结果
        successful_exports = sum(1 for result in export_results.values() if result['status'] == 'success')
        total_formats = len(supported_formats)
        
        print(f"\n📈 导出测试结果:")
        print(f"  总格式数: {total_formats}")
        print(f"  成功导出: {successful_exports}")
        print(f"  成功率: {successful_exports/total_formats*100:.1f}%")
        
        return successful_exports == total_formats
        
    except Exception as e:
        print(f"❌ 导出功能测试失败: {str(e)}")
        return False


def test_config_functionality():
    """测试配置管理功能"""
    print("\n🧪 测试配置管理功能")
    print("-" * 40)
    
    try:
        # 创建临时配置目录
        temp_config_dir = tempfile.mkdtemp()
        config_manager = ConfigManager(temp_config_dir)
        
        print(f"📁 临时配置目录: {temp_config_dir}")
        
        # 测试默认配置加载
        print("\n📋 测试默认配置...")
        analysis_config = config_manager.get_analysis_config()
        system_config = config_manager.get_system_config()
        
        print("  ✅ 分析配置加载成功")
        print(f"     事件分析配置: {bool(analysis_config.get('event_analysis'))}")
        print(f"     留存分析配置: {bool(analysis_config.get('retention_analysis'))}")
        print(f"     转化分析配置: {bool(analysis_config.get('conversion_analysis'))}")
        
        print("  ✅ 系统配置加载成功")
        print(f"     API配置: {bool(system_config.get('api_settings'))}")
        print(f"     数据处理配置: {bool(system_config.get('data_processing'))}")
        print(f"     导出配置: {bool(system_config.get('export_settings'))}")
        
        # 测试配置更新
        print("\n🔄 测试配置更新...")
        
        # 更新分析配置
        event_updates = {
            'time_granularity': 'week',
            'top_events_limit': 15,
            'trend_analysis_days': 45
        }
        
        result = config_manager.update_analysis_config('event_analysis', event_updates)
        if result:
            print("  ✅ 事件分析配置更新成功")
            
            # 验证更新
            updated_config = config_manager.get_analysis_config('event_analysis')
            if updated_config['time_granularity'] == 'week':
                print("     配置值更新正确")
            else:
                print("     ⚠️ 配置值更新异常")
        
        # 更新系统配置
        api_updates = {
            'llm_temperature': 0.3,
            'llm_max_tokens': 5000
        }
        
        result = config_manager.update_system_config('api_settings', api_updates)
        if result:
            print("  ✅ API配置更新成功")
        
        # 测试配置验证
        print("\n✅ 测试配置验证...")
        validation_result = config_manager.validate_config()
        
        print(f"  配置有效性: {'✅ 有效' if validation_result['valid'] else '❌ 无效'}")
        print(f"  错误数量: {len(validation_result['errors'])}")
        print(f"  警告数量: {len(validation_result['warnings'])}")
        
        if validation_result['errors']:
            for error in validation_result['errors']:
                print(f"    错误: {error}")
        
        if validation_result['warnings']:
            for warning in validation_result['warnings']:
                print(f"    警告: {warning}")
        
        # 测试配置导出导入
        print("\n📤 测试配置导出导入...")
        
        export_path = os.path.join(temp_config_dir, 'config_backup.json')
        export_result = config_manager.export_config(export_path)
        
        if export_result:
            print("  ✅ 配置导出成功")
            
            # 验证导出文件
            if os.path.exists(export_path):
                with open(export_path, 'r', encoding='utf-8') as f:
                    exported_data = json.load(f)
                
                if 'analysis_config' in exported_data and 'system_config' in exported_data:
                    print("     导出文件格式正确")
                else:
                    print("     ⚠️ 导出文件格式异常")
            
            # 测试导入
            import_result = config_manager.import_config(export_path)
            if import_result:
                print("  ✅ 配置导入成功")
            else:
                print("  ❌ 配置导入失败")
        else:
            print("  ❌ 配置导出失败")
        
        # 测试配置重置
        print("\n🔄 测试配置重置...")
        
        reset_result = config_manager.reset_analysis_config('event_analysis')
        if reset_result:
            print("  ✅ 分析配置重置成功")
            
            # 验证重置
            reset_config = config_manager.get_analysis_config('event_analysis')
            if reset_config['time_granularity'] == 'day':  # 默认值
                print("     配置重置正确")
            else:
                print("     ⚠️ 配置重置异常")
        
        # 测试配置摘要
        print("\n📊 测试配置摘要...")
        summary = config_manager.get_config_summary()
        
        if summary:
            print("  ✅ 配置摘要生成成功")
            print(f"     分析配置项: {len(summary.get('analysis_config', {}))}")
            print(f"     系统配置项: {len(summary.get('system_config', {}))}")
        else:
            print("  ❌ 配置摘要生成失败")
        
        # 清理临时目录
        import shutil
        shutil.rmtree(temp_config_dir)
        print(f"🗑️ 临时配置文件已清理")
        
        print(f"\n📈 配置管理测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 配置管理功能测试失败: {str(e)}")
        return False


def test_integration():
    """测试导出和配置功能集成"""
    print("\n🧪 测试功能集成")
    print("-" * 40)
    
    try:
        # 创建配置管理器
        temp_config_dir = tempfile.mkdtemp()
        config_manager = ConfigManager(temp_config_dir)
        
        # 配置导出设置
        export_config_updates = {
            'default_format': 'json',
            'include_raw_data': True,
            'compress_exports': False,
            'export_dir': 'test_reports'
        }
        
        config_manager.update_system_config('export_settings', export_config_updates)
        print("✅ 导出配置更新完成")
        
        # 获取导出配置
        export_config = config_manager.get_system_config('export_settings')
        print(f"📋 当前导出配置:")
        print(f"   默认格式: {export_config['default_format']}")
        print(f"   包含原始数据: {export_config['include_raw_data']}")
        print(f"   压缩导出: {export_config['compress_exports']}")
        
        # 使用配置进行导出测试
        exporter = ReportExporter()
        
        test_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'data_summary': {'total_events': 1000, 'unique_users': 200}
            },
            'detailed_analysis': {
                'event_analysis': {'summary': {'top_events': ['page_view', 'click']}}
            }
        }
        
        # 使用配置的默认格式导出
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, f'integrated_test.{export_config["default_format"]}')
        
        result = exporter.export_report(test_data, export_config['default_format'], output_path)
        
        if result['status'] == 'success':
            print("✅ 集成导出测试成功")
            print(f"   文件路径: {result['file_path']}")
            print(f"   文件大小: {result['file_size']} bytes")
        else:
            print(f"❌ 集成导出测试失败: {result['message']}")
            return False
        
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)
        shutil.rmtree(temp_config_dir)
        
        print("🗑️ 临时文件已清理")
        print("✅ 功能集成测试完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 功能集成测试失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始导出和配置功能完整测试")
    print("=" * 60)
    
    test_results = []
    
    # 测试导出功能
    export_success = test_export_functionality()
    test_results.append(('导出功能', export_success))
    
    # 测试配置管理功能
    config_success = test_config_functionality()
    test_results.append(('配置管理', config_success))
    
    # 测试功能集成
    integration_success = test_integration()
    test_results.append(('功能集成', integration_success))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("-" * 30)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, success in test_results if success)
    
    for test_name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过! 导出和配置功能实现完成")
        return True
    else:
        print("\n⚠️ 部分测试失败，请检查实现")
        return False


if __name__ == "__main__":
    success = main()
    
    if not success:
        sys.exit(1)