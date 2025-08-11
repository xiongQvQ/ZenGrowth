"""
配置管理器测试
测试分析参数配置和系统设置管理功能
"""

import unittest
import tempfile
import json
import os
from pathlib import Path
import sys
import shutil

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config_manager import ConfigManager, AnalysisConfig, SystemConfig


class TestConfigManager(unittest.TestCase):
    """配置管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时配置目录
        self.temp_config_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_config_dir)
    
    def tearDown(self):
        """测试后清理"""
        # 清理临时目录
        if os.path.exists(self.temp_config_dir):
            shutil.rmtree(self.temp_config_dir)
    
    def test_default_config_creation(self):
        """测试默认配置创建"""
        print("\n测试默认配置创建...")
        
        # 验证分析配置
        analysis_config = self.config_manager.get_analysis_config()
        self.assertIn('event_analysis', analysis_config)
        self.assertIn('retention_analysis', analysis_config)
        self.assertIn('conversion_analysis', analysis_config)
        self.assertIn('user_segmentation', analysis_config)
        self.assertIn('path_analysis', analysis_config)
        self.assertIn('general', analysis_config)
        
        # 验证系统配置
        system_config = self.config_manager.get_system_config()
        self.assertIn('api_settings', system_config)
        self.assertIn('data_processing', system_config)
        self.assertIn('ui_settings', system_config)
        self.assertIn('export_settings', system_config)
        
        print("✓ 默认配置创建成功")
    
    def test_analysis_config_update(self):
        """测试分析配置更新"""
        print("\n测试分析配置更新...")
        
        # 更新事件分析配置
        update_data = {
            'time_granularity': 'week',
            'top_events_limit': 20,
            'trend_analysis_days': 60
        }
        
        result = self.config_manager.update_analysis_config('event_analysis', update_data)
        self.assertTrue(result)
        
        # 验证更新结果
        event_config = self.config_manager.get_analysis_config('event_analysis')
        self.assertEqual(event_config['time_granularity'], 'week')
        self.assertEqual(event_config['top_events_limit'], 20)
        self.assertEqual(event_config['trend_analysis_days'], 60)
        
        print("✓ 分析配置更新成功")
    
    def test_system_config_update(self):
        """测试系统配置更新"""
        print("\n测试系统配置更新...")
        
        # 更新API配置
        update_data = {
            'llm_model': 'gemini-1.5-pro',
            'llm_temperature': 0.2,
            'llm_max_tokens': 6000
        }
        
        result = self.config_manager.update_system_config('api_settings', update_data)
        self.assertTrue(result)
        
        # 验证更新结果
        api_config = self.config_manager.get_system_config('api_settings')
        self.assertEqual(api_config['llm_model'], 'gemini-1.5-pro')
        self.assertEqual(api_config['llm_temperature'], 0.2)
        self.assertEqual(api_config['llm_max_tokens'], 6000)
        
        print("✓ 系统配置更新成功")
    
    def test_config_persistence(self):
        """测试配置持久化"""
        print("\n测试配置持久化...")
        
        # 更新配置
        self.config_manager.update_analysis_config('retention_analysis', {
            'retention_periods': [1, 3, 7, 14, 30],
            'cohort_type': 'daily'
        })
        
        # 创建新的配置管理器实例
        new_manager = ConfigManager(self.temp_config_dir)
        
        # 验证配置被正确加载
        retention_config = new_manager.get_analysis_config('retention_analysis')
        self.assertEqual(retention_config['retention_periods'], [1, 3, 7, 14, 30])
        self.assertEqual(retention_config['cohort_type'], 'daily')
        
        print("✓ 配置持久化成功")
    
    def test_config_reset(self):
        """测试配置重置"""
        print("\n测试配置重置...")
        
        # 修改配置
        self.config_manager.update_analysis_config('user_segmentation', {
            'n_clusters': 8,
            'clustering_method': 'dbscan'
        })
        
        # 重置配置
        result = self.config_manager.reset_analysis_config('user_segmentation')
        self.assertTrue(result)
        
        # 验证重置结果
        seg_config = self.config_manager.get_analysis_config('user_segmentation')
        self.assertEqual(seg_config['n_clusters'], 5)  # 默认值
        self.assertEqual(seg_config['clustering_method'], 'kmeans')  # 默认值
        
        print("✓ 配置重置成功")
    
    def test_config_export_import(self):
        """测试配置导入导出"""
        print("\n测试配置导入导出...")
        
        # 修改一些配置
        self.config_manager.update_analysis_config('path_analysis', {
            'min_path_support': 0.02,
            'max_path_length': 15
        })
        
        self.config_manager.update_system_config('export_settings', {
            'default_format': 'pdf',
            'compress_exports': False
        })
        
        # 导出配置
        export_path = os.path.join(self.temp_config_dir, 'exported_config.json')
        result = self.config_manager.export_config(export_path)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(export_path))
        
        # 验证导出文件内容
        with open(export_path, 'r', encoding='utf-8') as f:
            exported_data = json.load(f)
        
        self.assertIn('analysis_config', exported_data)
        self.assertIn('system_config', exported_data)
        self.assertIn('exported_at', exported_data)
        
        # 重置配置
        self.config_manager.reset_analysis_config()
        self.config_manager.reset_system_config()
        
        # 导入配置
        result = self.config_manager.import_config(export_path)
        self.assertTrue(result)
        
        # 验证导入结果
        path_config = self.config_manager.get_analysis_config('path_analysis')
        self.assertEqual(path_config['min_path_support'], 0.02)
        self.assertEqual(path_config['max_path_length'], 15)
        
        export_config = self.config_manager.get_system_config('export_settings')
        self.assertEqual(export_config['default_format'], 'pdf')
        self.assertEqual(export_config['compress_exports'], False)
        
        print("✓ 配置导入导出成功")
    
    def test_config_validation(self):
        """测试配置验证"""
        print("\n测试配置验证...")
        
        # 测试有效配置
        validation_result = self.config_manager.validate_config()
        self.assertIn('valid', validation_result)
        self.assertIn('errors', validation_result)
        self.assertIn('warnings', validation_result)
        
        # 设置无效配置
        self.config_manager.update_system_config('data_processing', {
            'max_file_size_mb': -1  # 无效值
        })
        
        validation_result = self.config_manager.validate_config()
        # 应该有警告或错误
        self.assertTrue(len(validation_result['warnings']) > 0 or len(validation_result['errors']) > 0)
        
        print("✓ 配置验证功能正常")
    
    def test_config_summary(self):
        """测试配置摘要"""
        print("\n测试配置摘要...")
        
        summary = self.config_manager.get_config_summary()
        
        # 验证摘要结构
        self.assertIn('analysis_config', summary)
        self.assertIn('system_config', summary)
        self.assertIn('config_files', summary)
        
        # 验证分析配置摘要
        analysis_summary = summary['analysis_config']
        self.assertIn('event_analysis_enabled', analysis_summary)
        self.assertIn('retention_periods', analysis_summary)
        self.assertIn('clustering_method', analysis_summary)
        
        # 验证系统配置摘要
        system_summary = summary['system_config']
        self.assertIn('max_file_size_mb', system_summary)
        self.assertIn('default_export_format', system_summary)
        
        print("✓ 配置摘要生成成功")
    
    def test_invalid_config_type(self):
        """测试无效配置类型"""
        print("\n测试无效配置类型...")
        
        # 尝试更新不存在的分析配置类型
        result = self.config_manager.update_analysis_config('invalid_analysis', {'test': 'value'})
        self.assertFalse(result)
        
        # 尝试更新不存在的系统配置类型
        result = self.config_manager.update_system_config('invalid_system', {'test': 'value'})
        self.assertFalse(result)
        
        print("✓ 无效配置类型处理正确")
    
    def test_config_file_creation(self):
        """测试配置文件创建"""
        print("\n测试配置文件创建...")
        
        # 验证配置文件存在
        analysis_config_file = Path(self.temp_config_dir) / "analysis_config.json"
        system_config_file = Path(self.temp_config_dir) / "system_config.json"
        
        self.assertTrue(analysis_config_file.exists())
        self.assertTrue(system_config_file.exists())
        
        # 验证文件内容格式
        with open(analysis_config_file, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        with open(system_config_file, 'r', encoding='utf-8') as f:
            system_data = json.load(f)
        
        # 验证必要字段存在
        self.assertIn('event_analysis', analysis_data)
        self.assertIn('api_settings', system_data)
        
        print("✓ 配置文件创建和格式正确")


def run_config_tests():
    """运行配置管理测试"""
    print("🧪 开始配置管理功能测试")
    print("=" * 60)
    
    # 创建测试套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestConfigManager)
    
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
            print(f"  - {test}")
    
    if result.errors:
        print("\n💥 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\n✅ 测试成功率: {success_rate:.1f}%")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_config_tests()
    
    if success:
        print("\n🎉 所有配置管理测试通过!")
    else:
        print("\n⚠️ 部分测试失败，请检查实现")
        sys.exit(1)