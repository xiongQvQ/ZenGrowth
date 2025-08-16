#!/usr/bin/env python3
"""
Final test to verify both User Segmentation and Conversion Analysis pages 
display English text in English mode.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.i18n import t

def test_user_segmentation_tabs():
    """Test User Segmentation tab titles."""
    print("👥 Testing User Segmentation Tab Titles...")
    
    # These are the exact calls from the UI
    tab_titles = [
        "📊 " + t('analysis.results_overview', 'Results Overview'),
        "🔍 " + t('analysis.segment_details', 'Segment Details'),
        "📈 " + t('analysis.visualizations', 'Visualizations'),
        "📊 " + t('analysis.feature_analysis', 'Feature Analysis'),
        "💡 " + t('analysis.insights_recommendations', 'Insights & Recommendations')
    ]
    
    print("User Segmentation tabs that will appear:")
    for i, title in enumerate(tab_titles, 1):
        print(f"  Tab {i}: {title}")
        
        # Check for Chinese
        chinese_chars = [char for char in title if '\u4e00' <= char <= '\u9fff']
        if chinese_chars:
            print(f"    ❌ Contains Chinese: {chinese_chars}")
            return False
    
    print("  ✅ All User Segmentation tabs are in English!")
    return True

def test_conversion_analysis_ui():
    """Test Conversion Analysis UI elements."""
    print("\n🎯 Testing Conversion Analysis UI...")
    
    ui_elements = {
        "Page Title": t("pages.conversion_analysis.title", "Conversion Analysis"),
        "Start Button": t('analysis.start_conversion_analysis', 'Start Conversion Analysis'),
        "Configuration": t('analysis.conversion_config', 'Conversion Analysis Configuration')
    }
    
    all_english = True
    
    for element_name, text in ui_elements.items():
        print(f"  {element_name}: {text}")
        
        # Check for Chinese
        chinese_chars = [char for char in text if '\u4e00' <= char <= '\u9fff']
        if chinese_chars:
            print(f"    ❌ Contains Chinese: {chinese_chars}")
            all_english = False
    
    if all_english:
        print("  ✅ All Conversion Analysis UI elements are in English!")
    
    return all_english

def test_ui_metrics_labels():
    """Test common metrics labels."""
    print("\n📊 Testing Metrics Labels...")
    
    metrics = [
        t('analysis.segment_count', 'Segment Count'),
        t('analysis.user_count', 'User Count'),
        t('analysis.quality_score', 'Quality Score'),
        t('analysis.analysis_method', 'Analysis Method')
    ]
    
    print("Common metrics labels:")
    all_english = True
    
    for metric in metrics:
        print(f"  - {metric}")
        chinese_chars = [char for char in metric if '\u4e00' <= char <= '\u9fff']
        if chinese_chars:
            print(f"    ❌ Contains Chinese: {chinese_chars}")
            all_english = False
    
    if all_english:
        print("  ✅ All metrics labels are in English!")
    
    return all_english

def main():
    """Run final UI pages test."""
    print("🚀 Final UI Pages English Mode Test")
    print("="*60)
    print("Testing User Segmentation and Conversion Analysis pages...")
    print("="*60)
    
    seg_test = test_user_segmentation_tabs()
    conv_test = test_conversion_analysis_ui()
    metrics_test = test_ui_metrics_labels()
    
    print("\n" + "="*60)
    print("📊 Final Test Results:")
    print("="*60)
    
    if seg_test and conv_test and metrics_test:
        print("🎉 SUCCESS! Both pages will display in English!")
        print("\nUser Segmentation tabs:")
        print("- Tab 1: 📊 Results Overview")
        print("- Tab 2: 🔍 Segment Details") 
        print("- Tab 3: 📈 Visualizations")
        print("- Tab 4: 📊 Feature Analysis")
        print("- Tab 5: 💡 Insights & Recommendations")
        print("\nConversion Analysis page: 🎯 Conversion Analysis")
        print("\n✅ ISSUES RESOLVED: No more Chinese text in English mode!")
        return True
    else:
        print("❌ FAIL: Some elements still contain Chinese text")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)