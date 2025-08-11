"""
报告导出器测试
测试PDF、Excel、JSON格式的报告导出功能
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.report_exporter import ReportExporter
from datetime import datetime


class TestReportExporter(unittest.TestCase):
    """报告导出器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.exporter = ReportExporter()
        self.test_report_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'analysis_scope': {
                    'date_range': '2024-01-01 to 2024-01-31',
                    'event_types': ['page_view', 'click', 'purchase']
                },
                'data_summary': {
                    'total_events': 10000,
                    'unique_users': 1500,
                    'total_sessions': 3000
                }
            },
            'executive_summary': {
                'key_metrics': {
                    'total_events': 10000,
                    'unique_users': 1500,
                    'conversion_rate': 0.05,
                    'day1_retention': 0.3
                },
                'key_trends': [
                    '移动端用户占比增长',
                    '周末活跃度下降'
                ],
                'key_issues': [
                    '转化率偏低',
                    '新用户留存需改善'
                ]
            },
            'detailed_analysis': {
                'event_analysis': {
                    'summary': {
                        'top_events': ['page_view', 'click', 'scroll'],
                        'trending_events': ['purchase', 'signup'],
                        'event_count': 5
                    },
                    'frequency_analysis': {
                        'page_view': 5000,
                        'click': 3000,
                        'purchase': 500
                    }
                },
                'retention_analysis': {
                    'summary': {
                        'day1_retention': 0.3,
                        'day7_retention': 0.15,
                        'day30_retention': 0.08
                    }
                },
                'conversion_analysis': {
                    'summary': {
                        'overall_conversion_rate': 0.05,
                        'bottleneck_step': 'checkout',
                        'top_conversion_paths': ['home->product->purchase']
                    }
                }
            }
        }
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        # 清理临时文件
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_json_export(self):
        """测试JSON格式导出"""
        print("\n测试JSON格式导出...")
        
        output_path = os.path.join(self.temp_dir, 'test_report.json')
        result = self.exporter.export_report(self.test_report_data, 'json', output_path)
        
        # 验证导出结果
        self.assertEqual(result['status'], 'success')
        self.assertIn('file_path', result)
        self.assertIn('file_size', result)
        
        # 验证文件存在
        self.assertTrue(os.path.exists(output_path))
        
        # 验证文件内容
        with open(output_path, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        self.assertIn('export_metadata', exported_data)
        self.assertIn('report_data', exported_data)
        self.assertEqual(exported_data['export_metadata']['format'], 'json')
        
        print(f"✓ JSON导出成功: {output_path}")
        print(f"  文件大小: {result['file_size']} bytes")
    
    def test_pdf_export(self):
        """测试PDF格式导出"""
        print("\n测试PDF格式导出...")
        
        if 'pdf' not in self.exporter.get_supported_formats():
            print("⚠️ PDF导出不可用，跳过测试")
            return
        
        output_path = os.path.join(self.temp_dir, 'test_report.pdf')
        result = self.exporter.export_report(self.test_report_data, 'pdf', output_path)
        
        # 验证导出结果
        self.assertEqual(result['status'], 'success')
        self.assertIn('file_path', result)
        self.assertIn('file_size', result)
        
        # 验证文件存在
        self.assertTrue(os.path.exists(output_path))
        
        # 验证文件大小合理
        self.assertGreater(result['file_size'], 1000)  # PDF文件应该大于1KB
        
        print(f"✓ PDF导出成功: {output_path}")
        print(f"  文件大小: {result['file_size']} bytes")
    
    def test_excel_export(self):
        """测试Excel格式导出"""
        print("\n测试Excel格式导出...")
        
        if 'excel' not in self.exporter.get_supported_formats():
            print("⚠️ Excel导出不可用，跳过测试")
            return
        
        output_path = os.path.join(self.temp_dir, 'test_report.xlsx')
        result = self.exporter.export_report(self.test_report_data, 'excel', output_path)
        
        # 验证导出结果
        self.assertEqual(result['status'], 'success')
        self.assertIn('file_path', result)
        self.assertIn('file_size', result)
        
        # 验证文件存在
        self.assertTrue(os.path.exists(output_path))
        
        # 验证文件大小合理
        self.assertGreater(result['file_size'], 5000)  # Excel文件应该大于5KB
        
        print(f"✓ Excel导出成功: {output_path}")
        print(f"  文件大小: {result['file_size']} bytes")
    
    def test_unsupported_format(self):
        """测试不支持的格式"""
        print("\n测试不支持的格式...")
        
        output_path = os.path.join(self.temp_dir, 'test_report.xml')
        result = self.exporter.export_report(self.test_report_data, 'xml', output_path)
        
        # 验证返回错误
        self.assertEqual(result['status'], 'error')
        self.assertIn('不支持的导出格式', result['message'])
        
        print(f"✓ 不支持格式处理正确: {result['message']}")
    
    def test_invalid_data(self):
        """测试无效数据"""
        print("\n测试无效数据...")
        
        invalid_data = {'invalid': 'data'}
        output_path = os.path.join(self.temp_dir, 'test_invalid.json')
        
        # 验证数据格式
        validation_result = self.exporter.validate_report_data(invalid_data)
        self.assertFalse(validation_result['valid'])
        
        print(f"✓ 数据验证正确识别无效数据: {validation_result['message']}")
    
    def test_default_filename(self):
        """测试默认文件名生成"""
        print("\n测试默认文件名生成...")
        
        # 不指定输出路径
        result = self.exporter.export_report(self.test_report_data, 'json')
        
        if result['status'] == 'success':
            # 验证文件路径格式
            file_path = result['file_path']
            self.assertTrue(file_path.startswith('reports/'))
            self.assertTrue(file_path.endswith('.json'))
            self.assertIn('analysis_report_', file_path)
            
            print(f"✓ 默认文件名生成成功: {file_path}")
            
            # 清理生成的文件
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_supported_formats(self):
        """测试支持的格式列表"""
        print("\n测试支持的格式列表...")
        
        formats = self.exporter.get_supported_formats()
        
        # JSON应该总是支持的
        self.assertIn('json', formats)
        
        print(f"✓ 支持的格式: {', '.join(formats)}")
    
    def test_large_data_export(self):
        """测试大数据量导出"""
        print("\n测试大数据量导出...")
        
        # 创建大量数据
        large_data = self.test_report_data.copy()
        large_data['detailed_analysis']['large_dataset'] = {
            f'item_{i}': f'value_{i}' for i in range(1000)
        }
        
        output_path = os.path.join(self.temp_dir, 'large_report.json')
        result = self.exporter.export_report(large_data, 'json', output_path)
        
        # 验证导出成功
        self.assertEqual(result['status'], 'success')
        self.assertTrue(os.path.exists(output_path))
        
        # 验证文件大小
        self.assertGreater(result['file_size'], 10000)  # 应该大于10KB
        
        print(f"✓ 大数据量导出成功: {result['file_size']} bytes")


def run_export_tests():
    """运行导出功能测试"""
    print("🧪 开始报告导出功能测试")
    print("=" * 60)
    
    # 创建测试套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestReportExporter)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(test_suite)
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果统计")
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n✅ 测试成功率: {success_rate:.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_export_tests()
    
    if success:
        print("\n🎉 所有导出功能测试通过!")
    else:
        print("\n⚠️ 部分测试失败，请检查实现")
        sys.exit(1)