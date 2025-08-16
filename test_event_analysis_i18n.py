#!/usr/bin/env python3
"""
Comprehensive i18n test for event analysis module.
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

def test_event_analysis_language_switching():
    """Test event analysis language switching functionality."""
    print("🧪 Testing Event Analysis Language Switching...")
    
    # Test English mode
    print("\n📍 Testing English mode:")
    
    # Test event activity insight
    event_activity = LocalizedInsightGenerator.format_event_activity_insight(['page_view', 'sign_up', 'purchase'])
    print(f"  Event Activity (EN): {event_activity}")
    
    # Test high frequency recommendation
    high_freq_rec = LocalizedInsightGenerator.format_high_frequency_recommendation()
    print(f"  High Frequency Rec (EN): {high_freq_rec}")
    
    # Test trend insight
    trend_insight = LocalizedInsightGenerator.format_trend_insight(['search', 'add_to_cart', 'checkout'])
    print(f"  Trend Insight (EN): {trend_insight}")
    
    # Test trend recommendation
    trend_rec = LocalizedInsightGenerator.format_trend_recommendation()
    print(f"  Trend Rec (EN): {trend_rec}")
    
    # Test correlation insight
    correlation_insight = LocalizedInsightGenerator.format_correlation_insight(['search-product_view', 'cart-purchase'])
    print(f"  Correlation Insight (EN): {correlation_insight}")
    
    # Test correlation recommendation
    correlation_rec = LocalizedInsightGenerator.format_correlation_recommendation()
    print(f"  Correlation Rec (EN): {correlation_rec}")
    
    # Test key events insight
    key_events = LocalizedInsightGenerator.format_key_events_insight(5)
    print(f"  Key Events (EN): {key_events}")
    
    # Test key events recommendation
    key_events_rec = LocalizedInsightGenerator.format_key_events_recommendation()
    print(f"  Key Events Rec (EN): {key_events_rec}")
    
    # Test event reasons
    reasons = [
        LocalizedInsightGenerator.format_event_reason('very_high_engagement'),
        LocalizedInsightGenerator.format_event_reason('high_conversion_impact'),
        LocalizedInsightGenerator.format_event_reason('conversion_event')
    ]
    print(f"  Event Reasons (EN): {reasons[0]}, {reasons[1]}, {reasons[2]}")
    
    # Verify no Chinese characters in English output
    all_english_text = [
        event_activity, high_freq_rec, trend_insight, trend_rec,
        correlation_insight, correlation_rec, key_events, key_events_rec
    ] + reasons
    
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

def test_event_analysis_translation_keys():
    """Test all event analysis translation keys."""
    print("\n🧪 Testing Event Analysis Translation Keys...")
    
    required_keys = [
        'event_analysis.insights.most_active_events',
        'event_analysis.insights.increasing_trends',
        'event_analysis.insights.strong_correlations',
        'event_analysis.insights.key_events_found',
        'event_analysis.recommendations.optimize_high_frequency',
        'event_analysis.recommendations.optimize_trends',
        'event_analysis.recommendations.leverage_correlations',
        'event_analysis.recommendations.monitor_key_events',
        'event_analysis.reasons.high_engagement',
        'event_analysis.reasons.very_high_engagement',
        'event_analysis.reasons.high_conversion_impact',
        'event_analysis.reasons.moderate_conversion_impact',
        'event_analysis.reasons.high_retention_impact',
        'event_analysis.reasons.moderate_retention_impact',
        'event_analysis.reasons.conversion_event',
        'event_analysis.reasons.engagement_event',
        'event_analysis.reasons.basic_event'
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

def test_event_analysis_parameter_substitution():
    """Test parameter substitution in event analysis translations."""
    print("\n🧪 Testing Event Analysis Parameter Substitution...")
    
    try:
        # Test event list substitution
        events_text = LocalizedInsightGenerator.format_event_activity_insight(['login', 'search', 'purchase'])
        expected_values = ["login, search, purchase"]
        
        if all(val in events_text for val in expected_values):
            print(f"  ✅ Event list substitution working: {events_text}")
        else:
            print(f"  ❌ Event list substitution failed: {events_text}")
            return False
        
        # Test trend list substitution
        trends_text = LocalizedInsightGenerator.format_trend_insight(['cart_add', 'wishlist_add'])
        expected_values = ["cart_add, wishlist_add"]
        
        if all(val in trends_text for val in expected_values):
            print(f"  ✅ Trend list substitution working: {trends_text}")
        else:
            print(f"  ❌ Trend list substitution failed: {trends_text}")
            return False
        
        # Test count substitution
        count_text = LocalizedInsightGenerator.format_key_events_insight(7)
        expected_values = ["7"]
        
        if all(val in count_text for val in expected_values):
            print(f"  ✅ Count substitution working: {count_text}")
            return True
        else:
            print(f"  ❌ Count substitution failed: {count_text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Parameter substitution test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run comprehensive event analysis i18n tests."""
    print("🚀 Starting Comprehensive Event Analysis i18n Tests\n")
    
    tests = [
        ("Event Analysis Language Switching", test_event_analysis_language_switching),
        ("Event Analysis Translation Keys", test_event_analysis_translation_keys), 
        ("Event Analysis Parameter Substitution", test_event_analysis_parameter_substitution)
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
    print("📊 Event Analysis i18n Test Results Summary:")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All event analysis i18n tests passed! Event analysis should now display correctly in English mode.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)