"""
简单的回退机制测试
验证基本功能而不依赖pytest
"""

import logging
import time
from unittest.mock import Mock, patch

from config.fallback_handler import FallbackHandler, FallbackEvent, FallbackReason

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_fallback_handler_basic():
    """测试回退处理器基本功能"""
    print("测试回退处理器基本功能...")
    
    handler = FallbackHandler(
        fallback_order=['google', 'volcano'],
        max_retries=2,
        retry_delay=0.1  # 减少延迟以加快测试
    )
    
    assert handler.fallback_order == ['google', 'volcano']
    assert handler.max_retries == 2
    assert handler._fallback_stats.total_fallbacks == 0
    
    print("✓ 回退处理器初始化正常")


def test_fallback_event():
    """测试回退事件"""
    print("测试回退事件...")
    
    event = FallbackEvent(
        from_provider="google",
        to_provider="volcano",
        reason=FallbackReason.PROVIDER_UNAVAILABLE,
        success=True,
        response_time=1.5
    )
    
    assert event.from_provider == "google"
    assert event.to_provider == "volcano"
    assert event.success is True
    
    # 测试转换为字典
    event_dict = event.to_dict()
    assert event_dict['from_provider'] == "google"
    assert event_dict['reason'] == "provider_unavailable"
    
    print("✓ 回退事件功能正常")


def test_circuit_breaker():
    """测试断路器功能"""
    print("测试断路器功能...")
    
    handler = FallbackHandler()
    
    # 模拟连续失败
    for i in range(6):  # 超过默认阈值5
        handler._update_circuit_breaker("test_provider", False)
    
    # 检查断路器是否开启
    assert handler._is_circuit_breaker_open("test_provider") is True
    print("✓ 断路器开启正常")
    
    # 重置断路器
    handler._reset_circuit_breaker("test_provider")
    assert handler._is_circuit_breaker_open("test_provider") is False
    print("✓ 断路器重置正常")


def test_fallback_reason_determination():
    """测试回退原因判断"""
    print("测试回退原因判断...")
    
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
    
    print("✓ 回退原因判断正常")


def test_fallback_execution():
    """测试回退执行"""
    print("测试回退执行...")
    
    handler = FallbackHandler(
        fallback_order=['provider1', 'provider2'],
        max_retries=1,
        retry_delay=0.1
    )
    
    # 模拟请求函数
    call_count = {'count': 0}
    
    def mock_request_func(provider, *args, **kwargs):
        call_count['count'] += 1
        if provider == 'provider1':
            raise Exception("Provider1 failed")
        elif provider == 'provider2':
            return f"Success from {provider}"
        else:
            raise Exception(f"Unknown provider: {provider}")
    
    # 执行带回退的请求
    try:
        result, used_provider, fallback_event = handler.execute_with_fallback(
            primary_provider='provider1',
            request_func=mock_request_func,
            available_providers=['provider1', 'provider2']
        )
        
        assert result == "Success from provider2"
        assert used_provider == "provider2"
        assert fallback_event is not None
        assert fallback_event.from_provider == "provider1"
        assert fallback_event.to_provider == "provider2"
        assert fallback_event.success is True
        
        print("✓ 回退执行成功")
        
    except Exception as e:
        print(f"❌ 回退执行失败: {e}")
        raise


def test_fallback_stats():
    """测试回退统计"""
    print("测试回退统计...")
    
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
    
    print("✓ 回退统计功能正常")


def test_manual_fallback():
    """测试手动回退"""
    print("测试手动回退...")
    
    handler = FallbackHandler()
    
    # 执行手动回退
    event = handler.manual_fallback("google", "volcano", "测试手动切换")
    
    assert event.from_provider == "google"
    assert event.to_provider == "volcano"
    assert event.success is True
    
    # 检查历史记录
    history = handler.get_fallback_history(limit=1)
    assert len(history) == 1
    assert history[0].from_provider == "google"
    
    print("✓ 手动回退功能正常")


def main():
    """运行所有测试"""
    print("开始回退机制测试...")
    print("=" * 50)
    
    try:
        test_fallback_handler_basic()
        test_fallback_event()
        test_circuit_breaker()
        test_fallback_reason_determination()
        test_fallback_execution()
        test_fallback_stats()
        test_manual_fallback()
        
        print("=" * 50)
        print("🎉 所有回退机制测试通过！")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)