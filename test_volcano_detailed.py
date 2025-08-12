#!/usr/bin/env python3
"""
详细测试 Volcano API 调用
"""

import logging
from config.volcano_llm_client import VolcanoLLMClient
from config.settings import settings

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_volcano_detailed():
    """详细测试 Volcano API"""
    try:
        # 创建基础客户端（不带监控）
        client = VolcanoLLMClient(
            api_key=settings.ark_api_key,
            base_url=settings.ark_base_url,
            model=settings.ark_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        
        print(f"客户端配置:")
        print(f"  API Key: {settings.ark_api_key[:10]}...")
        print(f"  Base URL: {settings.ark_base_url}")
        print(f"  Model: {settings.ark_model}")
        print(f"  Temperature: {settings.llm_temperature}")
        print(f"  Max Tokens: {settings.llm_max_tokens}")
        print()
        
        test_prompt = "Hello, this is a health check."
        print(f"测试提示: {test_prompt}")
        
        # 调用 API
        response = client._call(test_prompt)
        
        print(f"响应类型: {type(response)}")
        print(f"响应内容: '{response}'")
        print(f"响应长度: {len(response) if response else 0}")
        
        if response:
            print("✅ Volcano API 调用成功")
        else:
            print("❌ Volcano API 返回空响应")
        
    except Exception as e:
        print(f"❌ Volcano API 调用失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_volcano_detailed()