#!/usr/bin/env python3
"""
简单的LLM测试
"""

from config.crew_config import get_llm

def test_llm():
    try:
        print("获取LLM...")
        llm = get_llm()
        print(f"LLM类型: {type(llm).__name__}")
        
        print("测试调用...")
        response = llm.invoke("Hello")
        print(f"响应长度: {len(response)}")
        print("✅ 测试成功")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_llm()