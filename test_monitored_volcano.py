#!/usr/bin/env python3
"""
测试监控版本的 Volcano 客户端
"""

import logging
from config.volcano_llm_client_monitored import MonitoredVolcanoLLMClient
from config.settings import settings

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_monitored_volcano():
    """测试监控版本的 Volcano 客户端"""
    try:
        # 创建监控版本客户端
        client = MonitoredVolcanoLLMClient(
            api_key=settings.ark_api_key,
            base_url=settings.ark_base_url,
            model=settings.ark_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )
        
        print("监控版本客户端创建成功")
        
        test_prompt = "Hello, this is a health check."
        print(f"测试提示: {test_prompt}")
        
        # 调用 API
        response = client._call(test_prompt)
        
        print(f"响应类型: {type(response)}")
        print(f"响应内容: '{response}'")
        print(f"响应长度: {len(response) if response else 0}")
        
        if response:
            print("✅ 监控版本 Volcano API 调用成功")
        else:
            print("❌ 监控版本 Volcano API 返回空响应")
        
    except Exception as e:
        print(f"❌ 监控版本 Volcano API 调用失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_monitored_volcano()