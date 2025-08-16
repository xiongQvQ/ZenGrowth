#!/usr/bin/env python3
"""
Comprehensive i18n test for retention analysis module.
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

def test_retention_analysis_language_switching():
    """Test retention analysis language switching functionality."""
    print("🧪 Testing Retention Analysis Language Switching...")
    
    # Test English mode
    print("\n📍 Testing English mode:")
    
    # Test retention summary
    retention_summary = LocalizedInsightGenerator.format_retention_summary(5, "monthly")
    print(f"  Retention Summary (EN): {retention_summary}")
    
    # Test cohorts built
    cohorts_built = LocalizedInsightGenerator.format_cohorts_built(3)
    print(f"  Cohorts Built (EN): {cohorts_built}")
    
    # Test month 1 retention insight
    month1_insight = LocalizedInsightGenerator.format_month1_retention_insight(35.2)
    print(f"  Month 1 Insight (EN): {month1_insight}")
    
    # Test month 3 retention insight
    month3_insight = LocalizedInsightGenerator.format_month3_retention_insight(12.7)
    print(f"  Month 3 Insight (EN): {month3_insight}")
    
    # Test cohorts analyzed insight
    cohorts_analyzed = LocalizedInsightGenerator.format_cohorts_analyzed_insight(8)
    print(f"  Cohorts Analyzed (EN): {cohorts_analyzed}")
    
    # Test user profiles created
    profiles_created = LocalizedInsightGenerator.format_user_profiles_created(150)
    print(f"  Profiles Created (EN): {profiles_created}")
    
    # Test retention decline trend
    decline_trend = LocalizedInsightGenerator.format_retention_decline_trend()
    print(f"  Decline Trend (EN): {decline_trend}")
    
    # Test retention fast decline
    fast_decline = LocalizedInsightGenerator.format_retention_fast_decline()
    print(f"  Fast Decline (EN): {fast_decline}")
    
    # Test retention recommendations
    recommendations = [
        LocalizedInsightGenerator.format_retention_recommendation('low_first_period'),
        LocalizedInsightGenerator.format_retention_recommendation('month1_low'),
        LocalizedInsightGenerator.format_retention_recommendation('good_performance'),
        LocalizedInsightGenerator.format_retention_recommendation('insufficient_data')
    ]
    print(f"  Recommendations (EN): {recommendations[0][:50]}...")
    
    # Test retention risks
    risks = [
        LocalizedInsightGenerator.format_retention_risk('sharp_decline', 2),
        LocalizedInsightGenerator.format_retention_risk('overall_low'),
        LocalizedInsightGenerator.format_retention_risk('declining_trend'),
        LocalizedInsightGenerator.format_retention_risk('no_obvious_risks')
    ]
    print(f"  Risks (EN): {risks[0][:50]}...")
    
    # Verify no Chinese characters in English output
    all_english_text = [
        retention_summary, cohorts_built, month1_insight, month3_insight,
        cohorts_analyzed, profiles_created, decline_trend, fast_decline
    ] + recommendations + risks
    
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

def test_retention_analysis_translation_keys():
    """Test all retention analysis translation keys."""
    print("\n🧪 Testing Retention Analysis Translation Keys...")
    
    required_keys = [
        'retention.insights.analysis_summary',
        'retention.insights.cohorts_built',
        'retention.insights.month1_retention',
        'retention.insights.month3_retention',
        'retention.insights.analyzed_cohorts',
        'retention.insights.created_profiles',
        'retention.insights.gradual_decline',
        'retention.insights.fast_decline',
        'retention.recommendations.low_first_period',
        'retention.recommendations.improve_first_period',
        'retention.recommendations.low_long_term',
        'retention.recommendations.small_cohort_size',
        'retention.recommendations.large_variance',
        'retention.recommendations.good_performance',
        'retention.recommendations.insufficient_data',
        'retention.recommendations.month1_low',
        'retention.recommendations.month1_good',
        'retention.recommendations.month3_low',
        'retention.recommendations.maintain_strategy',
        'retention.recommendations.urgent_optimization',
        'retention.recommendations.sufficient_cohorts',
        'retention.recommendations.insufficient_cohorts',
        'retention.risks.period_sharp_decline',
        'retention.risks.overall_low',
        'retention.risks.declining_trend',
        'retention.risks.no_obvious_risks'
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

def test_retention_analysis_parameter_substitution():
    """Test parameter substitution in retention analysis translations."""
    print("\n🧪 Testing Retention Analysis Parameter Substitution...")
    
    try:
        # Test cohort count substitution
        summary_text = LocalizedInsightGenerator.format_retention_summary(7, "weekly")
        expected_values = ["7", "weekly"]
        
        if all(val in summary_text for val in expected_values):
            print(f"  ✅ Summary substitution working: {summary_text}")
        else:
            print(f"  ❌ Summary substitution failed: {summary_text}")
            return False
        
        # Test cohorts built substitution
        cohorts_text = LocalizedInsightGenerator.format_cohorts_built(12)
        expected_values = ["12"]
        
        if all(val in cohorts_text for val in expected_values):
            print(f"  ✅ Cohorts built substitution working: {cohorts_text}")
        else:
            print(f"  ❌ Cohorts built substitution failed: {cohorts_text}")
            return False
        
        # Test retention rate substitution
        retention_text = LocalizedInsightGenerator.format_month1_retention_insight(45.3)
        expected_values = ["45.3"]
        
        if all(val in retention_text for val in expected_values):
            print(f"  ✅ Retention rate substitution working: {retention_text}")
            return True
        else:
            print(f"  ❌ Retention rate substitution failed: {retention_text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Parameter substitution test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run comprehensive retention analysis i18n tests."""
    print("🚀 Starting Comprehensive Retention Analysis i18n Tests\n")
    
    tests = [
        ("Retention Analysis Language Switching", test_retention_analysis_language_switching),
        ("Retention Analysis Translation Keys", test_retention_analysis_translation_keys), 
        ("Retention Analysis Parameter Substitution", test_retention_analysis_parameter_substitution)
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
    print("📊 Retention Analysis i18n Test Results Summary:")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All retention analysis i18n tests passed! Retention analysis should now display correctly in English mode.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)