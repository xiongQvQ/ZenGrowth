#!/usr/bin/env python3
"""
快速修复脚本
"""

from config.llm_provider_manager import get_provider_manager, reset_provider_manager

def quick_fix():
    print("快速修复提供商...")
    reset_provider_manager()
    manager = get_provider_manager()
    results = manager.force_health_check()
    
    for provider, result in results.items():
        status = result.status if isinstance(result.status, str) else result.status.value
        print(f"{provider}: {status}")
    
    print("修复完成")

if __name__ == "__main__":
    quick_fix()