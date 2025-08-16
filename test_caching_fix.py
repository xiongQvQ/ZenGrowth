"""
简单的缓存修复测试
验证缓存组件是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_cached_components():
    """测试缓存组件"""
    print("🔍 测试缓存组件...")
    
    try:
        # 测试缓存的GA4解析器
        from utils.cached_components import get_cached_ga4_parser
        parser1 = get_cached_ga4_parser()
        parser2 = get_cached_ga4_parser()
        
        # 验证是否返回同一个实例（缓存生效）
        is_same_instance = parser1 is parser2
        print(f"  ✅ GA4Parser缓存: {'生效' if is_same_instance else '未生效'} (实例相同: {is_same_instance})")
        
        # 测试缓存的数据验证器
        from utils.cached_components import get_cached_data_validator
        validator1 = get_cached_data_validator()
        validator2 = get_cached_data_validator()
        
        is_same_validator = validator1 is validator2
        print(f"  ✅ DataValidator缓存: {'生效' if is_same_validator else '未生效'} (实例相同: {is_same_validator})")
        
    except Exception as e:
        print(f"  ❌ 缓存组件测试失败: {e}")


def test_data_upload_page():
    """测试数据上传页面初始化"""
    print("\n🚀 测试数据上传页面初始化...")
    
    try:
        from ui.pages.data_upload import DataUploadPage
        
        # 创建页面实例
        page1 = DataUploadPage()
        page2 = DataUploadPage()
        
        # 验证解析器是否来自缓存
        parser_cached = page1.parser is page2.parser
        validator_cached = page1.validator is page2.validator
        
        print(f"  ✅ Parser缓存: {'生效' if parser_cached else '未生效'}")
        print(f"  ✅ Validator缓存: {'生效' if validator_cached else '未生效'}")
        
        if parser_cached and validator_cached:
            print("  🎉 数据上传页面缓存优化成功！")
        
    except Exception as e:
        print(f"  ❌ 数据上传页面测试失败: {e}")


def test_manager_caching():
    """测试管理器缓存"""
    print("\n⚡ 测试管理器缓存...")
    
    try:
        # 测试集成管理器缓存
        from utils.cached_components import get_cached_integration_manager
        manager1 = get_cached_integration_manager()
        manager2 = get_cached_integration_manager()
        
        is_same_manager = manager1 is manager2
        print(f"  ✅ IntegrationManager缓存: {'生效' if is_same_manager else '未生效'}")
        
    except Exception as e:
        print(f"  ❌ 管理器缓存测试失败: {e}")


def main():
    """主测试函数"""
    print("🔧 开始缓存修复测试...")
    print("=" * 50)
    
    test_cached_components()
    test_data_upload_page()
    test_manager_caching()
    
    print("\n" + "=" * 50)
    print("✅ 缓存修复测试完成！")
    print("💡 提示: 如果所有缓存都显示'生效'，则性能问题已解决")


if __name__ == "__main__":
    main()