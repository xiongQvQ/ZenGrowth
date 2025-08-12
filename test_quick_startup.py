#!/usr/bin/env python3
"""
快速启动测试（带超时）
"""

import signal
import sys
from config.crew_config import get_llm

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("操作超时")

def test_quick_startup():
    print("🚀 快速启动测试...")
    
    try:
        # 设置30秒超时
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)
        
        print("1. 测试 LLM 获取...")
        llm = get_llm()
        print(f"  ✅ 获取到 LLM: {type(llm).__name__}")
        
        print("2. 跳过健康检查，直接测试调用...")
        response = llm.invoke("Hi")
        print(f"  ✅ 调用成功，响应长度: {len(response)}")
        
        # 取消超时
        signal.alarm(0)
        
        print("🎉 快速测试成功！可以启动应用")
        return True
        
    except TimeoutError:
        print("⏰ 操作超时，但这可能是正常的")
        print("💡 建议直接启动 Streamlit 应用试试")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        signal.alarm(0)

if __name__ == "__main__":
    test_quick_startup()