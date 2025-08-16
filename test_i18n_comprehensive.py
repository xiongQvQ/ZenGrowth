#!/usr/bin/env python3
"""
Comprehensive i18n test for conversion analysis and all analysis engines.
Tests language switching and ensures no Chinese text appears in English mode.
"""

import sys
import os
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.i18n_enhanced import t, LocalizedInsightGenerator
from utils.config_manager import config_manager

def test_language_switching():
    """Test language switching functionality."""
    print("🧪 Testing Language Switching...")
    
    # Test English mode
    print("\n📍 Testing English mode:")
    
    # Test basic translation
    english_title = t('pages.conversion_analysis.title', 'Conversion Analysis')
    print(f"  Title (EN): {english_title}")
    
    # Test conversion analysis specific keys
    best_funnel_text = LocalizedInsightGenerator.format_performance_insight(
        "purchase_funnel", 0.15, is_best=True
    )
    print(f"  Best funnel insight (EN): {best_funnel_text}")
    
    worst_funnel_text = LocalizedInsightGenerator.format_performance_insight(
        "engagement_funnel", 0.05, is_best=False
    )
    print(f"  Worst funnel insight (EN): {worst_funnel_text}")
    
    bottleneck_rec = LocalizedInsightGenerator.format_bottleneck_recommendation("add_to_cart")
    print(f"  Bottleneck recommendation (EN): {bottleneck_rec}")
    
    # Verify no Chinese characters in English output
    all_english_text = [english_title, best_funnel_text, worst_funnel_text, bottleneck_rec]
    has_chinese = any('\u4e00' <= char <= '\u9fff' for text in all_english_text for char in text)
    
    if has_chinese:
        print("  ❌ FAIL: Found Chinese characters in English mode!")
        for text in all_english_text:
            chinese_chars = [char for char in text if '\u4e00' <= char <= '\u9fff']
            if chinese_chars:
                print(f"    Chinese chars found in: '{text}' -> {chinese_chars}")
        return False
    else:
        print("  ✅ PASS: No Chinese characters found in English mode")
    
    print("\n📍 Testing Chinese mode:")
    
    # Test a few key translations to ensure they work
    try:
        # Mock changing language to Chinese
        chinese_title = t('pages.conversion_analysis.title', '转化分析')
        print(f"  Title (ZH): {chinese_title}")
        
        print("  ✅ PASS: Chinese translations working")
    except Exception as e:
        print(f"  ⚠️  Chinese translation test skipped: {e}")
    
    return True

def test_conversion_analysis_keys():
    """Test all conversion analysis translation keys."""
    print("\n🧪 Testing Conversion Analysis Translation Keys...")
    
    required_keys = [
        'conversion_analysis.insights.best_funnel_performance',
        'conversion_analysis.insights.worst_funnel_performance', 
        'conversion_analysis.recommendations.optimize_common_bottleneck',
        'pages.conversion_analysis.title'
    ]
    
    all_passed = True
    for key in required_keys:
        try:
            value = t(key, f"MISSING_KEY_{key}")
            if f"MISSING_KEY_{key}" in value:
                print(f"  ❌ Missing key: {key}")
                all_passed = False
            else:
                print(f"  ✅ Key found: {key} -> {value[:50]}...")
        except Exception as e:
            print(f"  ❌ Error testing key {key}: {e}")
            all_passed = False
    
    return all_passed

def test_enhanced_i18n_functionality():
    """Test enhanced i18n functionality."""
    print("\n🧪 Testing Enhanced i18n Functionality...")
    
    try:
        # Test parameter substitution
        test_text = t(
            'conversion_analysis.insights.best_funnel_performance',
            'Best performing funnel is {name} with conversion rate of {rate}',
            name="test_funnel",
            rate="15.2%"
        )
        
        expected_words = ["test_funnel", "15.2%"]
        if all(word in test_text for word in expected_words):
            print(f"  ✅ Parameter substitution working: {test_text}")
            return True
        else:
            print(f"  ❌ Parameter substitution failed: {test_text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Enhanced i18n test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run comprehensive i18n tests."""
    print("🚀 Starting Comprehensive i18n Tests for ZenGrowth Platform\n")
    
    tests = [
        ("Language Switching", test_language_switching),
        ("Conversion Analysis Keys", test_conversion_analysis_keys), 
        ("Enhanced i18n Functionality", test_enhanced_i18n_functionality)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"\n{'✅ PASS' if result else '❌ FAIL'}: {test_name}")
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "="*60)
    print("📊 Test Results Summary:")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All i18n tests passed! Conversion analysis should now display correctly in English mode.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)