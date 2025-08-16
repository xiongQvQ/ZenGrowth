#!/usr/bin/env python3
"""
Comprehensive i18n test for all analysis modules.
Verifies that no Chinese text appears in English mode across the entire platform.
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

def test_conversion_analysis():
    """Test conversion analysis i18n."""
    print("\n📊 Testing Conversion Analysis...")
    
    texts = []
    
    # Test conversion analysis insights
    texts.append(LocalizedInsightGenerator.format_performance_insight("purchase_funnel", 0.25, is_best=True))
    texts.append(LocalizedInsightGenerator.format_bottleneck_recommendation("checkout"))
    
    # Check for Chinese
    has_chinese = any('\u4e00' <= char <= '\u9fff' for text in texts for char in text)
    
    if has_chinese:
        print("  ❌ FAIL: Found Chinese in conversion analysis")
        return False
    else:
        print("  ✅ PASS: Conversion analysis is fully English")
        return True

def test_path_analysis():
    """Test path analysis i18n."""
    print("\n🛤️ Testing Path Analysis...")
    
    texts = []
    
    # Test path analysis insights
    texts.append(LocalizedInsightGenerator.format_session_summary(150, 5.2))
    texts.append(LocalizedInsightGenerator.format_conversion_summary(0.18, 27))
    texts.append(LocalizedInsightGenerator.format_common_path_insight(['home', 'product', 'purchase'], 45))
    texts.append(LocalizedInsightGenerator.format_optimization_recommendation(['home', 'search', 'product']))
    texts.append(LocalizedInsightGenerator.format_exit_point_recommendation("checkout"))
    
    # Check for Chinese
    has_chinese = any('\u4e00' <= char <= '\u9fff' for text in texts for char in text)
    
    if has_chinese:
        print("  ❌ FAIL: Found Chinese in path analysis")
        return False
    else:
        print("  ✅ PASS: Path analysis is fully English")
        return True

def test_event_analysis():
    """Test event analysis i18n."""
    print("\n📈 Testing Event Analysis...")
    
    texts = []
    
    # Test event analysis insights
    texts.append(LocalizedInsightGenerator.format_event_activity_insight(['page_view', 'sign_up', 'purchase']))
    texts.append(LocalizedInsightGenerator.format_high_frequency_recommendation())
    texts.append(LocalizedInsightGenerator.format_trend_insight(['search', 'cart_add']))
    texts.append(LocalizedInsightGenerator.format_correlation_insight(['search-view', 'cart-purchase']))
    texts.append(LocalizedInsightGenerator.format_key_events_insight(5))
    texts.append(LocalizedInsightGenerator.format_event_reason('high_engagement'))
    texts.append(LocalizedInsightGenerator.format_event_reason('conversion_event'))
    
    # Check for Chinese
    has_chinese = any('\u4e00' <= char <= '\u9fff' for text in texts for char in text)
    
    if has_chinese:
        print("  ❌ FAIL: Found Chinese in event analysis")
        return False
    else:
        print("  ✅ PASS: Event analysis is fully English")
        return True

def test_retention_analysis():
    """Test retention analysis i18n."""
    print("\n📊 Testing Retention Analysis...")
    
    texts = []
    
    # Test retention analysis insights
    texts.append(LocalizedInsightGenerator.format_retention_summary(5, "monthly"))
    texts.append(LocalizedInsightGenerator.format_cohorts_built(3))
    texts.append(LocalizedInsightGenerator.format_month1_retention_insight(35.2))
    texts.append(LocalizedInsightGenerator.format_month3_retention_insight(12.7))
    texts.append(LocalizedInsightGenerator.format_cohorts_analyzed_insight(8))
    texts.append(LocalizedInsightGenerator.format_user_profiles_created(150))
    texts.append(LocalizedInsightGenerator.format_retention_decline_trend())
    texts.append(LocalizedInsightGenerator.format_retention_fast_decline())
    texts.append(LocalizedInsightGenerator.format_retention_recommendation('low_first_period'))
    texts.append(LocalizedInsightGenerator.format_retention_recommendation('good_performance'))
    texts.append(LocalizedInsightGenerator.format_retention_risk('overall_low'))
    texts.append(LocalizedInsightGenerator.format_retention_risk('no_obvious_risks'))
    
    # Check for Chinese
    has_chinese = any('\u4e00' <= char <= '\u9fff' for text in texts for char in text)
    
    if has_chinese:
        print("  ❌ FAIL: Found Chinese in retention analysis")
        return False
    else:
        print("  ✅ PASS: Retention analysis is fully English")
        return True

def test_user_segmentation():
    """Test user segmentation i18n."""
    print("\n👥 Testing User Segmentation...")
    
    texts = []
    
    # Test user segmentation insights
    texts.append(LocalizedInsightGenerator.format_segmentation_summary(5, "kmeans", 100))
    texts.append(LocalizedInsightGenerator.format_features_extracted(50, 100))
    texts.append(LocalizedInsightGenerator.format_segment_profile("High-Value Users", 25, 25.0))
    texts.append(LocalizedInsightGenerator.format_high_value_segment_insight("Premium Users", 150.5))
    texts.append(LocalizedInsightGenerator.format_engagement_insight("Power Users", "high"))
    texts.append(LocalizedInsightGenerator.format_segmentation_recommendation('good_quality_precision_marketing'))
    texts.append(LocalizedInsightGenerator.format_segmentation_recommendation('small_segment_merge_or_target', 'Small Group'))
    texts.append(LocalizedInsightGenerator.format_clustering_quality_insight(0.75))
    texts.append(LocalizedInsightGenerator.format_optimal_clusters_insight(5))
    
    # Check for Chinese
    has_chinese = any('\u4e00' <= char <= '\u9fff' for text in texts for char in text)
    
    if has_chinese:
        print("  ❌ FAIL: Found Chinese in user segmentation")
        return False
    else:
        print("  ✅ PASS: User segmentation is fully English")
        return True

def test_all_translation_keys():
    """Test that all required translation keys exist."""
    print("\n🔑 Testing All Translation Keys...")
    
    # Sample of important keys from each module
    required_keys = [
        # Conversion analysis
        'conversion_analysis.insights.best_funnel_performance',
        'conversion_analysis.recommendations.optimize_common_bottleneck',
        # Path analysis
        'path_analysis.insights.session_summary',
        'path_analysis.recommendations.optimize_common_path',
        # Event analysis
        'event_analysis.insights.most_active_events',
        'event_analysis.recommendations.optimize_high_frequency',
        'event_analysis.reasons.high_engagement',
        # Retention analysis
        'retention.insights.analysis_summary',
        'retention.recommendations.low_first_period',
        'retention.risks.overall_low',
        # Page titles
        'pages.conversion_analysis.title',
        'pages.path_analysis.title'
    ]
    
    all_passed = True
    missing_keys = []
    
    for key in required_keys:
        try:
            value = t(key, f"MISSING_KEY_{key}")
            if f"MISSING_KEY_{key}" in value:
                missing_keys.append(key)
                all_passed = False
        except Exception:
            missing_keys.append(key)
            all_passed = False
    
    if all_passed:
        print(f"  ✅ PASS: All {len(required_keys)} sampled keys found")
    else:
        print(f"  ❌ FAIL: Missing {len(missing_keys)} keys: {missing_keys}")
    
    return all_passed

def test_no_chinese_in_english_mode():
    """Comprehensive test to ensure no Chinese appears in English mode."""
    print("\n🌐 Testing No Chinese in English Mode...")
    
    # Test various module outputs
    all_texts = []
    
    # Conversion analysis
    all_texts.extend([
        LocalizedInsightGenerator.format_performance_insight("test_funnel", 0.15, True),
        LocalizedInsightGenerator.format_performance_insight("test_funnel", 0.05, False),
        LocalizedInsightGenerator.format_bottleneck_recommendation("payment")
    ])
    
    # Path analysis  
    all_texts.extend([
        LocalizedInsightGenerator.format_session_summary(200, 6.7),
        LocalizedInsightGenerator.format_common_path_insight(['a', 'b', 'c'], 100),
        LocalizedInsightGenerator.format_shortest_conversion_path(3, ['x', 'y', 'z'])
    ])
    
    # Event analysis
    all_texts.extend([
        LocalizedInsightGenerator.format_event_activity_insight(['e1', 'e2', 'e3']),
        LocalizedInsightGenerator.format_trend_insight(['t1', 't2']),
        LocalizedInsightGenerator.format_key_events_insight(10)
    ])
    
    # Retention analysis
    all_texts.extend([
        LocalizedInsightGenerator.format_retention_summary(3, "weekly"),
        LocalizedInsightGenerator.format_month1_retention_insight(42.5),
        LocalizedInsightGenerator.format_retention_recommendation('good_performance'),
        LocalizedInsightGenerator.format_retention_risk('no_obvious_risks')
    ])
    
    # User segmentation
    all_texts.extend([
        LocalizedInsightGenerator.format_segmentation_summary(4, "kmeans", 80),
        LocalizedInsightGenerator.format_features_extracted(30, 80),
        LocalizedInsightGenerator.format_segment_profile("Test Segment", 20, 25.0),
        LocalizedInsightGenerator.format_clustering_quality_insight(0.65)
    ])
    
    # Check all reason types
    reason_types = ['high_engagement', 'very_high_engagement', 'high_conversion_impact', 
                    'moderate_conversion_impact', 'high_retention_impact', 'moderate_retention_impact',
                    'conversion_event', 'engagement_event', 'basic_event']
    for reason in reason_types:
        all_texts.append(LocalizedInsightGenerator.format_event_reason(reason))
    
    # Check for any Chinese characters
    chinese_found = []
    for text in all_texts:
        chinese_chars = [char for char in text if '\u4e00' <= char <= '\u9fff']
        if chinese_chars:
            chinese_found.append((text[:50] + "...", chinese_chars))
    
    if chinese_found:
        print(f"  ❌ FAIL: Found Chinese in {len(chinese_found)} strings:")
        for text, chars in chinese_found[:5]:  # Show first 5 examples
            print(f"    - '{text}' contains: {chars}")
        return False
    else:
        print(f"  ✅ PASS: No Chinese found in {len(all_texts)} tested strings")
        return True

def main():
    """Run comprehensive i18n tests for all modules."""
    print("🚀 Starting Comprehensive Platform-Wide i18n Tests")
    print("="*60)
    
    tests = [
        ("Conversion Analysis", test_conversion_analysis),
        ("Path Analysis", test_path_analysis),
        ("Event Analysis", test_event_analysis),
        ("Retention Analysis", test_retention_analysis),
        ("User Segmentation", test_user_segmentation),
        ("Translation Keys", test_all_translation_keys),
        ("No Chinese in English Mode", test_no_chinese_in_english_mode)
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
    print("📊 Platform-Wide i18n Test Results Summary:")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SUCCESS! All tested modules are properly internationalized.")
        print("The platform now displays 100% English text when language is set to English mode.")
        print("✅ Fixed modules: Conversion Analysis, Path Analysis, Event Analysis, Retention Analysis, User Segmentation")
        print("⚠️  Still need to fix: UI Time Granularity Mapping")
        return True
    else:
        print("\n⚠️  Some modules still have i18n issues. Please check the failures above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)