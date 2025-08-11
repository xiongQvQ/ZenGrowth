#!/usr/bin/env python3
"""
Test script to verify that the retention heatmap error is fixed
"""

import pandas as pd
from system.integration_manager import IntegrationManager

def test_retention_analysis_fix():
    """Test that retention analysis visualization works correctly"""
    
    print("Testing retention analysis visualization fix...")
    
    # Create test retention data
    retention_data = pd.DataFrame({
        'cohort_group': ['2024-01', '2024-01', '2024-02', '2024-02', '2024-03', '2024-03'],
        'period_number': [1, 2, 1, 2, 1, 2], 
        'retention_rate': [1.0, 0.8, 1.0, 0.75, 1.0, 0.85]
    })
    
    try:
        # Initialize integration manager
        manager = IntegrationManager()
        
        # Test the retention heatmap creation directly
        print("Creating retention heatmap...")
        heatmap = manager.advanced_visualizer.create_retention_heatmap(retention_data)
        
        if heatmap is not None:
            print("✅ SUCCESS: Retention heatmap created successfully!")
            print(f"   Chart type: {type(heatmap)}")
            print(f"   Has data: {len(heatmap.data) > 0}")
            return True
        else:
            print("❌ FAILED: Heatmap is None")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_all_visualization_methods():
    """Test all visualization methods to ensure they work"""
    
    print("\nTesting all visualization methods...")
    
    try:
        manager = IntegrationManager()
        
        # Test data for different visualizations
        test_cases = [
            {
                'name': 'Retention Heatmap',
                'method': manager.advanced_visualizer.create_retention_heatmap,
                'data': pd.DataFrame({
                    'cohort_group': ['2024-01', '2024-02'],
                    'period_number': [1, 1], 
                    'retention_rate': [1.0, 0.9]
                })
            },
            {
                'name': 'User Segmentation Scatter',
                'method': manager.advanced_visualizer.create_user_segmentation_scatter,
                'data': pd.DataFrame({
                    'user_id': ['user1', 'user2'],
                    'segment': ['high', 'low'],
                    'x_feature': [10, 5],
                    'y_feature': [8, 3]
                })
            },
            {
                'name': 'User Behavior Flow',
                'method': manager.advanced_visualizer.create_user_behavior_flow,
                'data': pd.DataFrame({
                    'source': ['home', 'product'],
                    'target': ['product', 'cart'],
                    'value': [100, 80]
                })
            }
        ]
        
        success_count = 0
        for test_case in test_cases:
            try:
                result = test_case['method'](test_case['data'])
                if result is not None:
                    print(f"✅ {test_case['name']}: SUCCESS")
                    success_count += 1
                else:
                    print(f"❌ {test_case['name']}: FAILED (None result)")
            except Exception as e:
                print(f"❌ {test_case['name']}: FAILED ({e})")
        
        print(f"\nResults: {success_count}/{len(test_cases)} tests passed")
        return success_count == len(test_cases)
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Testing retention analysis visualization fixes...")
    print("=" * 60)
    
    # Test the specific retention issue
    retention_success = test_retention_analysis_fix()
    
    # Test other visualization methods
    all_success = test_all_visualization_methods()
    
    print("\n" + "=" * 60)
    if retention_success and all_success:
        print("🎉 ALL TESTS PASSED! The visualization errors have been fixed.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")