#!/usr/bin/env python3
"""
详细测试 invoke 方法
"""

import logging
from config.volcano_llm_client_monitored import MonitoredVolcanoLLMClient
from config.settings import settings
from langchain_core.messages import HumanMessage

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_invoke_detailed():
    """详细测试 invoke 方法"""
    try:
        # 创建监控版本客户端
        client = MonitoredVolcanoLLMClient(
            api_key=settings.ark_api_key,
            base_url=settings.ark_base_url,
            model=settings.ark_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        
        print("客户端创建成功")
        
        test_prompt = "Hello, this is a health check."
        print(f"测试提示: {test_prompt}")
        
        # 测试不同的 invoke 方式
        print("\n=== 测试字符串 invoke ===")
        try:
            response1 = client.invoke(test_prompt)
            print(f"字符串 invoke 响应类型: {type(response1)}")
            print(f"字符串 invoke 响应: '{response1}'")
            print(f"字符串 invoke 长度: {len(str(response1).strip()) if response1 else 0}")
        except Exception as e:
            print(f"字符串 invoke 失败: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n=== 测试消息 invoke ===")
        try:
            message = HumanMessage(content=test_prompt)
            response2 = client.invoke([message])
            print(f"消息 invoke 响应类型: {type(response2)}")
            print(f"消息 invoke 响应: '{response2}'")
            print(f"消息 invoke 长度: {len(str(response2).strip()) if response2 else 0}")
        except Exception as e:
            print(f"消息 invoke 失败: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n=== 测试 predict 方法 ===")
        try:
            response3 = client.predict(test_prompt)
            print(f"predict 响应类型: {type(response3)}")
            print(f"predict 响应: '{response3}'")
            print(f"predict 长度: {len(str(response3).strip()) if response3 else 0}")
        except Exception as e:
            print(f"predict 失败: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_invoke_detailed()