#!/usr/bin/env python3
"""
修复提供商健康状态的脚本
"""

import logging
from config.llm_provider_manager import get_provider_manager, reset_provider_manager
from config.crew_config import get_llm

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_provider_health():
    """修复提供商健康状态"""
    try:
        print("=== 修复提供商健康状态 ===")
        
        # 重置提供商管理器
        print("1. 重置提供商管理器...")
        reset_provider_manager()
        
        # 获取新的管理器实例
        print("2. 获取新的管理器实例...")
        manager = get_provider_manager()
        
        # 强制执行健康检查
        print("3. 强制执行健康检查...")
        health_results = manager.force_health_check()
        
        print("4. 健康检查结果:")
        for provider, result in health_results.items():
            status = result.status if isinstance(result.status, str) else result.status.value
            print(f"  {provider}: {status}")
            if result.error_message:
                print(f"    错误: {result.error_message}")
        
        # 测试获取可用提供商
        print("5. 测试可用提供商:")
        available = manager.get_available_providers()
        print(f"  可用提供商: {available}")
        
        # 测试 LLM 获取
        print("6. 测试 LLM 获取:")
        try:
            llm = get_llm(provider="volcano")
            print(f"  Volcano LLM: {type(llm).__name__}")
            
            # 简单测试
            response = llm.invoke("Hello")
            print(f"  测试响应长度: {len(response)}")
            print("  ✅ Volcano LLM 工作正常")
            
        except Exception as e:
            print(f"  ❌ Volcano LLM 测试失败: {e}")
        
        print("\n=== 修复完成 ===")
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fix_provider_health()