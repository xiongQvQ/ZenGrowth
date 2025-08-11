"""
测试LLM提供商回退机制
验证自动回退、成功/失败跟踪和日志记录功能
"""

import pytest
import time
import logging
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from config.llm_provider_manager import LLMProviderManager, get_provider_manager, reset_provider_manager
from config.fallback_handler import FallbackHandler, FallbackEvent, FallbackReason, get_fallback_handler, reset_fallback_handler
from config.settings import settings

# 设置测试日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestFallbackMechanism:
    """回退机制测试类"""
    
    def setup_method(self):
        """测试前设置"""
        # 重置单例实例
        reset_provider_manager()
        reset_fallback_handler()
        
        # 模拟配置
        self.mock_settings = {
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
    
    def test_fallback_handler_initialization(self):
        """测试回退处理器初始化"""
        handler = FallbackHandler(
            fallback_order=['google', 'volcano'],
            max_retries=2,
            retry_delay=1.0
        )
        
        assert handler.fallback_order == ['google', 'volcano']
        assert handler.max_retries == 2
        assert handler.retry_delay == 1.0
        assert handler._fallback_stats.total_fallbacks == 0
        
        logger.info("✓ 回退处理器初始化测试通过")
    
    def test_fallback_event_creation(self):
        """测试回退事件创建"""
        event = FallbackEvent(
            from_provider="google",
            to_provider="volcano",
            reason=FallbackReason.PROVIDER_UNAVAILABLE,
            success=True,
            response_time=1.5
        )
        
        assert event.from_provider == "google"
        assert event.to_provider == "volcano"
        assert event.reason == FallbackReason.PROVIDER_UNAVAILABLE
        assert event.success is True
        assert event.response_time == 1.5
        
        # 测试转换为字典
        event_dict = event.to_dict()
        assert event_dict['from_provider'] == "google"
        assert event_dict['reason'] == "provider_unavailable"
        
        logger.info("✓ 回退事件创建测试通过")
    
    @patch('config.settings.settings')
    @patch('config.settings.validate_provider_config')
    def test_provider_manager_with_fallback(self, mock_validate, mock_settings):
        """测试提供商管理器的回退功能"""
        # 配置模拟
        for key, value in self.mock_settings.items():
            setattr(mock_settings, key, value)
        
        mock_validate.return_value = True
        
        # 模拟LLM实例
        mock_google_llm = Mock()
        mock_volcano_llm = Mock()
        
        with patch('config.llm_provider_manager.ChatGoogleGenerativeAI', return_value=mock_google_llm), \
             patch('config.llm_provider_manager.VolcanoLLMClient', return_value=mock_volcano_llm):
            
            manager = LLMProviderManager()
            
            # 验证初始化
            assert len(manager._providers) == 2
            assert 'google' in manager._providers
            assert 'volcano' in manager._providers
            assert manager.fallback_enabled is True
            
            logger.info("✓ 提供商管理器回退功能初始化测试通过")
    
    @patch('config.settings.settings')
    @patch('config.settings.validate_provider_config')
    def test_successful_fallback_execution(self, mock_validate, mock_settings):
        """测试成功的回退执行"""
        # 配置模拟
        for key, value in self.mock_settings.items():
            setattr(mock_settings, key, value)
        
        mock_validate.return_value = True
        
        # 模拟LLM实例
        mock_google_llm = Mock()
        mock_volcano_llm = Mock()
        
        # Google失败，Volcano成功
        mock_google_llm.invoke.side_effect = Exception("Google API Error")
        mock_volcano_llm.invoke.return_value = "Volcano response"
        
        with patch('config.llm_provider_manager.ChatGoogleGenerativeAI', return_value=mock_google_llm), \
             patch('config.llm_provider_manager.VolcanoLLMClient', return_value=mock_volcano_llm):
            
            manager = LLMProviderManager()
            
            # 执行带回退的调用
            result, used_provider, fallback_event = manager.invoke_with_fallback("Test prompt")
            
            # 验证结果
            assert result == "Volcano response"
            assert used_provider == "volcano"
            assert fallback_event is not None
            assert fallback_event.from_provider == "google"
            assert fallback_event.to_provider == "volcano"
            assert fallback_event.success is True
            
            # 验证统计信息
            stats = manager.get_fallback_stats()
            assert stats['total_fallbacks'] == 1
            assert stats['successful_fallbacks'] == 1
            assert stats['fallback_success_rate'] == 1.0
            
            logger.info("✓ 成功回退执行测试通过")
    
    @patch('config.settings.settings')
    @patch('config.settings.validate_provider_config')
    def test_failed_fallback_execution(self, mock_validate, mock_settings):
        """测试失败的回退执行"""
        # 配置模拟
        for key, value in self.mock_settings.items():
            setattr(mock_settings, key, value)
        
        mock_validate.return_value = True
        
        # 模拟LLM实例
        mock_google_llm = Mock()
        mock_volcano_llm = Mock()
        
        # 两个提供商都失败
        mock_google_llm.invoke.side_effect = Exception("Google API Error")
        mock_volcano_llm.invoke.side_effect = Exception("Volcano API Error")
        
        with patch('config.llm_provider_manager.ChatGoogleGenerativeAI', return_value=mock_google_llm), \
             patch('config.llm_provider_manager.VolcanoLLMClient', return_value=mock_volcano_llm):
            
            manager = LLMProviderManager()
            
            # 执行带回退的调用，应该抛出异常
            with pytest.raises(Exception) as exc_info:
                manager.invoke_with_fallback("Test prompt")
            
            assert "所有提供商都不可用" in str(exc_info.value)
            
            logger.info("✓ 失败回退执行测试通过")
    
    def test_circuit_breaker_functionality(self):
        """测试断路器功能"""
        handler = FallbackHandler()
        
        # 模拟连续失败
        for i in range(6):  # 超过阈值
            handler._update_circuit_breaker("test_provider", False)
        
        # 检查断路器是否开启
        assert handler._is_circuit_breaker_open("test_provider") is True
        
        # 重置断路器
        handler._reset_circuit_breaker("test_provider")
        assert handler._is_circuit_breaker_open("test_provider") is False
        
        logger.info("✓ 断路器功能测试通过")
    
    def test_fallback_reason_determination(self):
        """测试回退原因判断"""
        handler = FallbackHandler()
        
        # 测试不同类型的错误
        timeout_error = Exception("Request timeout occurred")
        rate_limit_error = Exception("Rate limit exceeded (429)")
        auth_error = Exception("Authentication failed (401)")
        quota_error = Exception("Quota exceeded (403)")
        
        assert handler._determine_fallback_reason(timeout_error) == FallbackReason.TIMEOUT
        assert handler._determine_fallback_reason(rate_limit_error) == FallbackReason.RATE_LIMIT
        assert handler._determine_fallback_reason(auth_error) == FallbackReason.AUTHENTICATION_ERROR
        assert handler._determine_fallback_reason(quota_error) == FallbackReason.QUOTA_EXCEEDED
        
        logger.info("✓ 回退原因判断测试通过")
    
    @patch('config.settings.settings')
    @patch('config.settings.validate_provider_config')
    def test_manual_fallback(self, mock_validate, mock_settings):
        """测试手动回退"""
        # 配置模拟
        for key, value in self.mock_settings.items():
            setattr(mock_settings, key, value)
        
        mock_validate.return_value = True
        
        with patch('config.llm_provider_manager.ChatGoogleGenerativeAI'), \
             patch('config.llm_provider_manager.VolcanoLLMClient'):
            
            manager = LLMProviderManager()
            
            # 执行手动回退
            success = manager.manual_fallback("google", "volcano", "测试手动切换")
            assert success is True
            
            # 检查回退历史
            history = manager.get_fallback_history(limit=1)
            assert len(history) == 1
            assert history[0]['from_provider'] == "google"
            assert history[0]['to_provider'] == "volcano"
            assert history[0]['reason'] == "manual_switch"
            
            logger.info("✓ 手动回退测试通过")
    
    @patch('config.settings.settings')
    @patch('config.settings.validate_provider_config')
    def test_fallback_order_update(self, mock_validate, mock_settings):
        """测试回退顺序更新"""
        # 配置模拟
        for key, value in self.mock_settings.items():
            setattr(mock_settings, key, value)
        
        mock_validate.return_value = True
        
        with patch('config.llm_provider_manager.ChatGoogleGenerativeAI'), \
             patch('config.llm_provider_manager.VolcanoLLMClient'):
            
            manager = LLMProviderManager()
            
            # 更新回退顺序
            new_order = ['volcano', 'google']
            success = manager.update_fallback_order(new_order)
            assert success is True
            assert manager.fallback_order == new_order
            
            logger.info("✓ 回退顺序更新测试通过")
    
    def test_fallback_stats_tracking(self):
        """测试回退统计跟踪"""
        handler = FallbackHandler()
        
        # 创建测试事件
        success_event = FallbackEvent(
            from_provider="google",
            to_provider="volcano",
            reason=FallbackReason.PROVIDER_UNAVAILABLE,
            success=True,
            response_time=1.5
        )
        
        failure_event = FallbackEvent(
            from_provider="volcano",
            to_provider="google",
            reason=FallbackReason.TIMEOUT,
            success=False,
            response_time=2.0
        )
        
        # 记录事件
        handler._record_fallback_event(success_event)
        handler._record_fallback_event(failure_event)
        
        # 检查统计信息
        stats = handler.get_fallback_stats()
        assert stats.total_fallbacks == 2
        assert stats.successful_fallbacks == 1
        assert stats.failed_fallbacks == 1
        assert stats.fallback_success_rate == 0.5
        
        # 检查按原因统计
        assert stats.fallback_by_reason['provider_unavailable'] == 1
        assert stats.fallback_by_reason['timeout'] == 1
        
        logger.info("✓ 回退统计跟踪测试通过")
    
    @patch('config.settings.settings')
    @patch('config.settings.validate_provider_config')
    def test_export_fallback_report(self, mock_validate, mock_settings):
        """测试导出回退报告"""
        # 配置模拟
        for key, value in self.mock_settings.items():
            setattr(mock_settings, key, value)
        
        mock_validate.return_value = True
        
        with patch('config.llm_provider_manager.ChatGoogleGenerativeAI'), \
             patch('config.llm_provider_manager.VolcanoLLMClient'):
            
            manager = LLMProviderManager()
            
            # 执行手动回退以生成数据
            manager.manual_fallback("google", "volcano", "测试报告")
            
            # 导出报告
            report_json = manager.export_fallback_report()
            assert report_json is not None
            assert "configuration" in report_json
            assert "statistics" in report_json
            assert "circuit_breaker_status" in report_json
            
            logger.info("✓ 导出回退报告测试通过")


def test_integration_with_existing_system():
    """测试与现有系统的集成"""
    # 测试单例模式
    manager1 = get_provider_manager()
    manager2 = get_provider_manager()
    assert manager1 is manager2
    
    # 测试回退处理器集成
    handler1 = get_fallback_handler()
    handler2 = get_fallback_handler()
    assert handler1 is handler2
    
    logger.info("✓ 系统集成测试通过")


if __name__ == "__main__":
    # 运行测试
    test_suite = TestFallbackMechanism()
    
    try:
        test_suite.setup_method()
        test_suite.test_fallback_handler_initialization()
        test_suite.test_fallback_event_creation()
        test_suite.test_circuit_breaker_functionality()
        test_suite.test_fallback_reason_determination()
        test_suite.test_fallback_stats_tracking()
        
        test_integration_with_existing_system()
        
        print("\n" + "="*50)
        print("🎉 所有回退机制测试通过！")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()