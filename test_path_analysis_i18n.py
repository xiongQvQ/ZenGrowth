#!/usr/bin/env python3
"""
Comprehensive i18n test for path analysis module.
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

def test_path_analysis_language_switching():
    """Test path analysis language switching functionality."""
    print("🧪 Testing Path Analysis Language Switching...")
    
    # Test English mode
    print("\n📍 Testing English mode:")
    
    # Test basic page title translation
    page_title = t('pages.path_analysis.title', 'Path Analysis')
    print(f"  Page Title (EN): {page_title}")
    
    # Test session summary insight
    session_summary = LocalizedInsightGenerator.format_session_summary(100, 4.5)
    print(f"  Session Summary (EN): {session_summary}")
    
    # Test conversion summary insight
    conversion_summary = LocalizedInsightGenerator.format_conversion_summary(0.15, 15)
    print(f"  Conversion Summary (EN): {conversion_summary}")
    
    # Test common path insight
    common_path = LocalizedInsightGenerator.format_common_path_insight(
        ["homepage", "product_page", "checkout", "purchase"], 45
    )
    print(f"  Common Path (EN): {common_path}")
    
    # Test conversion patterns insight
    conversion_patterns = LocalizedInsightGenerator.format_conversion_patterns_insight(3)
    print(f"  Conversion Patterns (EN): {conversion_patterns}")
    
    # Test anomalous patterns insight
    anomalous_patterns = LocalizedInsightGenerator.format_anomalous_patterns_insight(2)
    print(f"  Anomalous Patterns (EN): {anomalous_patterns}")
    
    # Test shortest conversion path insight
    shortest_path = LocalizedInsightGenerator.format_shortest_conversion_path(
        3, ["homepage", "product_page", "purchase"]
    )
    print(f"  Shortest Path (EN): {shortest_path}")
    
    # Test optimization recommendation
    optimization_rec = LocalizedInsightGenerator.format_optimization_recommendation(
        ["homepage", "search", "product_page", "checkout"]
    )
    print(f"  Optimization Rec (EN): {optimization_rec}")
    
    # Test exit point recommendation  
    exit_point_rec = LocalizedInsightGenerator.format_exit_point_recommendation("checkout")
    print(f"  Exit Point Rec (EN): {exit_point_rec}")
    
    # Verify no Chinese characters in English output
    all_english_text = [
        page_title, session_summary, conversion_summary, common_path,
        conversion_patterns, anomalous_patterns, shortest_path,
        optimization_rec, exit_point_rec
    ]
    
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
    
    return True

def test_path_analysis_translation_keys():
    """Test all path analysis translation keys."""
    print("\n🧪 Testing Path Analysis Translation Keys...")
    
    required_keys = [
        'pages.path_analysis.title',
        'path_analysis.insights.session_summary',
        'path_analysis.insights.conversion_summary',
        'path_analysis.insights.most_common_path',
        'path_analysis.insights.high_conversion_patterns',
        'path_analysis.insights.anomalous_patterns',
        'path_analysis.insights.shortest_conversion_path',
        'path_analysis.recommendations.optimize_common_path',
        'path_analysis.recommendations.optimize_exit_point',
        'path_analysis.recommendations.simplify_user_flow',
        'path_analysis.recommendations.investigate_anomalies',
        'path_analysis.recommendations.provide_shortcuts',
        'path_analysis.errors.empty_event_data',
        'path_analysis.errors.session_reconstruction_failed'
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

def test_path_analysis_parameter_substitution():
    """Test parameter substitution in path analysis translations."""
    print("\n🧪 Testing Path Analysis Parameter Substitution...")
    
    try:
        # Test session summary with parameters
        session_text = LocalizedInsightGenerator.format_session_summary(150, 5.2)
        expected_values = ["150", "5.2"]
        
        if all(str(val) in session_text for val in expected_values):
            print(f"  ✅ Session summary substitution working: {session_text}")
        else:
            print(f"  ❌ Session summary substitution failed: {session_text}")
            return False
        
        # Test conversion summary with parameters
        conversion_text = LocalizedInsightGenerator.format_conversion_summary(0.23, 35)
        expected_values = ["23.0%", "35"]  # 0.23 should format as 23.0%
        
        if all(str(val) in conversion_text for val in expected_values):
            print(f"  ✅ Conversion summary substitution working: {conversion_text}")
        else:
            print(f"  ❌ Conversion summary substitution failed: {conversion_text}")
            return False
        
        # Test path sequence substitution
        path_text = LocalizedInsightGenerator.format_common_path_insight(
            ["home", "search", "product"], 28
        )
        expected_values = ["home → search → product", "28"]
        
        if all(str(val) in path_text for val in expected_values):
            print(f"  ✅ Path sequence substitution working: {path_text}")
            return True
        else:
            print(f"  ❌ Path sequence substitution failed: {path_text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Parameter substitution test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run comprehensive path analysis i18n tests."""
    print("🚀 Starting Comprehensive Path Analysis i18n Tests\n")
    
    tests = [
        ("Path Analysis Language Switching", test_path_analysis_language_switching),
        ("Path Analysis Translation Keys", test_path_analysis_translation_keys), 
        ("Path Analysis Parameter Substitution", test_path_analysis_parameter_substitution)
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
    print("📊 Path Analysis i18n Test Results Summary:")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All path analysis i18n tests passed! Path analysis should now display correctly in English mode.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)