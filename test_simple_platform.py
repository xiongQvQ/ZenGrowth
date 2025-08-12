#!/usr/bin/env python3
"""
简化的平台测试
"""

from config.crew_config import get_llm

def test_simple():
    """简单测试"""
    try:
        print("测试 LLM 提供商...")
        
        # 获取 LLM
        llm = get_llm(provider="volcano")
        print(f"LLM 类型: {type(llm).__name__}")
        
        # 简单测试
        response = llm.invoke("什么是用户行为分析？请简短回答。")
        print(f"响应长度: {len(response)}")
        print(f"响应: {response[:200]}...")
        
        print("✅ 测试成功")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_simple()