#!/usr/bin/env python3
"""
Test script for Volcano Integration Demo
Validates demo functionality and provides quick testing capabilities
"""

import os
import sys
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_demo_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing demo imports...")
    
    try:
        from demo_volcano_integration import VolcanoIntegrationDemo, PerformanceMetrics, DemoResult
        print("✅ Demo classes imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_demo_initialization():
    """Test demo initialization without API calls"""
    print("🔍 Testing demo initialization...")
    
    try:
        # Mock the dependencies to avoid API calls
        with patch('demo_volcano_integration.LLMProviderManager') as mock_manager, \
             patch('demo_volcano_integration.MultiModalContentHandler') as mock_handler, \
             patch('demo_volcano_integration.setup_logger') as mock_logger:
            
            # Configure mocks
            mock_manager.return_value.get_available_providers.return_value = ["google", "volcano"]
            mock_handler.return_value = Mock()
            mock_logger.return_value = Mock()
            
            from demo_volcano_integration import VolcanoIntegrationDemo
            
            demo = VolcanoIntegrationDemo()
            
            print("✅ Demo initialized successfully")
            print(f"   Sample images: {len(demo.sample_images)} configured")
            print(f"   Results list: {len(demo.results)} items")
            print(f"   Performance data: {len(demo.performance_data)} providers")
            
            return True
            
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

def run_quick_demo_test():
    """Run a quick demo test with mocked dependencies"""
    print("🔍 Running quick demo test...")
    
    try:
        with patch('demo_volcano_integration.LLMProviderManager') as mock_manager, \
             patch('demo_volcano_integration.MultiModalContentHandler') as mock_handler, \
             patch('demo_volcano_integration.setup_logger') as mock_logger:
            
            # Configure mocks
            mock_llm = Mock()
            mock_llm.invoke.return_value = "Mock response for testing"
            mock_llm.supports_multimodal.return_value = True
            
            mock_manager.return_value.get_llm.return_value = mock_llm
            mock_manager.return_value.get_available_providers.return_value = ["google", "volcano"]
            
            mock_handler.return_value.prepare_content.return_value = [{"type": "text", "text": "test"}]
            mock_handler.return_value.create_multimodal_request.return_value = Mock(content=[])
            mock_handler.return_value.extract_text_content.return_value = "test text"
            
            from demo_volcano_integration import VolcanoIntegrationDemo
            
            demo = VolcanoIntegrationDemo()
            
            # Test individual demo methods
            connection_result = demo._demo_provider_connections()
            assert connection_result.success, "Connection test should succeed with mocks"
            
            text_result = demo._demo_text_analysis_comparison()
            assert text_result.success, "Text analysis should succeed with mocks"
            
            print("✅ Quick demo test passed")
            return True
            
    except Exception as e:
        print(f"❌ Quick demo test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Volcano Integration Demo Test Suite")
    print("="*50)
    
    tests = [
        ("Import Test", test_demo_imports),
        ("Initialization Test", test_demo_initialization),
        ("Quick Demo Test", run_quick_demo_test)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Demo is ready to run.")
        print("\nTo run the full demo:")
        print("  python demo_volcano_integration.py")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    print("="*50)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)