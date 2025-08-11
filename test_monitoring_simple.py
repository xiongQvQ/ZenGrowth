#!/usr/bin/env python3
"""
简化的监控和日志增强功能测试
专注于测试监控系统的核心功能
"""

import os
import sys
import time
import json
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

from config.monitoring_system import (
    get_performance_monitor, 
    reset_performance_monitor,
    RequestType, 
    ResponseStatus,
    RequestMetrics
)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_provider_specific_metrics():
    """测试提供商特定指标收集"""
    print("\n=== 测试提供商特定指标收集 ===")
    
    # 重置监控器
    reset_performance_monitor()
    monitor = get_performance_monitor()
    
    # 模拟不同类型的请求
    test_scenarios = [
        {
            "provider": "volcano",
            "request_type": RequestType.TEXT_ONLY,
            "model": "doubao-seed-1-6-250615",
            "response_time": 1.2,
            "tokens_used": 150,
            "status": ResponseStatus.SUCCESS
        },
        {
            "provider": "volcano",
            "request_type": RequestType.MULTIMODAL,
            "model": "doubao-seed-1-6-250615",
            "response_time": 2.5,
            "tokens_used": 200,
            "image_count": 2,
            "status": ResponseStatus.SUCCESS
        },
        {
            "provider": "google",
            "request_type": RequestType.TEXT_ONLY,
            "model": "gemini-2.5-pro",
            "response_time": 0.8,
            "tokens_used": 120,
            "status": ResponseStatus.SUCCESS
        },
        {
            "provider": "volcano",
            "request_type": RequestType.TEXT_ONLY,
            "model": "doubao-seed-1-6-250615",
            "status": ResponseStatus.RATE_LIMITED,
            "error_message": "Rate limit exceeded"
        }
    ]
    
    # 记录测试请求
    for i, scenario in enumerate(test_scenarios):
        request_id = f"test_request_{i+1}"
        
        # 开始请求记录
        metrics = monitor.record_request_start(
            request_id=request_id,
            provider=scenario["provider"],
            prompt=f"Test prompt {i+1}",
            request_type=scenario["request_type"],
            image_count=scenario.get("image_count", 0),
            model=scenario["model"]
        )
        
        # 结束请求记录
        monitor.record_request_end(
            metrics=metrics,
            response=f"Test response {i+1}" if scenario["status"] == ResponseStatus.SUCCESS else None,
            status=scenario["status"],
            error_message=scenario.get("error_message"),
            tokens_used=scenario.get("tokens_used"),
            retry_count=scenario.get("retry_count", 0)
        )
        
        print(f"✓ 记录了请求 {request_id}: {scenario['provider']} - {scenario['request_type'].value}")
    
    # 验证提供商特定指标
    volcano_metrics = monitor.get_provider_specific_metrics("volcano")
    google_metrics = monitor.get_provider_specific_metrics("google")
    
    print(f"\n--- Volcano 提供商特定指标 ---")
    if volcano_metrics:
        print(f"模型性能: {json.dumps(volcano_metrics.get('model_performance', {}), indent=2, ensure_ascii=False)}")
        print(f"多模态统计: {json.dumps(volcano_metrics.get('multimodal_stats', {}), indent=2, ensure_ascii=False)}")
        print(f"错误模式: {json.dumps(volcano_metrics.get('error_patterns', {}), indent=2, ensure_ascii=False)}")
        print(f"延迟分布记录数: {len(volcano_metrics.get('latency_distribution', []))}")
    else:
        print("❌ 没有找到 Volcano 提供商特定指标")
    
    print(f"\n--- Google 提供商特定指标 ---")
    if google_metrics:
        print(f"模型性能: {json.dumps(google_metrics.get('model_performance', {}), indent=2, ensure_ascii=False)}")
        print(f"延迟分布记录数: {len(google_metrics.get('latency_distribution', []))}")
    else:
        print("❌ 没有找到 Google 提供商特定指标")
    
    return volcano_metrics is not None and google_metrics is not None


def test_detailed_logging():
    """测试详细的请求/响应日志记录"""
    print("\n=== 测试详细的请求/响应日志记录 ===")
    
    # 检查日志文件是否创建
    log_dir = Path("logs/monitoring")
    expected_log_files = [
        "requests.log",
        "performance.log",
        "errors.log",
        "provider_comparison.log",
        "provider_metrics.log"
    ]
    
    created_files = []
    for log_file in expected_log_files:
        log_path = log_dir / log_file
        if log_path.exists():
            created_files.append(log_file)
            print(f"✓ 日志文件已创建: {log_path}")
            
            # 检查文件内容
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        print(f"  - 文件大小: {len(content)} 字符")
                        # 显示最后几行
                        lines = content.strip().split('\n')
                        if lines:
                            print(f"  - 最新日志: {lines[-1][:100]}...")
                    else:
                        print(f"  - 文件为空")
            except Exception as e:
                print(f"  - 读取文件失败: {e}")
        else:
            print(f"❌ 日志文件未创建: {log_path}")
    
    print(f"\n创建的日志文件: {len(created_files)}/{len(expected_log_files)}")
    return len(created_files) >= 3  # 至少要有3个主要日志文件


def test_performance_comparison():
    """测试性能监控和提供商比较"""
    print("\n=== 测试性能监控和提供商比较 ===")
    
    monitor = get_performance_monitor()
    
    # 生成提供商比较报告
    comparison_report = monitor.get_provider_comparison_report(time_window_hours=1)
    
    print(f"比较报告状态: {comparison_report.get('status', 'success')}")
    
    if comparison_report.get('status') != 'no_data':
        print(f"总请求数: {comparison_report.get('total_requests', 0)}")
        print(f"提供商数量: {len(comparison_report.get('providers', {}))}")
        
        # 显示每个提供商的性能数据
        for provider, data in comparison_report.get('providers', {}).items():
            print(f"\n--- {provider} 提供商性能 ---")
            print(f"  总请求: {data.get('total_requests', 0)}")
            print(f"  成功率: {data.get('success_rate', 0):.1%}")
            print(f"  平均响应时间: {data['performance'].get('avg_response_time', 0):.2f}秒")
            print(f"  多模态请求: {data['capabilities'].get('multimodal_requests', 0)}")
            print(f"  回退使用: {data['reliability'].get('fallback_usage', 0)}")
        
        # 显示整体比较
        overall = comparison_report.get('overall_comparison', {})
        if overall:
            print(f"\n--- 整体比较 ---")
            print(f"性能排名: {overall.get('performance_ranking', [])}")
            print(f"可靠性排名: {overall.get('reliability_ranking', [])}")
            print(f"成本排名: {overall.get('cost_ranking', [])}")
            print(f"最佳整体: {overall.get('best_overall', 'N/A')}")
        
        # 显示建议
        recommendations = comparison_report.get('recommendations', [])
        if recommendations:
            print(f"\n--- 建议 ---")
            for rec in recommendations:
                print(f"  • {rec}")
        
        return True
    else:
        print(f"❌ 没有足够的数据生成比较报告: {comparison_report.get('message', '')}")
        return False


def test_detailed_performance_metrics():
    """测试详细性能指标"""
    print("\n=== 测试详细性能指标 ===")
    
    monitor = get_performance_monitor()
    
    # 测试每个提供商的详细指标
    providers = ["volcano", "google"]
    
    success_count = 0
    for provider in providers:
        print(f"\n--- {provider} 详细性能指标 ---")
        
        detailed_metrics = monitor.get_detailed_performance_metrics(provider, time_window_hours=1)
        
        if detailed_metrics.get('status') != 'no_data':
            print(f"✓ 获取到 {provider} 的详细指标")
            success_count += 1
            
            # 显示关键指标
            latency_analysis = detailed_metrics.get('latency_analysis', {})
            if latency_analysis.get('status') != 'no_data':
                print(f"  延迟分析:")
                print(f"    样本数: {latency_analysis.get('total_samples', 0)}")
                print(f"    平均值: {latency_analysis.get('mean', 0):.2f}秒")
                print(f"    中位数: {latency_analysis.get('median', 0):.2f}秒")
                print(f"    P95: {latency_analysis.get('percentiles', {}).get('p95', 0):.2f}秒")
            
            throughput_analysis = detailed_metrics.get('throughput_analysis', {})
            if throughput_analysis.get('status') != 'no_data':
                print(f"  吞吐量分析:")
                print(f"    总请求: {throughput_analysis.get('total_requests', 0)}")
                print(f"    成功率: {throughput_analysis.get('success_rate', 0):.1%}")
                print(f"    平均每分钟请求: {throughput_analysis.get('avg_requests_per_minute', 0):.1f}")
            
            multimodal_analysis = detailed_metrics.get('multimodal_analysis', {})
            if multimodal_analysis.get('status') != 'no_data':
                print(f"  多模态分析:")
                print(f"    多模态请求: {multimodal_analysis.get('total_multimodal_requests', 0)}")
                print(f"    多模态成功率: {multimodal_analysis.get('multimodal_success_rate', 0):.1%}")
                print(f"    处理图片总数: {multimodal_analysis.get('total_images_processed', 0)}")
        else:
            print(f"❌ 没有 {provider} 的详细指标数据")
    
    return success_count > 0


def test_export_functionality():
    """测试监控数据导出功能"""
    print("\n=== 测试监控数据导出功能 ===")
    
    monitor = get_performance_monitor()
    
    try:
        # 导出监控指标
        exported_data = monitor.export_metrics()
        
        print(f"✓ 成功导出监控数据")
        print(f"导出数据大小: {len(exported_data)} 字符")
        
        # 验证JSON格式
        parsed_data = json.loads(exported_data)
        print(f"✓ 导出数据为有效JSON格式")
        print(f"包含的键: {list(parsed_data.keys())}")
        
        # 检查关键数据
        if 'provider_stats' in parsed_data:
            provider_count = len(parsed_data['provider_stats'])
            print(f"✓ 包含 {provider_count} 个提供商的统计数据")
        
        if 'performance_comparison' in parsed_data:
            comparison_data = parsed_data['performance_comparison']
            if comparison_data.get('status') != 'no_data':
                print(f"✓ 包含性能比较数据")
            else:
                print(f"⚠ 性能比较数据为空")
        
        return True
        
    except Exception as e:
        print(f"❌ 监控数据导出测试失败: {e}")
        return False


def test_all_provider_metrics():
    """测试获取所有提供商指标"""
    print("\n=== 测试获取所有提供商指标 ===")
    
    monitor = get_performance_monitor()
    
    # 获取所有提供商的特定指标
    all_metrics = monitor.get_all_provider_specific_metrics()
    
    print(f"监控的提供商数量: {len(all_metrics)}")
    
    for provider, metrics in all_metrics.items():
        print(f"\n--- {provider} 提供商指标概览 ---")
        print(f"  模型数量: {len(metrics.get('model_performance', {}))}")
        print(f"  延迟记录数: {len(metrics.get('latency_distribution', []))}")
        print(f"  错误模式数: {len(metrics.get('error_patterns', {}))}")
        print(f"  成本分析项: {len(metrics.get('cost_analysis', {}))}")
        
        # 显示多模态统计
        multimodal_stats = metrics.get('multimodal_stats', {})
        if multimodal_stats:
            print(f"  多模态请求: {multimodal_stats.get('total_requests', 0)}")
            print(f"  处理图片数: {multimodal_stats.get('total_images', 0)}")
    
    return len(all_metrics) > 0


def main():
    """主测试函数"""
    print("开始测试监控和日志增强功能...")
    
    # 确保日志目录存在
    log_dir = Path("logs/monitoring")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    test_results = []
    
    # 运行各项测试
    test_functions = [
        ("提供商特定指标收集", test_provider_specific_metrics),
        ("详细日志记录", test_detailed_logging),
        ("性能比较", test_performance_comparison),
        ("详细性能指标", test_detailed_performance_metrics),
        ("数据导出功能", test_export_functionality),
        ("所有提供商指标", test_all_provider_metrics)
    ]
    
    for test_name, test_func in test_functions:
        print(f"\n{'='*60}")
        print(f"运行测试: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            test_results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} - 通过")
            else:
                print(f"❌ {test_name} - 失败")
                
        except Exception as e:
            print(f"❌ {test_name} - 异常: {e}")
            import traceback
            traceback.print_exc()
            test_results.append((test_name, False))
    
    # 汇总测试结果
    print(f"\n{'='*60}")
    print("测试结果汇总")
    print(f"{'='*60}")
    
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总体结果: {passed_tests}/{total_tests} 测试通过")
    
    if passed_tests == total_tests:
        print("🎉 所有监控和日志增强功能测试通过！")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关功能")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)