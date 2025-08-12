#!/usr/bin/env python3
"""
测试 invoke 方法
"""

import logging
from config.volcano_llm_client_monitored import MonitoredVolcanoLLMClient
from config.settings import settings

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_invoke_method():
    """测试 invoke 方法"""
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
        
        # 测试 _call 方法
        print("\n=== 测试 _call 方法 ===")
        response1 = client._call(test_prompt)
        print(f"_call 响应类型: {type(response1)}")
        print(f"_call 响应内容: '{response1}'")
        print(f"_call 响应长度: {len(response1) if response1 else 0}")
        
        # 测试 invoke 方法
        print("\n=== 测试 invoke 方法 ===")
        response2 = client.invoke(test_prompt)
        print(f"invoke 响应类型: {type(response2)}")
        print(f"invoke 响应内容: '{response2}'")
        print(f"invoke 响应长度: {len(str(response2).strip()) if response2 else 0}")
        
        # 检查健康检查逻辑
        print("\n=== 健康检查逻辑测试 ===")
        is_valid = response2 and len(str(response2).strip()) > 0
        print(f"健康检查有效性: {is_valid}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_invoke_method()