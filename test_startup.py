#!/usr/bin/env python3
"""
测试启动流程
"""

from config.llm_provider_manager import get_provider_manager
from config.crew_config import get_llm

def test_startup():
    print("🔧 测试启动流程...")
    
    try:
        # 1. 测试提供商管理器
        print("1. 初始化提供商管理器...")
        manager = get_provider_manager()
        
        # 2. 执行健康检查
        print("2. 执行健康检查...")
        health_results = manager.force_health_check()
        
        healthy_count = 0
        for provider, result in health_results.items():
            status = result.status if isinstance(result.status, str) else result.status.value
            if status in ["available", "degraded"]:
                healthy_count += 1
                print(f"  ✅ {provider}: {status}")
            else:
                print(f"  ❌ {provider}: {status}")
        
        if healthy_count == 0:
            print("❌ 没有可用的提供商")
            return False
        
        # 3. 测试 LLM 获取
        print("3. 测试 LLM 获取...")
        llm = get_llm()
        print(f"  ✅ 获取到 LLM: {type(llm).__name__}")
        
        # 4. 测试 LLM 调用
        print("4. 测试 LLM 调用...")
        response = llm.invoke("Test")
        print(f"  ✅ 调用成功，响应长度: {len(response)}")
        
        print("🎉 启动流程测试成功！")
        print("现在可以安全启动 Streamlit 应用")
        return True
        
    except Exception as e:
        print(f"❌ 启动流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_startup()