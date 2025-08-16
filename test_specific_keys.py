#!/usr/bin/env python3
"""
测试特定翻译键
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_specific_keys():
    """测试特定翻译键"""
    from utils.config_manager import config_manager
    from utils.i18n import i18n, t
    
    # 设置英文模式
    config_manager.update_system_config('ui_settings', {'language': 'en-US'})
    i18n._update_current_language()
    
    print("Testing specific keys in English mode:")
    print(f"Current language: {i18n.get_current_language()}")
    
    test_keys = [
        'analysis.conversion_complete',
        'analysis.conversion_processing', 
        'analysis.no_custom_steps',
        'analysis.path_complete',
        'analysis.path_processing',
        'analysis.session_reconstruction'
    ]
    
    for key in test_keys:
        result = t(key, 'MISSING')
        print(f"   {key}: {result}")
    
    # 查看英文翻译是否加载
    print(f"\nAvailable translations keys for analysis section:")
    analysis_section = i18n.translations['en-US'].get('analysis', {})
    conversion_keys = [k for k in analysis_section.keys() if 'conversion' in k or 'path' in k or 'session' in k]
    print(f"   Found keys: {conversion_keys}")

if __name__ == "__main__":
    test_specific_keys()