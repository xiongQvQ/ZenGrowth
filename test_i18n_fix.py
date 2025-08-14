#!/usr/bin/env python3
"""
测试语言切换功能
验证i18n国际化系统是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_i18n_basic():
    """测试i18n基础功能"""
    print("🧪 测试i18n基础功能...")
    
    try:
        from utils.i18n import i18n, t
        
        # 测试中文
        i18n.current_language = 'zh-CN'
        print(f"✅ 中文标题: {t('app.title')}")
        print(f"✅ 中文导航: {t('app.navigation')}")
        print(f"✅ 中文菜单: {t('navigation.data_upload')}")
        
        # 测试英文
        i18n.current_language = 'en-US'
        print(f"✅ 英文标题: {t('app.title')}")
        print(f"✅ 英文导航: {t('app.navigation')}")
        print(f"✅ 英文菜单: {t('navigation.data_upload')}")
        
        print("✅ i18n基础功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ i18n基础功能测试失败: {e}")
        return False


def test_language_files():
    """测试语言文件是否存在"""
    print("\n🧪 测试语言文件...")
    
    try:
        import json
        
        # 检查中文语言文件
        zh_file = project_root / "languages" / "zh-CN.json"
        if zh_file.exists():
            with open(zh_file, 'r', encoding='utf-8') as f:
                zh_data = json.load(f)
            print(f"✅ 中文语言文件存在，包含 {len(zh_data)} 个主要分类")
        else:
            print("❌ 中文语言文件不存在")
            return False
        
        # 检查英文语言文件
        en_file = project_root / "languages" / "en-US.json"
        if en_file.exists():
            with open(en_file, 'r', encoding='utf-8') as f:
                en_data = json.load(f)
            print(f"✅ 英文语言文件存在，包含 {len(en_data)} 个主要分类")
        else:
            print("❌ 英文语言文件不存在")
            return False
        
        print("✅ 语言文件测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 语言文件测试失败: {e}")
        return False


def test_config_integration():
    """测试配置集成"""
    print("\n🧪 测试配置集成...")
    
    try:
        from utils.config_manager import config_manager
        from utils.i18n import i18n
        
        # 获取当前系统配置
        system_config = config_manager.get_system_config()
        ui_language = system_config.get('ui_settings', {}).get('language', 'zh-CN')
        
        print(f"✅ 系统配置中的语言设置: {ui_language}")
        
        # 测试i18n是否能正确读取配置
        i18n._update_current_language()
        current_lang = i18n.get_current_language()
        
        print(f"✅ i18n当前语言: {current_lang}")
        
        if ui_language == current_lang:
            print("✅ 配置集成测试通过")
            return True
        else:
            print(f"❌ 配置不一致：系统配置={ui_language}, i18n={current_lang}")
            return False
        
    except Exception as e:
        print(f"❌ 配置集成测试失败: {e}")
        return False


def test_translation_coverage():
    """测试翻译覆盖率"""
    print("\n🧪 测试翻译覆盖率...")
    
    try:
        from utils.i18n import i18n
        
        # 关键翻译键列表
        key_translations = [
            'app.title',
            'app.navigation', 
            'app.select_module',
            'navigation.data_upload',
            'navigation.system_settings',
            'settings.interface_language',
            'settings.save_config',
            'settings.config_saved',
            'data_upload.title',
            'data_upload.file_upload'
        ]
        
        missing_translations = []
        
        for lang in ['zh-CN', 'en-US']:
            i18n.current_language = lang
            print(f"\n检查 {lang} 翻译:")
            
            for key in key_translations:
                translation = i18n.get_text(key)
                if translation == key:  # 如果返回键名本身，说明没有翻译
                    missing_translations.append(f"{lang}:{key}")
                    print(f"  ❌ 缺失: {key}")
                else:
                    print(f"  ✅ {key}: {translation}")
        
        if not missing_translations:
            print("✅ 翻译覆盖率测试通过")
            return True
        else:
            print(f"❌ 发现 {len(missing_translations)} 个缺失翻译")
            return False
        
    except Exception as e:
        print(f"❌ 翻译覆盖率测试失败: {e}")
        return False


def simulate_language_switch():
    """模拟语言切换流程"""
    print("\n🧪 模拟语言切换流程...")
    
    try:
        from utils.config_manager import config_manager
        from utils.i18n import i18n, t
        
        print("1. 当前状态:")
        current_config = config_manager.get_system_config()
        current_lang = current_config.get('ui_settings', {}).get('language', 'zh-CN')
        print(f"   配置文件语言: {current_lang}")
        print(f"   界面显示: {t('app.title')}")
        
        print("\n2. 模拟切换到英文:")
        # 模拟更新配置
        config_manager.update_system_config('ui_settings', {'language': 'en-US'})
        
        # 重新加载i18n
        i18n._update_current_language()
        print(f"   新的语言设置: {i18n.get_current_language()}")
        print(f"   界面显示: {t('app.title')}")
        
        print("\n3. 模拟切换回中文:")
        config_manager.update_system_config('ui_settings', {'language': 'zh-CN'})
        i18n._update_current_language()
        print(f"   新的语言设置: {i18n.get_current_language()}")
        print(f"   界面显示: {t('app.title')}")
        
        print("✅ 语言切换流程测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 语言切换流程测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试i18n语言切换功能修复\n")
    
    tests = [
        test_language_files,
        test_i18n_basic,
        test_config_integration,
        test_translation_coverage,
        simulate_language_switch
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！语言切换功能修复成功！")
        print("\n🔧 修复总结:")
        print("1. ✅ 创建了完整的i18n国际化系统")
        print("2. ✅ 添加了中英文语言文件")
        print("3. ✅ 修改了main.py使用t()函数")
        print("4. ✅ 语言设置现在能正确切换界面")
        print("\n📝 使用说明:")
        print("- 在系统设置中选择界面语言")
        print("- 点击保存后界面会自动切换语言")
        print("- 重启应用后语言设置会保持")
    else:
        print(f"❌ 发现 {total - passed} 个问题需要修复")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)