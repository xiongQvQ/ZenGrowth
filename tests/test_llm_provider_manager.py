#!/usr/bin/env python3
"""
LLM提供商管理系统单元测试
测试提供商选择逻辑、回退机制和配置验证
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

from config.llm_provider_manager import (
    LLMProviderManager,
    ProviderStatus,
    HealthCheckResult,
    ProviderMetrics
)
from config.fallback_handler import (
    FallbackHandler,
    FallbackEvent,
    FallbackReason,
    FallbackStrategy
)
from config.volcano_llm_client import VolcanoLLMClient, VolcanoAPIException, VolcanoErrorType


class TestProviderSelection:
    """测试提供商选择逻辑"""
    
    def test_provider_manager_initialization(self):
        """测试提供商管理器初始化"""
        manager = LLMProviderManager()
        
        assert manager is not None
        assert hasattr(manager, 'providers')
        assert hasattr(manager, 'current_provider')
        assert hasattr(manager, 'fallback_handler')
    
    @patch('config.llm_provider_manager.validate_provider_config')
    def test_add_provider_success(self, mock_validate):
        """测试成功添加提供商"""
        mock_validate.return_value = True
        
        manager = LLMProviderManager()
        
        provider_config = {
            "name": "volcano",
            "type": "volcano",
            "api_key": "test-key",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "doubao-seed-1-6-250615",
            "priority": 1,
            "enabled": True
        }
        
        result = manager.add_provider("volcano", provider_config)
        
        assert result == True
        assert "volcano" in manager.providers
        mock_validate.assert_called_once()
    
    def test_add_provider_invalid_config(self):
        """测试添加无效配置的提供商"""
        manager = LLMProviderManager()
        
        invalid_config = {
            "name": "invalid",
            # 缺少必要字段
        }
        
        with pytest.raises(ValueError, match="Invalid provider configuration"):
            manager.add_provider("invalid", invalid_config)
    
    def test_provider_priority_ordering(self):
        """测试提供商优先级排序"""
        manager = LLMProviderManager()
        
        # 添加多个提供商，不同优先级
        providers = [
            ("volcano", {"priority": 1, "enabled": True}),
            ("google", {"priority": 2, "enabled": True}),
            ("openai", {"priority": 0, "enabled": True})  # 最高优先级
        ]
        
        for name, config in providers:
            with patch('config.llm_provider_manager.validate_provider_config', return_value=True):
                manager.add_provider(name, {
                    "name": name,
                    "type": name,
                    "api_key": "test-key",
                    **config
                })
        
        # 获取按优先级排序的提供商
        sorted_providers = manager.get_providers_by_priority()
        
        assert len(sorted_providers) == 3
        assert sorted_providers[0]["name"] == "openai"  # 优先级0最高
        assert sorted_providers[1]["name"] == "volcano"  # 优先级1
        assert sorted_providers[2]["name"] == "google"   # 优先级2
    
    def test_select_best_provider(self):
        """测试选择最佳提供商"""
        manager = LLMProviderManager()
        
        # 添加提供商并设置健康状态
        with patch('config.llm_provider_manager.validate_provider_config', return_value=True):
            manager.add_provider("volcano", {
                "name": "volcano",
                "type": "volcano",
                "api_key": "test-key",
                "priority": 1,
                "enabled": True
            })
            manager.add_provider("google", {
                "name": "google",
                "type": "google",
                "api_key": "test-key",
                "priority": 2,
                "enabled": True
            })
        
        # 设置健康检查结果
        manager.health_status["volcano"] = HealthCheckResult(
            provider="volcano",
            status=ProviderStatus.AVAILABLE,
            response_time=0.5,
            success_rate=0.95
        )
        manager.health_status["google"] = HealthCheckResult(
            provider="google",
            status=ProviderStatus.DEGRADED,
            response_time=1.2,
            success_rate=0.80
        )
        
        best_provider = manager.select_best_provider()
        
        assert best_provider == "volcano"  # 更高优先级且状态更好
    
    def test_select_provider_all_unavailable(self):
        """测试所有提供商都不可用时的选择"""
        manager = LLMProviderManager()
        
        with patch('config.llm_provider_manager.validate_provider_config', return_value=True):
            manager.add_provider("volcano", {
                "name": "volcano",
                "type": "volcano",
                "api_key": "test-key",
                "priority": 1,
                "enabled": True
            })
        
        # 设置为不可用状态
        manager.health_status["volcano"] = HealthCheckResult(
            provider="volcano",
            status=ProviderStatus.UNAVAILABLE,
            error_message="Service unavailable"
        )
        
        best_provider = manager.select_best_provider()
        
        assert best_provider is None  # 没有可用的提供商


class TestFallbackMechanism:
    """测试回退机制"""
    
    def test_fallback_handler_initialization(self):
        """测试回退处理器初始化"""
        handler = FallbackHandler()
        
        assert handler is not None
        assert hasattr(handler, 'strategy')
        assert hasattr(handler, 'max_retries')
        assert hasattr(handler, 'events')
    
    def test_fallback_on_provider_failure(self):
        """测试提供商失败时的回退"""
        manager = LLMProviderManager()
        
        # 添加多个提供商
        providers = [
            ("volcano", {"priority": 1, "enabled": True}),
            ("google", {"priority": 2, "enabled": True})
        ]
        
        for name, config in providers:
            with patch('config.llm_provider_manager.validate_provider_config', return_value=True):
                manager.add_provider(name, {
                    "name": name,
                    "type": name,
                    "api_key": "test-key",
                    **config
                })
        
        # 设置初始状态
        manager.health_status["volcano"] = HealthCheckResult(
            provider="volcano",
            status=ProviderStatus.AVAILABLE
        )
        manager.health_status["google"] = HealthCheckResult(
            provider="google",
            status=ProviderStatus.AVAILABLE
        )
        
        # 模拟volcano失败
        manager.current_provider = "volcano"
        
        # 触发回退
        fallback_result = manager.handle_provider_failure(
            "volcano",
            VolcanoAPIException("API Error", VolcanoErrorType.API_CONNECTION_ERROR)
        )
        
        assert fallback_result is not None
        assert fallback_result != "volcano"  # 应该切换到其他提供商
        assert manager.current_provider != "volcano"
    
    def test_fallback_strategy_round_robin(self):
        """测试轮询回退策略"""
        handler = FallbackHandler(strategy=FallbackStrategy.ROUND_ROBIN)
        
        providers = ["volcano", "google", "openai"]
        
        # 测试轮询顺序
        first = handler.get_next_provider(providers, current="volcano")
        second = handler.get_next_provider(providers, current=first)
        third = handler.get_next_provider(providers, current=second)
        
        assert first != "volcano"
        assert second != first
        assert third != second
        
        # 应该循环回到开始
        fourth = handler.get_next_provider(providers, current=third)
        assert fourth == "volcano"
    
    def test_fallback_strategy_priority_based(self):
        """测试基于优先级的回退策略"""
        handler = FallbackHandler(strategy=FallbackStrategy.PRIORITY_BASED)
        
        providers_with_priority = [
            {"name": "volcano", "priority": 1},
            {"name": "google", "priority": 2},
            {"name": "openai", "priority": 0}  # 最高优先级
        ]
        
        # 当前提供商失败，应该选择下一个最高优先级
        next_provider = handler.get_next_provider_by_priority(
            providers_with_priority,
            failed_provider="openai"
        )
        
        assert next_provider == "volcano"  # 下一个最高优先级
    
    def test_fallback_event_logging(self):
        """测试回退事件记录"""
        handler = FallbackHandler()
        
        # 记录回退事件
        event = FallbackEvent(
            timestamp=time.time(),
            from_provider="volcano",
            to_provider="google",
            reason=FallbackReason.PROVIDER_ERROR,
            error_details="API connection failed"
        )
        
        handler.log_fallback_event(event)
        
        assert len(handler.events) == 1
        assert handler.events[0].from_provider == "volcano"
        assert handler.events[0].to_provider == "google"
        assert handler.events[0].reason == FallbackReason.PROVIDER_ERROR
    
    def test_fallback_with_max_retries(self):
        """测试最大重试次数限制"""
        handler = FallbackHandler(max_retries=2)
        
        # 模拟连续失败
        providers = ["volcano", "google"]
        
        # 第一次回退
        result1 = handler.attempt_fallback(providers, "volcano", "API Error 1")
        assert result1 is not None
        
        # 第二次回退
        result2 = handler.attempt_fallback(providers, result1, "API Error 2")
        assert result2 is not None
        
        # 第三次回退应该失败（超过最大重试次数）
        result3 = handler.attempt_fallback(providers, result2, "API Error 3")
        assert result3 is None  # 超过最大重试次数
    
    def test_fallback_circuit_breaker(self):
        """测试断路器模式"""
        handler = FallbackHandler(enable_circuit_breaker=True)
        
        provider = "volcano"
        
        # 模拟连续失败触发断路器
        for i in range(5):  # 假设阈值为5次失败
            handler.record_failure(provider, f"Error {i+1}")
        
        # 检查断路器状态
        is_circuit_open = handler.is_circuit_open(provider)
        assert is_circuit_open == True
        
        # 断路器打开时不应该尝试该提供商
        should_try = handler.should_try_provider(provider)
        assert should_try == False


class TestConfigurationValidation:
    """测试配置验证"""
    
    def test_valid_volcano_config(self):
        """测试有效的Volcano配置"""
        from config.settings import validate_provider_config
        
        valid_config = {
            "name": "volcano",
            "type": "volcano",
            "api_key": "test-ark-key",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "doubao-seed-1-6-250615",
            "priority": 1,
            "enabled": True,
            "timeout": 30,
            "max_retries": 3
        }
        
        is_valid = validate_provider_config(valid_config)
        assert is_valid == True
    
    def test_invalid_volcano_config_missing_api_key(self):
        """测试缺少API密钥的无效配置"""
        from config.settings import validate_provider_config
        
        invalid_config = {
            "name": "volcano",
            "type": "volcano",
            # 缺少api_key
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "doubao-seed-1-6-250615"
        }
        
        is_valid = validate_provider_config(invalid_config)
        assert is_valid == False
    
    def test_invalid_volcano_config_wrong_base_url(self):
        """测试错误base_url的无效配置"""
        from config.settings import validate_provider_config
        
        invalid_config = {
            "name": "volcano",
            "type": "volcano",
            "api_key": "test-key",
            "base_url": "invalid-url",  # 无效URL
            "model": "doubao-seed-1-6-250615"
        }
        
        is_valid = validate_provider_config(invalid_config)
        assert is_valid == False
    
    def test_provider_config_with_custom_parameters(self):
        """测试带有自定义参数的提供商配置"""
        from config.settings import validate_provider_config
        
        config_with_custom_params = {
            "name": "volcano",
            "type": "volcano",
            "api_key": "test-key",
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "doubao-seed-1-6-250615",
            "priority": 1,
            "enabled": True,
            "custom_parameters": {
                "temperature": 0.7,
                "max_tokens": 2000,
                "top_p": 0.9
            }
        }
        
        is_valid = validate_provider_config(config_with_custom_params)
        assert is_valid == True
    
    def test_multiple_provider_configs(self):
        """测试多提供商配置验证"""
        manager = LLMProviderManager()
        
        configs = {
            "volcano": {
                "name": "volcano",
                "type": "volcano",
                "api_key": "volcano-key",
                "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                "model": "doubao-seed-1-6-250615",
                "priority": 1,
                "enabled": True
            },
            "google": {
                "name": "google",
                "type": "google",
                "api_key": "google-key",
                "model": "gemini-2.5-pro",
                "priority": 2,
                "enabled": True
            }
        }
        
        with patch('config.llm_provider_manager.validate_provider_config', return_value=True):
            for name, config in configs.items():
                result = manager.add_provider(name, config)
                assert result == True
        
        assert len(manager.providers) == 2
        assert "volcano" in manager.providers
        assert "google" in manager.providers


class TestProviderMetrics:
    """测试提供商指标"""
    
    def test_provider_metrics_initialization(self):
        """测试提供商指标初始化"""
        metrics = ProviderMetrics()
        
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.success_rate == 0.0
        assert metrics.average_response_time == 0.0
    
    def test_record_successful_request(self):
        """测试记录成功请求"""
        metrics = ProviderMetrics()
        
        # 记录成功请求
        metrics.record_success(response_time=0.5)
        
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 0
        assert metrics.success_rate == 1.0
        assert metrics.average_response_time == 0.5
        assert metrics.consecutive_failures == 0
        assert metrics.consecutive_successes == 1
    
    def test_record_failed_request(self):
        """测试记录失败请求"""
        metrics = ProviderMetrics()
        
        # 记录失败请求
        metrics.record_failure("API Error")
        
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 1
        assert metrics.success_rate == 0.0
        assert metrics.last_error == "API Error"
        assert metrics.consecutive_failures == 1
        assert metrics.consecutive_successes == 0
    
    def test_mixed_request_metrics(self):
        """测试混合请求指标"""
        metrics = ProviderMetrics()
        
        # 记录多个请求
        metrics.record_success(0.3)
        metrics.record_success(0.7)
        metrics.record_failure("Timeout")
        metrics.record_success(0.5)
        
        assert metrics.total_requests == 4
        assert metrics.successful_requests == 3
        assert metrics.failed_requests == 1
        assert metrics.success_rate == 0.75
        assert metrics.average_response_time == 0.5  # (0.3 + 0.7 + 0.5) / 3
        assert metrics.consecutive_failures == 0  # 最后一次是成功
        assert metrics.consecutive_successes == 1


class TestHealthChecks:
    """测试健康检查"""
    
    def test_health_check_result_creation(self):
        """测试健康检查结果创建"""
        result = HealthCheckResult(
            provider="volcano",
            status=ProviderStatus.AVAILABLE,
            response_time=0.5,
            success_rate=0.95
        )
        
        assert result.provider == "volcano"
        assert result.status == ProviderStatus.AVAILABLE
        assert result.response_time == 0.5
        assert result.success_rate == 0.95
        assert result.consecutive_failures == 0
    
    @patch('config.llm_provider_manager.time.time')
    def test_health_check_execution(self, mock_time):
        """测试健康检查执行"""
        mock_time.return_value = 1234567890.0
        
        manager = LLMProviderManager()
        
        with patch('config.llm_provider_manager.validate_provider_config', return_value=True):
            manager.add_provider("volcano", {
                "name": "volcano",
                "type": "volcano",
                "api_key": "test-key",
                "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                "model": "doubao-seed-1-6-250615"
            })
        
        # 模拟健康检查
        with patch.object(manager, '_perform_health_check') as mock_check:
            mock_check.return_value = HealthCheckResult(
                provider="volcano",
                status=ProviderStatus.AVAILABLE,
                response_time=0.3,
                last_check=1234567890.0
            )
            
            result = manager.check_provider_health("volcano")
            
            assert result.provider == "volcano"
            assert result.status == ProviderStatus.AVAILABLE
            assert result.response_time == 0.3
            mock_check.assert_called_once_with("volcano")
    
    def test_health_check_failure_detection(self):
        """测试健康检查失败检测"""
        manager = LLMProviderManager()
        
        # 模拟健康检查失败
        failed_result = HealthCheckResult(
            provider="volcano",
            status=ProviderStatus.UNAVAILABLE,
            error_message="Connection timeout",
            consecutive_failures=3
        )
        
        manager.health_status["volcano"] = failed_result
        
        # 检查提供商是否被标记为不健康
        is_healthy = manager.is_provider_healthy("volcano")
        assert is_healthy == False
        
        # 检查是否应该触发回退
        should_fallback = manager.should_trigger_fallback("volcano")
        assert should_fallback == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])