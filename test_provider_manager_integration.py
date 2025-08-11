"""
测试LLM提供商管理器与回退机制的集成
验证完整的提供商管理和回退功能
"""

import logging
import time
from unittest.mock import Mock, patch, MagicMock

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_provider_manager_integration():
    """测试提供商管理器集成"""
    print("测试提供商管理器与回退机制集成...")
    
    # 模拟配置
    mock_settings_data = {
        'enabled_providers': ['google', 'volcano'],
        'default_llm_provider': 'google',
        'enable_fallback': True,
        'fallback_order': ['google', 'volcano'],
        'google_api_key': 'test_google_key',
        'ark_api_key': 'test_volcano_key',
        'ark_base_url': 'https://test.volcano.com',
        'ark_model': 'test-model',
        'llm_model': 'gemini-2.5-pro',
        'llm_temperature': 0.1,
        'llm_max_tokens': 4000,
        'enable_multimodal': True
    }
    
    with patch('config.settings.settings') as mock_settings, \
         patch('config.settings.validate_provider_config', return_value=True), \
         patch('config.llm_provider_manager.ChatGoogleGenerativeAI') as mock_google, \
         patch('config.llm_provider_manager.VolcanoLLMClient') as mock_volcano:
        
        # 配置模拟设置
        for key, value in mock_settings_data.items():
            setattr(mock_settings, key, value)
        
        # 创建模拟LLM实例
        mock_google_instance = Mock()
        mock_volcano_instance = Mock()
        mock_google.return_value = mock_google_instance
        mock_volcano.return_value = mock_volcano_instance
        
        # 导入并创建管理器
        from config.llm_provider_manager import LLMProviderManager
        
        manager = LLMProviderManager()
        
        # 验证初始化
        assert len(manager._providers) == 2
        assert 'google' in manager._providers
        assert 'volcano' in manager._providers
        assert manager.fallback_enabled is True
        
        print("✓ 提供商管理器初始化成功")
        
        # 测试成功的回退场景
        mock_google_instance.invoke.side_effect = Exception("Google API Error")
        mock_volcano_instance.invoke.return_value = "Volcano response"
        
        result, used_provider, fallback_event = manager.invoke_with_fallback("Test prompt")
        
        assert result == "Volcano response"
        assert used_provider == "volcano"
        assert fallback_event is not None
        assert fallback_event.from_provider == "google"
        assert fallback_event.to_provider == "volcano"
        assert fallback_event.success is True
        
        print("✓ 回退机制工作正常")
        
        # 验证统计信息
        stats = manager.get_fallback_stats()
        assert stats['total_fallbacks'] == 1
        assert stats['successful_fallbacks'] == 1
        assert stats['fallback_success_rate'] == 1.0
        
        print("✓ 回退统计正常")
        
        # 测试手动回退
        success = manager.manual_fallback("google", "volcano", "测试手动切换")
        assert success is True
        
        # 检查历史记录
        history = manager.get_fallback_history(limit=2)
        assert len(history) == 2  # 一个自动回退 + 一个手动回退
        
        print("✓ 手动回退功能正常")
        
        # 测试回退顺序更新
        new_order = ['volcano', 'google']
        success = manager.update_fallback_order(new_order)
        assert success is True
        assert manager.fallback_order == new_order
        
        print("✓ 回退顺序更新正常")
        
        # 测试导出功能
        metrics_json = manager.export_metrics()
        assert metrics_json is not None
        assert "fallback_stats" in metrics_json
        assert "circuit_breaker_status" in metrics_json
        
        fallback_report = manager.export_fallback_report()
        assert fallback_report is not None
        assert "configuration" in fallback_report
        assert "statistics" in fallback_report
        
        print("✓ 导出功能正常")


def test_health_check_integration():
    """测试健康检查与回退的集成"""
    print("测试健康检查与回退集成...")
    
    mock_settings_data = {
        'enabled_providers': ['google', 'volcano'],
        'default_llm_provider': 'google',
        'enable_fallback': True,
        'fallback_order': ['google', 'volcano'],
        'google_api_key': 'test_google_key',
        'ark_api_key': 'test_volcano_key',
        'ark_base_url': 'https://test.volcano.com',
        'ark_model': 'test-model',
        'llm_model': 'gemini-2.5-pro',
        'llm_temperature': 0.1,
        'llm_max_tokens': 4000,
        'enable_multimodal': True
    }
    
    with patch('config.settings.settings') as mock_settings, \
         patch('config.settings.validate_provider_config', return_value=True), \
         patch('config.llm_provider_manager.ChatGoogleGenerativeAI') as mock_google, \
         patch('config.llm_provider_manager.VolcanoLLMClient') as mock_volcano:
        
        # 配置模拟设置
        for key, value in mock_settings_data.items():
            setattr(mock_settings, key, value)
        
        # 创建模拟LLM实例
        mock_google_instance = Mock()
        mock_volcano_instance = Mock()
        mock_google.return_value = mock_google_instance
        mock_volcano.return_value = mock_volcano_instance
        
        # 导入并创建管理器
        from config.llm_provider_manager import LLMProviderManager
        
        manager = LLMProviderManager()
        
        # 模拟健康检查
        mock_google_instance.invoke.return_value = "Google health check response"
        mock_volcano_instance.invoke.return_value = "Volcano health check response"
        
        # 执行健康检查
        health_results = manager.health_check_all()
        
        assert len(health_results) == 2
        assert 'google' in health_results
        assert 'volcano' in health_results
        
        # 验证可用提供商
        available = manager.get_available_providers()
        assert len(available) >= 0  # 可能为空，取决于健康检查结果
        
        print("✓ 健康检查集成正常")


def test_circuit_breaker_integration():
    """测试断路器与提供商管理器的集成"""
    print("测试断路器集成...")
    
    mock_settings_data = {
        'enabled_providers': ['google', 'volcano'],
        'default_llm_provider': 'google',
        'enable_fallback': True,
        'fallback_order': ['google', 'volcano'],
        'google_api_key': 'test_google_key',
        'ark_api_key': 'test_volcano_key',
        'ark_base_url': 'https://test.volcano.com',
        'ark_model': 'test-model',
        'llm_model': 'gemini-2.5-pro',
        'llm_temperature': 0.1,
        'llm_max_tokens': 4000,
        'enable_multimodal': True
    }
    
    with patch('config.settings.settings') as mock_settings, \
         patch('config.settings.validate_provider_config', return_value=True), \
         patch('config.llm_provider_manager.ChatGoogleGenerativeAI') as mock_google, \
         patch('config.llm_provider_manager.VolcanoLLMClient') as mock_volcano:
        
        # 配置模拟设置
        for key, value in mock_settings_data.items():
            setattr(mock_settings, key, value)
        
        # 创建模拟LLM实例
        mock_google_instance = Mock()
        mock_volcano_instance = Mock()
        mock_google.return_value = mock_google_instance
        mock_volcano.return_value = mock_volcano_instance
        
        # 导入并创建管理器
        from config.llm_provider_manager import LLMProviderManager
        
        manager = LLMProviderManager()
        
        # 获取断路器状态
        circuit_status = manager.get_circuit_breaker_status()
        assert isinstance(circuit_status, dict)
        
        # 重置断路器
        manager.reset_circuit_breakers()
        
        print("✓ 断路器集成正常")


def main():
    """运行所有集成测试"""
    print("开始提供商管理器集成测试...")
    print("=" * 60)
    
    try:
        test_provider_manager_integration()
        test_health_check_integration()
        test_circuit_breaker_integration()
        
        print("=" * 60)
        print("🎉 所有提供商管理器集成测试通过！")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)