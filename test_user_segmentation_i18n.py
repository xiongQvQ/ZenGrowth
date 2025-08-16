#!/usr/bin/env python3
"""
Test user segmentation i18n implementation.
Verifies that user segmentation engine displays English in English mode.
"""

import sys
import os
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.i18n_enhanced import LocalizedInsightGenerator, t
from utils.config_manager import config_manager

def test_user_segmentation_localized_generator():
    """Test LocalizedInsightGenerator for user segmentation methods."""
    print("\n👥 Testing User Segmentation LocalizedInsightGenerator...")
    
    texts = []
    
    # Test segmentation summary
    texts.append(LocalizedInsightGenerator.format_segmentation_summary(5, "kmeans", 100))
    
    # Test features extracted
    texts.append(LocalizedInsightGenerator.format_features_extracted(50, 100))
    
    # Test segment profile
    texts.append(LocalizedInsightGenerator.format_segment_profile("High-Value Active Users", 25, 25.0))
    
    # Test high value segment insight
    texts.append(LocalizedInsightGenerator.format_high_value_segment_insight("Premium Users", 150.5))
    
    # Test engagement insight
    texts.append(LocalizedInsightGenerator.format_engagement_insight("Power Users", "high"))
    
    # Test segmentation recommendations
    texts.append(LocalizedInsightGenerator.format_segmentation_recommendation('good_quality_precision_marketing'))
    texts.append(LocalizedInsightGenerator.format_segmentation_recommendation('small_segment_merge_or_target', 'Small Group'))
    texts.append(LocalizedInsightGenerator.format_segmentation_recommendation('large_segment_further_subdivide', 'Large Group'))
    texts.append(LocalizedInsightGenerator.format_segmentation_recommendation('focus_high_value_needs_quality_service'))
    
    # Test clustering quality insight
    texts.append(LocalizedInsightGenerator.format_clustering_quality_insight(0.75))
    
    # Test optimal clusters insight
    texts.append(LocalizedInsightGenerator.format_optimal_clusters_insight(5))
    
    # Check for Chinese characters
    has_chinese = any('\u4e00' <= char <= '\u9fff' for text in texts for char in text)
    
    if has_chinese:
        print("  ❌ FAIL: Found Chinese in user segmentation LocalizedInsightGenerator")
        chinese_texts = [text for text in texts if any('\u4e00' <= char <= '\u9fff' for char in text)]
        for text in chinese_texts[:3]:
            print(f"    - Chinese found: {text[:100]}...")
        return False
    else:
        print("  ✅ PASS: User segmentation LocalizedInsightGenerator is fully English")
        # Show sample outputs
        for i, text in enumerate(texts[:3]):
            print(f"    Sample {i+1}: {text}")
        return True

def test_user_segmentation_translation_keys():
    """Test critical user segmentation translation keys."""
    print("\n🔑 Testing User Segmentation Translation Keys...")
    
    # Critical keys that should exist
    critical_keys = [
        'user_segmentation.logs.engine_initialized',
        'user_segmentation.logs.feature_extraction_failed',
        'user_segmentation.logs.segmentation_creation_failed',
        'user_segmentation.insights.analysis_summary',
        'user_segmentation.insights.features_extracted',
        'user_segmentation.insights.segment_profile',
        'user_segmentation.insights.clustering_quality',
        'user_segmentation.insights.optimal_clusters',
        'user_segmentation.recommendations.good_quality_precision_marketing',
        'user_segmentation.recommendations.small_segment_merge_or_target',
        'user_segmentation.recommendations.large_segment_further_subdivide',
        'user_segmentation.errors.unsupported_method'
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
        print(f"  ✅ PASS: All {len(critical_keys)} critical keys found and in English")
    
    return success

def test_segment_name_translations():
    """Test segment name translations."""
    print("\n📛 Testing Segment Name Translations...")
    
    segment_combinations = [
        ('high', 'high'), ('high', 'medium'), ('high', 'low'),
        ('medium', 'high'), ('medium', 'medium'), ('medium', 'low'),
        ('low', 'high'), ('low', 'medium'), ('low', 'low')
    ]
    
    texts = []
    
    for engagement, value in segment_combinations:
        key = f'user_segmentation.segment_names.{engagement}_engagement_{value}_value'
        text = t(key, f'Default {engagement} engagement {value} value')
        texts.append(text)
    
    # Check for Chinese
    has_chinese = any('\u4e00' <= char <= '\u9fff' for text in texts for char in text)
    
    if has_chinese:
        print("  ❌ FAIL: Found Chinese in segment names")
        chinese_texts = [text for text in texts if any('\u4e00' <= char <= '\u9fff' for char in text)]
        for text in chinese_texts[:3]:
            print(f"    - Chinese found: {text}")
        return False
    else:
        print("  ✅ PASS: All segment names are in English")
        # Show some samples
        for i, text in enumerate(texts[:3]):
            print(f"    Sample {i+1}: {text}")
        return True

def test_comprehensive_user_segmentation():
    """Comprehensive test of user segmentation i18n."""
    print("\n🏁 Testing Comprehensive User Segmentation i18n...")
    
    # Test various scenarios that would appear in user segmentation results
    test_texts = []
    
    # Simulate insights that would be generated
    test_texts.append(t('user_segmentation.insights.segments_identified', 'Identified {segment_count} user segments').format(segment_count=5))
    test_texts.append(t('user_segmentation.insights.segment_quality_good', 'Segmentation quality is good, user groups are well-distinguished'))
    test_texts.append(t('user_segmentation.insights.high_value_user_segments', 'High-value user segments: {segment_names}').format(segment_names='Group A, Group B'))
    test_texts.append(t('user_segmentation.insights.main_distinguishing_features', 'Main distinguishing features: {features}').format(features='engagement, conversion, activity'))
    
    # Test recommendations
    test_texts.append(LocalizedInsightGenerator.format_segmentation_recommendation('good_quality_precision_marketing'))
    test_texts.append(LocalizedInsightGenerator.format_segmentation_recommendation('focus_high_value_retention'))
    
    # Test log messages
    test_texts.append(t('user_segmentation.logs.engine_initialized', 'User segmentation engine initialized successfully'))
    test_texts.append(t('user_segmentation.logs.clustering_completed', 'Clustering completed, generated {segment_count} segments').format(segment_count=5))
    
    # Check for Chinese
    chinese_found = []
    for text in test_texts:
        chinese_chars = [char for char in text if '\u4e00' <= char <= '\u9fff']
        if chinese_chars:
            chinese_found.append((text[:50] + "...", chinese_chars))
    
    if chinese_found:
        print(f"  ❌ FAIL: Found Chinese in {len(chinese_found)} comprehensive tests:")
        for text, chars in chinese_found[:3]:
            print(f"    - '{text}' contains: {chars}")
        return False
    else:
        print(f"  ✅ PASS: No Chinese found in {len(test_texts)} comprehensive tests")
        return True

def main():
    """Run comprehensive user segmentation i18n tests."""
    print("🚀 Starting User Segmentation i18n Tests")
    print("="*60)
    
    tests = [
        ("LocalizedInsightGenerator", test_user_segmentation_localized_generator),
        ("Translation Keys", test_user_segmentation_translation_keys),
        ("Segment Names", test_segment_name_translations),
        ("Comprehensive Test", test_comprehensive_user_segmentation)
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
    print("📊 User Segmentation i18n Test Results Summary:")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 SUCCESS! User segmentation module is properly internationalized.")
        print("The user segmentation module now displays 100% English text when language is set to English mode.")
        return True
    else:
        print("\n⚠️  Some user segmentation i18n tests failed. Please check the failures above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)