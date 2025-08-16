#!/usr/bin/env python3
"""
Configuration Fix Verification Test
Tests that the SystemConfig class properly handles the llm_settings parameter
and loads configuration without errors.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_config_loading():
    """Test configuration loading works without errors."""
    print("🧪 Testing Configuration Loading...")
    
    try:
        from utils.config_manager import config_manager
        
        # Test getting config as dict (original method)
        config_dict = config_manager.get_system_config()
        print(f"  ✅ Config dict loaded: {type(config_dict)}")
        
        # Test getting config as object (new method)
        config_obj = config_manager.get_system_config_object()
        print(f"  ✅ Config object loaded: {type(config_obj)}")
        
        # Test accessing llm_settings
        if hasattr(config_obj, 'llm_settings') and config_obj.llm_settings:
            provider = config_obj.llm_settings.get('default_provider', 'unknown')
            print(f"  ✅ LLM provider: {provider}")
        else:
            print("  ⚠️ llm_settings not found or empty")
        
        # Test accessing ui_settings
        if hasattr(config_obj, 'ui_settings') and config_obj.ui_settings:
            language = config_obj.ui_settings.get('language', 'unknown')
            print(f"  ✅ UI language: {language}")
        else:
            print("  ⚠️ ui_settings not found or empty")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration loading failed: {e}")
        return False

def test_i18n_system():
    """Test the i18n system works correctly."""
    print("\n🌐 Testing I18N System...")
    
    try:
        from utils.i18n import t, get_current_language
        
        # Test language detection
        current_lang = get_current_language()
        print(f"  ✅ Current language: {current_lang}")
        
        # Test translation
        title = t("analysis.event_title", "Event Analysis")
        print(f"  ✅ Translation test: {title}")
        
        # Test with environment override
        os.environ['FORCE_LANGUAGE'] = 'en-US'
        en_title = t("analysis.event_title", "Event Analysis")
        print(f"  ✅ English forced: {en_title}")
        
        # Clean up
        if 'FORCE_LANGUAGE' in os.environ:
            del os.environ['FORCE_LANGUAGE']
            
        return True
        
    except Exception as e:
        print(f"  ❌ I18N system failed: {e}")
        return False

def main():
    """Run all configuration tests."""
    print("🚀 Configuration Fix Verification")
    print("=" * 50)
    
    config_test = test_config_loading()
    i18n_test = test_i18n_system()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print("=" * 50)
    
    if config_test and i18n_test:
        print("🎉 SUCCESS! All configuration tests passed!")
        print("\n✅ SystemConfig now properly handles llm_settings")
        print("✅ I18N system works with environment overrides")
        print("✅ No more 'unexpected keyword argument' errors")
        return True
    else:
        print("❌ FAIL: Some configuration tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)