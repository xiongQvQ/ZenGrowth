#!/usr/bin/env python3
"""
配置系统调试测试
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_config_system():
    """测试配置系统"""
    print("🔧 测试配置系统...")
    
    try:
        from utils.config_manager import config_manager
        
        # 检查配置文件
        print("\n1. 检查配置文件...")
        analysis_config_exists = config_manager.analysis_config_file.exists()
        system_config_exists = config_manager.system_config_file.exists()
        
        print(f"   分析配置文件存在: {analysis_config_exists}")
        print(f"   系统配置文件存在: {system_config_exists}")
        
        # 获取系统配置
        print("\n2. 获取系统配置...")
        system_config = config_manager.get_system_config()
        print(f"   系统配置类型: {type(system_config)}")
        print(f"   系统配置键: {list(system_config.keys())}")
        
        # 检查UI设置
        print("\n3. 检查UI设置...")
        ui_settings = system_config.get('ui_settings', {})
        print(f"   UI设置: {ui_settings}")
        
        current_language = ui_settings.get('language', 'zh-CN')
        print(f"   当前语言: {current_language}")
        
        # 测试更新语言设置
        print("\n4. 测试更新语言设置...")
        
        # 更新到英文
        success = config_manager.update_system_config('ui_settings', {'language': 'en-US'})
        print(f"   更新到英文结果: {success}")
        
        # 重新读取配置
        system_config_after = config_manager.get_system_config()
        ui_settings_after = system_config_after.get('ui_settings', {})
        language_after = ui_settings_after.get('language', 'zh-CN')
        print(f"   更新后语言: {language_after}")
        
        # 验证文件内容
        print("\n5. 验证配置文件内容...")
        if config_manager.system_config_file.exists():
            with open(config_manager.system_config_file, 'r', encoding='utf-8') as f:
                file_content = json.load(f)
                file_language = file_content.get('ui_settings', {}).get('language', 'zh-CN')
                print(f"   文件中的语言设置: {file_language}")
        
        # 恢复中文设置
        config_manager.update_system_config('ui_settings', {'language': 'zh-CN'})
        print("   已恢复中文设置")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_i18n_with_config():
    """测试i18n与配置的集成"""
    print("\n🌐 测试i18n与配置的集成...")
    
    try:
        from utils.config_manager import config_manager
        from utils.i18n import i18n, t
        
        # 设置英文
        print("\n1. 设置英文模式...")
        config_manager.update_system_config('ui_settings', {'language': 'en-US'})
        
        # 更新i18n语言设置
        i18n._update_current_language()
        current_lang = i18n.get_current_language()
        print(f"   i18n当前语言: {current_lang}")
        
        # 测试翻译
        title = t('app.title')
        upload = t('navigation.data_upload')
        print(f"   app.title: {title}")
        print(f"   navigation.data_upload: {upload}")
        
        # 检查是否为英文
        if current_lang == 'en-US' and 'User Behavior' in title and 'Data Upload' in upload:
            print("   ✅ 英文模式正常工作")
        else:
            print("   ❌ 英文模式未正常工作")
            return False
        
        # 设置中文
        print("\n2. 设置中文模式...")
        config_manager.update_system_config('ui_settings', {'language': 'zh-CN'})
        
        # 更新i18n语言设置
        i18n._update_current_language()
        current_lang = i18n.get_current_language()
        print(f"   i18n当前语言: {current_lang}")
        
        # 测试翻译
        title = t('app.title')
        upload = t('navigation.data_upload')
        print(f"   app.title: {title}")
        print(f"   navigation.data_upload: {upload}")
        
        # 检查是否为中文
        if current_lang == 'zh-CN' and '用户行为分析' in title and '数据上传' in upload:
            print("   ✅ 中文模式正常工作")
        else:
            print("   ❌ 中文模式未正常工作")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始配置系统调试测试...")
    
    tests = [
        test_config_system,
        test_i18n_with_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 配置系统和i18n集成测试通过！")
        return True
    else:
        print("\n⚠️  部分测试失败，需要进一步调试。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)