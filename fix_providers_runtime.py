#!/usr/bin/env python3
"""
运行时提供商修复脚本
用于在应用运行时快速修复提供商问题
"""

import logging
from config.llm_provider_manager import get_provider_manager, reset_provider_manager
from config.crew_config import get_llm

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_providers():
    """修复提供商问题"""
    print("🔧 修复提供商状态...")
    
    try:
        # 1. 重置提供商管理器
        print("1. 重置提供商管理器...")
        reset_provider_manager()
        
        # 2. 获取新的管理器实例
        print("2. 获取新的管理器实例...")
        manager = get_provider_manager()
        
        # 3. 强制健康检查
        print("3. 执行健康检查...")
        health_results = manager.force_health_check()
        
        # 4. 显示结果
        print("4. 健康检查结果:")
        available_count = 0
        for provider, result in health_results.items():
            status = result.status if isinstance(result.status, str) else result.status.value
            if status in ["available", "degraded"]:
                available_count += 1
                print(f"  ✅ {provider}: {status}")
            else:
                print(f"  ❌ {provider}: {status}")
        
        # 5. 测试默认提供商
        if available_count > 0:
            print("5. 测试默认提供商...")
            try:
                llm = get_llm()
                response = llm.invoke("Test")
                print(f"  ✅ 测试成功，响应长度: {len(response)}")
                print("🎉 提供商修复完成！")
                return True
            except Exception as e:
                print(f"  ⚠️ 测试失败: {e}")
                return False
        else:
            print("❌ 没有可用的提供商")
            return False
            
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

if __name__ == "__main__":
    fix_providers()