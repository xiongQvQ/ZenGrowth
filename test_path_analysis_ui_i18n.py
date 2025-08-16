#!/usr/bin/env python3
"""
Test path analysis UI i18n implementation.
Specifically check for Chinese text in UI elements.
"""

import sys
import os
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.i18n import t
from utils.config_manager import config_manager

def test_path_analysis_ui_keys():
    """Test critical path analysis UI translation keys."""
    print("\n🛤️ Testing Path Analysis UI Keys...")
    
    # Critical UI keys that should exist
    critical_keys = [
        'path_analysis',
        'start_path_analysis', 
        'path_results',
        'overview',
        'path_patterns',
        'visualizations', 
        'sessions',
        'insights'
    ]
    
    missing_keys = []
    chinese_keys = []
    
    for key in critical_keys:
        try:
            value = t(key, f"MISSING_KEY_{key}")
            if f"MISSING_KEY_{key}" in value:
                missing_keys.append(key)
            elif any('\u4e00' <= char <= '\u9fff' for char in value):
                chinese_keys.append((key, value))
        except Exception as e:
            missing_keys.append(f"{key} (error: {e})")
    
    success = True
    
    if missing_keys:
        print(f"  ❌ FAIL: Missing {len(missing_keys)} keys:")
        for key in missing_keys[:5]:
            print(f"    - {key}")
        success = False
    
    if chinese_keys:
        print(f"  ❌ FAIL: Found Chinese in {len(chinese_keys)} keys:")
        for key, value in chinese_keys[:3]:
            print(f"    - {key}: {value[:50]}...")
        success = False
    
    if success:
        print(f"  ✅ PASS: All {len(critical_keys)} critical UI keys found and in English")
        # Show sample outputs
        print("    Samples:")
        for key in critical_keys[:3]:
            value = t(key, f"Default {key}")
            print(f"      {key}: {value}")
    
    return success

def test_ui_labels_no_chinese():
    """Test that UI labels are not showing Chinese."""
    print("\n🌐 Testing UI Labels for Chinese Text...")
    
    # Test common UI elements
    ui_elements = [
        t('path_analysis', 'Path Analysis'),
        t('start_path_analysis', 'Start Path Analysis'), 
        t('path_results', 'Path Analysis Results'),
        t('overview', 'Overview'),
        t('path_patterns', 'Path Patterns'),
        t('visualizations', 'Visualizations'),
        t('sessions', 'Session Details'),
        t('insights', 'Insights & Recommendations')
    ]
    
    # Check for Chinese characters
    chinese_found = []
    for text in ui_elements:
        chinese_chars = [char for char in text if '\u4e00' <= char <= '\u9fff']
        if chinese_chars:
            chinese_found.append((text[:50] + "...", chinese_chars))
    
    if chinese_found:
        print(f"  ❌ FAIL: Found Chinese in {len(chinese_found)} UI elements:")
        for text, chars in chinese_found:
            print(f"    - '{text}' contains: {chars}")
        return False
    else:
        print(f"  ✅ PASS: No Chinese found in {len(ui_elements)} UI elements")
        return True

def main():
    """Run path analysis UI i18n tests."""
    print("🚀 Starting Path Analysis UI i18n Tests")
    print("="*60)
    
    tests = [
        ("UI Translation Keys", test_path_analysis_ui_keys),
        ("UI Labels No Chinese", test_ui_labels_no_chinese)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "="*60)
    print("📊 Path Analysis UI i18n Test Results Summary:")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SUCCESS! Path analysis UI is properly internationalized.")
        print("The path analysis page should now display English text when language is set to English mode.")
        return True
    else:
        print("\n⚠️  Some path analysis UI i18n tests failed. Please check the failures above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)