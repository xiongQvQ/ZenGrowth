"""
核心集成测试
测试提供商管理器和回退处理器的核心功能，不依赖外部库
"""

import logging
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_fallback_handler_singleton():
    """测试回退处理器单例模式"""
    print("测试回退处理器单例模式...")
    
    from config.fallback_handler import get_fallback_handler, reset_fallback_handler
    
    # 重置单例
    reset_fallback_handler()
    
    # 获取两个实例
    handler1 = get_fallback_handler()
    handler2 = get_fallback_handler()
    
    # 验证是同一个实例
    assert handler1 is handler2
    print("✓ 回退处理器单例模式正常")


def test_fallback_configuration():
    """测试回退配置"""
    print("测试回退配置...")
    
    from config.fallback_handler import FallbackHandler, FallbackStrategy
    
    # 创建自定义配置的处理器
    handler = FallbackHandler(
        fallback_order=['provider1', 'provider2', 'provider3'],
        strategy=FallbackStrategy.IMMEDIATE,
        max_retries=3,
        retry_delay=0.5
    )
    
    assert handler.fallback_order == ['provider1', 'provider2', 'provider3']
    assert handler.strategy == FallbackStrategy.IMMEDIATE
    assert handler.max_retries == 3
    assert handler.retry_delay == 0.5
    
    print("✓ 回退配置正常")


def test_fallback_order_management():
    """测试回退顺序管理"""
    print("测试回退顺序管理...")
    
    from config.fallback_handler import FallbackHandler
    
    handler = FallbackHandler(fallback_order=['google', 'volcano'])
    
    # 测试构建尝试顺序
    try_order = handler._build_try_order('google', ['google', 'volcano'])
    assert try_order == ['google', 'volcano']
    
    try_order = handler._build_try_order('volcano', ['google', 'volcano'])
    assert try_order == ['volcano', 'google']
    
    # 测试更新回退顺序
    new_order = ['volcano', 'google']
    handler.update_fallback_order(new_order)
    assert handler.fallback_order == new_order
    
    print("✓ 回退顺序管理正常")


def test_error_classification():
    """测试错误分类"""
    print("测试错误分类...")
    
    from config.fallback_handler import FallbackHandler, FallbackReason
    
    handler = FallbackHandler()
    
    # 测试各种错误类型的分类
    test_cases = [
        ("Connection timeout", FallbackReason.TIMEOUT),
        ("Rate limit exceeded (429)", FallbackReason.RATE_LIMIT),
        ("Authentication failed (401)", FallbackReason.AUTHENTICATION_ERROR),
        ("Quota exceeded (403)", FallbackReason.QUOTA_EXCEEDED),
        ("Configuration error", FallbackReason.CONFIGURATION_ERROR),
        ("Unknown error", FallbackReason.REQUEST_FAILED)
    ]
    
    for error_msg, expected_reason in test_cases:
        error = Exception(error_msg)
        reason = handler._determine_fallback_reason(error)
        assert reason == expected_reason, f"错误 '{error_msg}' 应该分类为 {expected_reason}, 但得到 {reason}"
    
    print("✓ 错误分类正常")


def test_circuit_breaker_logic():
    """测试断路器逻辑"""
    print("测试断路器逻辑...")
    
    from config.fallback_handler import FallbackHandler
    
    handler = FallbackHandler()
    provider = "test_provider"
    
    # 初始状态应该是关闭的
    assert handler._is_circuit_breaker_open(provider) is False
    
    # 模拟连续失败
    for i in range(5):  # 达到阈值
        handler._update_circuit_breaker(provider, False)
    
    # 断路器应该开启
    assert handler._is_circuit_breaker_open(provider) is True
    
    # 成功请求应该重置断路器
    handler._update_circuit_breaker(provider, True)
    assert handler._is_circuit_breaker_open(provider) is False
    
    print("✓ 断路器逻辑正常")


def test_statistics_tracking():
    """测试统计跟踪"""
    print("测试统计跟踪...")
    
    from config.fallback_handler import FallbackHandler, FallbackEvent, FallbackReason
    
    handler = FallbackHandler()
    
    # 创建测试事件
    events = [
        FallbackEvent(
            from_provider="google",
            to_provider="volcano",
            reason=FallbackReason.PROVIDER_UNAVAILABLE,
            success=True,
            response_time=1.0
        ),
        FallbackEvent(
            from_provider="volcano",
            to_provider="google",
            reason=FallbackReason.TIMEOUT,
            success=False,
            response_time=2.0
        ),
        FallbackEvent(
            from_provider="google",
            to_provider="volcano",
            reason=FallbackReason.RATE_LIMIT,
            success=True,
            response_time=1.5
        )
    ]
    
    # 记录事件
    for event in events:
        handler._record_fallback_event(event)
    
    # 检查统计信息
    stats = handler.get_fallback_stats()
    assert stats.total_fallbacks == 3
    assert stats.successful_fallbacks == 2
    assert stats.failed_fallbacks == 1
    assert stats.fallback_success_rate == 2/3
    
    # 检查按原因统计
    assert stats.fallback_by_reason['provider_unavailable'] == 1
    assert stats.fallback_by_reason['timeout'] == 1
    assert stats.fallback_by_reason['rate_limit'] == 1
    
    # 检查按提供商统计
    assert stats.fallback_by_provider['google->volcano'] == 2
    assert stats.fallback_by_provider['volcano->google'] == 1
    
    print("✓ 统计跟踪正常")


def test_export_functionality():
    """测试导出功能"""
    print("测试导出功能...")
    
    from config.fallback_handler import FallbackHandler
    import json
    
    handler = FallbackHandler()
    
    # 添加一些测试数据
    handler.manual_fallback("google", "volcano", "测试导出")
    
    # 测试导出报告
    report_json = handler.export_fallback_report()
    if isinstance(report_json, str):
        report_data = json.loads(report_json)
    else:
        report_data = report_json  # 如果已经是字典，直接使用
    
    # 验证报告结构
    assert 'timestamp' in report_data
    assert 'configuration' in report_data
    assert 'statistics' in report_data
    assert 'circuit_breaker_status' in report_data
    assert 'recent_history' in report_data
    
    # 验证配置信息
    config = report_data['configuration']
    assert 'fallback_order' in config
    assert 'strategy' in config
    assert 'max_retries' in config
    
    # 验证统计信息
    stats = report_data['statistics']
    assert 'total_fallbacks' in stats
    assert 'successful_fallbacks' in stats
    assert 'fallback_success_rate' in stats
    
    print("✓ 导出功能正常")


def test_configuration_validation():
    """测试配置验证"""
    print("测试配置验证...")
    
    from config.fallback_handler import FallbackHandler, FallbackStrategy
    
    # 测试有效配置
    try:
        handler = FallbackHandler(
            fallback_order=['google', 'volcano'],
            strategy=FallbackStrategy.IMMEDIATE,
            max_retries=3,
            retry_delay=1.0
        )
        assert handler is not None
    except Exception as e:
        assert False, f"有效配置应该成功创建处理器: {e}"
    
    # 测试空回退顺序
    try:
        handler = FallbackHandler(fallback_order=[])
        # 空回退顺序会使用默认的settings.fallback_order
        assert isinstance(handler.fallback_order, list)
    except Exception as e:
        assert False, f"空回退顺序应该被允许: {e}"
    
    print("✓ 配置验证正常")


def main():
    """运行所有核心集成测试"""
    print("开始核心集成测试...")
    print("=" * 50)
    
    try:
        test_fallback_handler_singleton()
        test_fallback_configuration()
        test_fallback_order_management()
        test_error_classification()
        test_circuit_breaker_logic()
        test_statistics_tracking()
        test_export_functionality()
        test_configuration_validation()
        
        print("=" * 50)
        print("🎉 所有核心集成测试通过！")
        print("=" * 50)
        
        # 输出功能总结
        print("\n📋 实现的功能总结:")
        print("✓ LLM提供商管理系统")
        print("  - 多提供商支持 (Google Gemini, Volcano Doubao)")
        print("  - 提供商健康检查和可用性检测")
        print("  - 动态提供商选择和切换")
        print("✓ 自动回退机制")
        print("  - 智能回退顺序管理")
        print("  - 断路器模式防止级联失败")
        print("  - 详细的回退事件跟踪和日志")
        print("✓ 统计和监控")
        print("  - 回退成功/失败率统计")
        print("  - 按原因和提供商的回退分析")
        print("  - 完整的导出和报告功能")
        print("✓ 配置管理")
        print("  - 灵活的回退策略配置")
        print("  - 运行时配置更新支持")
        print("  - 全面的错误分类和处理")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 核心集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)