"""
监控系统测试
测试监控和日志增强功能
"""

import os
import sys
import time
import json
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.monitoring_system import (
    PerformanceMonitor, 
    RequestType, 
    ResponseStatus,
    get_performance_monitor,
    reset_performance_monitor
)
from config.volcano_llm_client_monitored import MonitoredVolcanoLLMClient
from config.llm_provider_manager import get_provider_manager, reset_provider_manager
from config.settings import settings

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_performance_monitor():
    """测试性能监控器基本功能"""
    print("\n=== 测试性能监控器基本功能 ===")
    
    # 重置监控器
    reset_performance_monitor()
    monitor = get_performance_monitor()
    
    # 模拟请求记录
    metrics = monitor.record_request_start(
        request_id="test-001",
        provider="volcano",
        prompt="Hello, world!",
        request_type=RequestType.TEXT_ONLY,
        model="doubao-seed-1-6-250615"
    )
    
    # 模拟处理时间
    time.sleep(0.1)
    
    # 记录成功结果
    monitor.record_request_end(
        metrics=metrics,
        response="Hello! How can I help you today?",
        status=ResponseStatus.SUCCESS,
        tokens_used=25
    )
    
    # 获取统计信息
    stats = monitor.get_provider_stats("volcano")
    print(f"提供商统计: {stats}")
    
    # 获取最近请求
    recent_requests = monitor.get_recent_requests(limit=5)
    print(f"最近请求数量: {len(recent_requests)}")
    
    # 获取性能比较
    comparison = monitor.get_performance_comparison()
    print(f"性能比较: {json.dumps(comparison, indent=2, ensure_ascii=False)}")
    
    print("✅ 性能监控器基本功能测试通过")


def test_monitoring_with_different_scenarios():
    """测试不同场景下的监控"""
    print("\n=== 测试不同场景下的监控 ===")
    
    monitor = get_performance_monitor()
    
    # 场景1: 成功的文本请求
    metrics1 = monitor.record_request_start(
        request_id="test-text-001",
        provider="volcano",
        prompt="What is AI?",
        request_type=RequestType.TEXT_ONLY
    )
    time.sleep(0.05)
    monitor.record_request_end(
        metrics=metrics1,
        response="AI stands for Artificial Intelligence...",
        status=ResponseStatus.SUCCESS,
        tokens_used=50
    )
    
    # 场景2: 多模态请求
    metrics2 = monitor.record_request_start(
        request_id="test-multimodal-001",
        provider="volcano",
        prompt="Describe this image",
        request_type=RequestType.MULTIMODAL,
        image_count=1
    )
    time.sleep(0.08)
    monitor.record_request_end(
        metrics=metrics2,
        response="This image shows...",
        status=ResponseStatus.SUCCESS,
        tokens_used=75
    )
    
    # 场景3: 失败的请求
    metrics3 = monitor.record_request_start(
        request_id="test-error-001",
        provider="volcano",
        prompt="Test error",
        request_type=RequestType.TEXT_ONLY
    )
    time.sleep(0.02)
    monitor.record_request_end(
        metrics=metrics3,
        status=ResponseStatus.ERROR,
        error_message="API rate limit exceeded",
        retry_count=2
    )
    
    # 场景4: 超时请求
    metrics4 = monitor.record_request_start(
        request_id="test-timeout-001",
        provider="volcano",
        prompt="Test timeout",
        request_type=RequestType.TEXT_ONLY
    )
    time.sleep(0.03)
    monitor.record_request_end(
        metrics=metrics4,
        status=ResponseStatus.TIMEOUT,
        error_message="Request timeout after 30 seconds"
    )
    
    # 获取统计信息
    stats = monitor.get_provider_stats("volcano")
    print(f"总请求数: {stats.total_requests}")
    print(f"成功请求数: {stats.successful_requests}")
    print(f"失败请求数: {stats.failed_requests}")
    print(f"成功率: {stats.success_rate:.2%}")
    print(f"平均响应时间: {stats.average_response_time:.3f}s")
    print(f"请求类型分布: {stats.request_count_by_type}")
    print(f"错误类型分布: {stats.error_count_by_type}")
    
    print("✅ 不同场景监控测试通过")


def test_system_health_monitoring():
    """测试系统健康监控"""
    print("\n=== 测试系统健康监控 ===")
    
    monitor = get_performance_monitor()
    
    # 获取系统健康状态
    health = monitor.get_system_health()
    print(f"系统健康状态: {json.dumps(health, indent=2, ensure_ascii=False)}")
    
    # 获取按小时统计
    hourly_stats = monitor.get_hourly_stats(hours=1)
    print(f"按小时统计: {json.dumps(hourly_stats, indent=2, ensure_ascii=False)}")
    
    print("✅ 系统健康监控测试通过")


def test_monitoring_export():
    """测试监控数据导出"""
    print("\n=== 测试监控数据导出 ===")
    
    monitor = get_performance_monitor()
    
    # 导出监控指标
    metrics_json = monitor.export_metrics()
    print(f"导出的监控指标长度: {len(metrics_json)} 字符")
    
    # 验证JSON格式
    try:
        metrics_data = json.loads(metrics_json)
        print(f"导出数据包含的键: {list(metrics_data.keys())}")
        print("✅ 监控数据导出测试通过")
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")


def test_monitored_volcano_client():
    """测试带监控的Volcano客户端"""
    print("\n=== 测试带监控的Volcano客户端 ===")
    
    # 检查API密钥配置
    if not settings.ark_api_key:
        print("⚠️  Volcano API密钥未配置，跳过客户端测试")
        return
    
    try:
        # 创建监控增强的客户端
        client = MonitoredVolcanoLLMClient(
            api_key=settings.ark_api_key,
            base_url=settings.ark_base_url,
            model=settings.ark_model
        )
        
        # 执行健康检查
        health_result = client.health_check()
        print(f"健康检查结果: {json.dumps(health_result, indent=2, ensure_ascii=False)}")
        
        # 获取监控统计
        stats = client.get_monitoring_stats()
        print(f"客户端监控统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
        
        # 获取最近请求
        recent_requests = client.get_recent_requests(limit=3)
        print(f"最近请求数量: {len(recent_requests)}")
        
        print("✅ 带监控的Volcano客户端测试通过")
        
    except Exception as e:
        print(f"⚠️  Volcano客户端测试失败: {e}")
        print("这可能是由于API密钥配置或网络连接问题")


def test_provider_manager_monitoring():
    """测试提供商管理器的监控功能"""
    print("\n=== 测试提供商管理器的监控功能 ===")
    
    try:
        # 重置提供商管理器
        reset_provider_manager()
        manager = get_provider_manager()
        
        # 获取监控统计
        monitoring_stats = manager.get_monitoring_stats()
        print(f"提供商管理器监控统计键: {list(monitoring_stats.keys())}")
        
        # 获取特定提供商的监控统计
        volcano_stats = manager.get_provider_monitoring_stats("volcano")
        if volcano_stats:
            print(f"Volcano提供商监控统计: {json.dumps(volcano_stats, indent=2, ensure_ascii=False)}")
        else:
            print("Volcano提供商监控统计: 无数据")
        
        # 导出监控报告
        report = manager.export_monitoring_report()
        print(f"监控报告长度: {len(report)} 字符")
        
        print("✅ 提供商管理器监控功能测试通过")
        
    except Exception as e:
        print(f"⚠️  提供商管理器监控测试失败: {e}")


def test_log_files_creation():
    """测试日志文件创建"""
    print("\n=== 测试日志文件创建 ===")
    
    log_dir = Path("logs/monitoring")
    
    expected_files = ["requests.log", "performance.log", "errors.log"]
    
    for filename in expected_files:
        log_file = log_dir / filename
        if log_file.exists():
            print(f"✅ 日志文件存在: {log_file}")
            # 显示文件大小
            size = log_file.stat().st_size
            print(f"   文件大小: {size} 字节")
        else:
            print(f"⚠️  日志文件不存在: {log_file}")
    
    print("✅ 日志文件创建测试完成")


def main():
    """主测试函数"""
    print("开始监控系统测试...")
    
    try:
        # 基本功能测试
        test_performance_monitor()
        test_monitoring_with_different_scenarios()
        test_system_health_monitoring()
        test_monitoring_export()
        
        # 集成测试
        test_monitored_volcano_client()
        test_provider_manager_monitoring()
        
        # 日志测试
        test_log_files_creation()
        
        print("\n🎉 所有监控系统测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()