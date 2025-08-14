#!/usr/bin/env python3
"""
Test script to validate i18n functionality
Checks if all hardcoded Chinese text has been replaced with translation keys
"""

import json
import re
import os
from pathlib import Path

def load_language_files():
    """Load language files"""
    zh_path = Path("languages/zh-CN.json")
    en_path = Path("languages/en-US.json")
    
    with open(zh_path, 'r', encoding='utf-8') as f:
        zh_translations = json.load(f)
    
    with open(en_path, 'r', encoding='utf-8') as f:
        en_translations = json.load(f)
    
    return zh_translations, en_translations

def check_main_py_hardcoded_chinese():
    """Check main.py for hardcoded Chinese text"""
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to find Chinese characters in strings
    chinese_pattern = r'["\'].*?[\u4e00-\u9fff].*?["\']'
    matches = re.findall(chinese_pattern, content)
    
    # Filter out comments and certain allowed patterns
    hardcoded_chinese = []
    for match in matches:
        # Skip if it's in a comment or specific allowed contexts
        if not any(skip_pattern in match for skip_pattern in [
            'help=', '# ', '"""', "'''", 'encoding=', 'decode=',
            'TIME_GRANULARITY_MAPPING', 'COHORT_PERIOD_MAPPING'
        ]):
            hardcoded_chinese.append(match)
    
    return hardcoded_chinese

def check_translation_coverage(zh_translations, en_translations):
    """Check if all Chinese translations have English equivalents"""
    def get_all_keys(d, prefix=""):
        """Recursively get all keys from nested dict"""
        keys = []
        for k, v in d.items():
            key_path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                keys.extend(get_all_keys(v, key_path))
            else:
                keys.append(key_path)
        return keys
    
    zh_keys = set(get_all_keys(zh_translations))
    en_keys = set(get_all_keys(en_translations))
    
    missing_in_english = zh_keys - en_keys
    missing_in_chinese = en_keys - zh_keys
    
    return missing_in_english, missing_in_chinese

def test_i18n_function():
    """Test the i18n function directly"""
    try:
        from utils.i18n import t, get_current_language
        
        # Test basic functionality
        test_key = "app.title"
        zh_result = t(test_key)
        
        print(f"Current language: {get_current_language()}")
        print(f"Translation for '{test_key}': {zh_result}")
        
        return True
    except Exception as e:
        print(f"Error testing i18n function: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing i18n Validation")
    print("=" * 50)
    
    # Test 1: Load language files
    print("📁 Loading language files...")
    try:
        zh_translations, en_translations = load_language_files()
        print(f"✅ Loaded {len(zh_translations)} Chinese translation groups")
        print(f"✅ Loaded {len(en_translations)} English translation groups")
    except Exception as e:
        print(f"❌ Failed to load language files: {e}")
        return False
    
    # Test 2: Check for hardcoded Chinese in main.py
    print("\n🔍 Checking for hardcoded Chinese text...")
    hardcoded_chinese = check_main_py_hardcoded_chinese()
    
    if hardcoded_chinese:
        print(f"⚠️ Found {len(hardcoded_chinese)} potential hardcoded Chinese strings:")
        for i, text in enumerate(hardcoded_chinese[:10], 1):  # Show first 10
            print(f"   {i}. {text}")
        if len(hardcoded_chinese) > 10:
            print(f"   ... and {len(hardcoded_chinese) - 10} more")
    else:
        print("✅ No obvious hardcoded Chinese text found in main.py")
    
    # Test 3: Check translation coverage
    print("\n🌐 Checking translation coverage...")
    missing_en, missing_zh = check_translation_coverage(zh_translations, en_translations)
    
    if missing_en:
        print(f"⚠️ {len(missing_en)} keys missing in English:")
        for key in list(missing_en)[:5]:
            print(f"   - {key}")
        if len(missing_en) > 5:
            print(f"   ... and {len(missing_en) - 5} more")
    else:
        print("✅ All Chinese keys have English translations")
    
    if missing_zh:
        print(f"⚠️ {len(missing_zh)} keys missing in Chinese:")
        for key in list(missing_zh)[:5]:
            print(f"   - {key}")
        if len(missing_zh) > 5:
            print(f"   ... and {len(missing_zh) - 5} more")
    else:
        print("✅ All English keys have Chinese translations")
    
    # Test 4: Test i18n function
    print("\n🔧 Testing i18n function...")
    i18n_works = test_i18n_function()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 50)
    
    total_issues = len(hardcoded_chinese) + len(missing_en) + len(missing_zh)
    
    if total_issues == 0 and i18n_works:
        print("🎉 All tests passed! i18n implementation looks good.")
        return True
    else:
        print(f"⚠️ Found {total_issues} potential issues.")
        if not i18n_works:
            print("❌ i18n function test failed.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)