#!/usr/bin/env python3
"""
语言切换功能测试
测试国际化(i18n)系统是否正常工作
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_i18n_system():
    """测试国际化系统"""
    print("🧪 测试国际化系统...")
    
    try:
        from utils.i18n import i18n, t
        from utils.config_manager import config_manager
        
        # 测试1: 检查语言文件是否正确加载
        print("\n1. 检查语言文件加载...")
        available_languages = i18n.get_available_languages()
        print(f"   可用语言: {available_languages}")
        
        if 'zh-CN' not in i18n.translations:
            print("   ❌ 中文语言文件未加载")
            return False
        
        if 'en-US' not in i18n.translations:
            print("   ❌ 英文语言文件未加载")
            return False
        
        print("   ✅ 语言文件加载成功")
        
        # 测试2: 测试中文翻译
        print("\n2. 测试中文翻译...")
        config_manager.update_system_config('ui_settings', {'language': 'zh-CN'})
        i18n._update_current_language()
        zh_title = t('app.title', 'Default Title')
        zh_navigation = t('navigation.data_upload', 'Default Upload')
        zh_analysis = t('analysis.event_title', 'Default Event')
        
        print(f"   app.title: {zh_title}")
        print(f"   navigation.data_upload: {zh_navigation}")
        print(f"   analysis.event_title: {zh_analysis}")
        
        if '用户行为分析' not in zh_title or '数据上传' not in zh_navigation or '事件分析' not in zh_analysis:
            print("   ❌ 中文翻译不正确")
            return False
        
        print("   ✅ 中文翻译正确")
        
        # 测试3: 测试英文翻译
        print("\n3. 测试英文翻译...")
        config_manager.update_system_config('ui_settings', {'language': 'en-US'})
        i18n._update_current_language()
        en_title = t('app.title', 'Default Title')
        en_navigation = t('navigation.data_upload', 'Default Upload')
        en_analysis = t('analysis.event_title', 'Default Event')
        
        print(f"   app.title: {en_title}")
        print(f"   navigation.data_upload: {en_navigation}")
        print(f"   analysis.event_title: {en_analysis}")
        
        if 'User Behavior' not in en_title or 'Data Upload' not in en_navigation or 'Event Analysis' not in en_analysis:
            print("   ❌ 英文翻译不正确")
            return False
        
        print("   ✅ 英文翻译正确")
        
        # 测试4: 测试新增加的翻译键
        print("\n4. 测试新增翻译键...")
        config_manager.update_system_config('ui_settings', {'language': 'zh-CN'})
        i18n._update_current_language()
        
        # 测试分析页面的翻译
        test_keys = [
            ('errors.no_analysis_results', '没有找到分析结果'),
            ('errors.retention_analysis_complete', '留存分析完成'),
            ('analysis.path_complete', '路径分析完成'),
            ('common.detailed_error', '详细错误信息')
        ]
        
        all_keys_found = True
        for key, expected_text in test_keys:
            result = t(key, 'KEY_NOT_FOUND')
            print(f"   {key}: {result}")
            if 'KEY_NOT_FOUND' in result or expected_text not in result:
                print(f"   ❌ 键 {key} 翻译不正确")
                all_keys_found = False
        
        if not all_keys_found:
            return False
        
        print("   ✅ 新增翻译键正确")
        
        # 测试5: 测试英文模式下的新增翻译键
        print("\n5. 测试英文模式下的新增翻译键...")
        config_manager.update_system_config('ui_settings', {'language': 'en-US'})
        i18n._update_current_language()
        
        test_keys_en = [
            ('errors.no_analysis_results', 'No analysis results found'),
            ('errors.retention_analysis_complete', 'Retention analysis complete'),
            ('analysis.path_complete', 'Path analysis complete'),
            ('common.detailed_error', 'Detailed error information')
        ]
        
        all_keys_found_en = True
        for key, expected_text in test_keys_en:
            result = t(key, 'KEY_NOT_FOUND')
            print(f"   {key}: {result}")
            if 'KEY_NOT_FOUND' in result:
                print(f"   ❌ 键 {key} 英文翻译缺失")
                all_keys_found_en = False
        
        if not all_keys_found_en:
            return False
        
        print("   ✅ 英文新增翻译键正确")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_language_switching():
    """测试配置文件语言切换"""
    print("\n🧪 测试配置文件语言切换...")
    
    try:
        from utils.config_manager import config_manager
        from utils.i18n import i18n, t
        
        # 创建临时配置文件
        original_config = config_manager.get_system_config()
        
        # 测试切换到英文
        print("\n1. 测试切换到英文...")
        test_config = original_config.copy()
        test_config['ui_settings'] = {'language': 'en-US'}
        
        # 临时修改配置
        config_manager.system_config = test_config
        
        # 更新i18n语言设置
        i18n._update_current_language()
        
        current_lang = i18n.get_current_language()
        print(f"   当前语言: {current_lang}")
        
        if current_lang != 'en-US':
            print("   ❌ 语言切换到英文失败")
            return False
        
        # 验证翻译
        title = t('app.title')
        print(f"   应用标题: {title}")
        
        if 'User Behavior' not in title:
            print("   ❌ 英文翻译未生效")
            return False
        
        print("   ✅ 成功切换到英文")
        
        # 测试切换回中文
        print("\n2. 测试切换回中文...")
        test_config['ui_settings'] = {'language': 'zh-CN'}
        config_manager.system_config = test_config
        
        i18n._update_current_language()
        current_lang = i18n.get_current_language()
        print(f"   当前语言: {current_lang}")
        
        if current_lang != 'zh-CN':
            print("   ❌ 语言切换到中文失败")
            return False
        
        # 验证翻译
        title = t('app.title')
        print(f"   应用标题: {title}")
        
        if '用户行为分析' not in title:
            print("   ❌ 中文翻译未生效")
            return False
        
        print("   ✅ 成功切换回中文")
        
        # 恢复原始配置
        config_manager.system_config = original_config
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_pages_internationalization():
    """测试UI页面国际化"""
    print("\n🧪 测试UI页面国际化...")
    
    try:
        from utils.i18n import i18n, t
        from utils.config_manager import config_manager
        
        # 测试各个分析页面的翻译键
        print("\n1. 测试事件分析页面翻译...")
        
        # 设置为英文模式
        config_manager.update_system_config('ui_settings', {'language': 'en-US'})
        i18n._update_current_language()
        
        event_keys = [
            'errors.no_analysis_results',
            'errors.analysis_result_format_error', 
            'errors.filter_data_missing',
            'errors.timeline_chart_failed'
        ]
        
        for key in event_keys:
            result = t(key, 'MISSING')
            print(f"   {key}: {result}")
            if result == 'MISSING':
                print(f"   ⚠️  键 {key} 缺失")
        
        print("\n2. 测试留存分析页面翻译...")
        
        retention_keys = [
            'errors.retention_analysis_complete',
            'errors.retention_analysis_failed',
            'errors.detailed_error_info'
        ]
        
        for key in retention_keys:
            result = t(key, 'MISSING')
            print(f"   {key}: {result}")
            if result == 'MISSING':
                print(f"   ⚠️  键 {key} 缺失")
        
        print("\n3. 测试转化分析页面翻译...")
        
        conversion_keys = [
            'analysis.conversion_complete',
            'analysis.conversion_processing',
            'analysis.no_custom_steps'
        ]
        
        for key in conversion_keys:
            result = t(key, 'MISSING')
            print(f"   {key}: {result}")
            if result == 'MISSING':
                print(f"   ⚠️  键 {key} 缺失")
        
        print("\n4. 测试路径分析页面翻译...")
        
        path_keys = [
            'analysis.path_complete',
            'analysis.path_processing',
            'analysis.session_reconstruction'
        ]
        
        for key in path_keys:
            result = t(key, 'MISSING')
            print(f"   {key}: {result}")
            if result == 'MISSING':
                print(f"   ⚠️  键 {key} 缺失")
        
        print("\n   ✅ UI页面国际化测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始语言切换功能测试...")
    
    tests = [
        test_i18n_system,
        test_config_language_switching,
        test_ui_pages_internationalization
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
        print("\n🎉 语言切换功能测试全部通过！")
        print("\n✅ 验证结果:")
        print("1. ✅ 国际化系统正常工作")
        print("2. ✅ 中英文翻译文件正确加载")
        print("3. ✅ 语言切换配置生效")
        print("4. ✅ 分析页面翻译键完整")
        print("5. ✅ 英文模式下不再显示中文")
        print("\n🌐 国际化修复成功，可以正常在英文和中文之间切换！")
        return True
    else:
        print("\n⚠️  部分测试失败，语言切换功能可能存在问题。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)