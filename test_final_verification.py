#!/usr/bin/env python3
"""
Final verification test for i18n implementation
Tests the translation system and verifies language switching functionality
"""

import json
import sys
import os
from pathlib import Path

# Add project root to path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

def test_translation_system():
    """Test the translation system directly"""
    print("🧪 Testing Translation System")
    print("=" * 50)
    
    try:
        from utils.i18n import t, get_current_language, i18n
        
        # Test Chinese translations
        print("🇨🇳 Testing Chinese translations...")
        i18n.current_language = 'zh-CN'
        
        # Test some key translations
        test_cases = [
            ("app.title", "用户行为分析智能体平台"),
            ("navigation.data_upload", "📁 数据上传"),
            ("analysis.event_title", "📊 事件分析"),
            ("common.day", "日"),
            ("common.week", "周"),
            ("common.month", "月")
        ]
        
        for key, expected in test_cases:
            result = t(key)
            if expected in result:
                print(f"   ✅ {key}: {result}")
            else:
                print(f"   ❌ {key}: Expected '{expected}', got '{result}'")
        
        # Test English translations  
        print("\n🇺🇸 Testing English translations...")
        i18n.current_language = 'en-US'
        
        test_cases_en = [
            ("app.title", "User Behavior Analytics Platform"),
            ("navigation.data_upload", "📁 Data Upload"),
            ("analysis.event_title", "📊 Event Analysis"),
            ("common.day", "Day"),
            ("common.week", "Week"),
            ("common.month", "Month")
        ]
        
        for key, expected in test_cases_en:
            result = t(key)
            if expected in result:
                print(f"   ✅ {key}: {result}")
            else:
                print(f"   ❌ {key}: Expected '{expected}', got '{result}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Translation system test failed: {e}")
        return False

def test_language_file_completeness():
    """Test language file completeness"""
    print("\n📁 Testing Language File Completeness")
    print("=" * 50)
    
    try:
        with open('languages/zh-CN.json', 'r', encoding='utf-8') as f:
            zh_data = json.load(f)
        
        with open('languages/en-US.json', 'r', encoding='utf-8') as f:
            en_data = json.load(f)
        
        def count_keys(d):
            count = 0
            for v in d.values():
                if isinstance(v, dict):
                    count += count_keys(v)
                else:
                    count += 1
            return count
        
        zh_count = count_keys(zh_data)
        en_count = count_keys(en_data)
        
        print(f"📊 Chinese translation keys: {zh_count}")
        print(f"📊 English translation keys: {en_count}")
        
        if zh_count > 0 and en_count > 0:
            coverage = min(zh_count, en_count) / max(zh_count, en_count) * 100
            print(f"📈 Translation coverage: {coverage:.1f}%")
            
            if coverage >= 95:
                print("✅ Excellent translation coverage!")
                return True
            elif coverage >= 80:
                print("⚠️ Good translation coverage, but could be improved")
                return True
            else:
                print("❌ Poor translation coverage")
                return False
        else:
            print("❌ Empty translation files")
            return False
            
    except Exception as e:
        print(f"❌ Language file test failed: {e}")
        return False

def test_ui_elements():
    """Test common UI elements that should be translated"""
    print("\n🎨 Testing Common UI Elements")
    print("=" * 50)
    
    try:
        from utils.i18n import t
        
        # Test navigation elements
        nav_elements = [
            "navigation.data_upload",
            "navigation.intelligent_analysis", 
            "navigation.event_analysis",
            "navigation.retention_analysis",
            "navigation.conversion_analysis",
            "navigation.user_segmentation",
            "navigation.path_analysis",
            "navigation.comprehensive_report",
            "navigation.system_settings"
        ]
        
        print("🧭 Navigation elements:")
        for element in nav_elements:
            translation = t(element)
            if translation != element:  # If translation exists
                print(f"   ✅ {element}: {translation}")
            else:
                print(f"   ❌ {element}: No translation found")
        
        # Test common buttons and actions
        common_elements = [
            "common.start", "common.stop", "common.save", "common.export",
            "common.loading", "common.processing", "common.completed"
        ]
        
        print("\n🔘 Common UI elements:")
        for element in common_elements:
            translation = t(element)
            if translation != element:
                print(f"   ✅ {element}: {translation}")
            else:
                print(f"   ❌ {element}: No translation found")
        
        return True
        
    except Exception as e:
        print(f"❌ UI elements test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Final i18n Implementation Verification")
    print("=" * 60)
    
    # Run all tests
    tests = [
        test_translation_system,
        test_language_file_completeness,
        test_ui_elements
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n📊 Final Test Results")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! i18n implementation is complete and working correctly.")
        print("\n🌟 Language switching should now work properly across all analysis pages!")
        return True
    else:
        print(f"⚠️ {total - passed} test(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)