"""
集成测试运行器
运行所有智能体兼容性和提供商切换测试
"""

import pytest
import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.llm_provider_manager import get_provider_manager, ProviderStatus
from config.settings import settings

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tests/integration_test.log')
    ]
)
logger = logging.getLogger(__name__)


class IntegrationTestRunner:
    """集成测试运行器"""
    
    def __init__(self):
        self.provider_manager = get_provider_manager()
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    def check_prerequisites(self) -> bool:
        """检查测试前提条件"""
        logger.info("检查测试前提条件...")
        
        # 检查提供商可用性
        google_status = self.provider_manager.health_check("google")
        volcano_status = self.provider_manager.health_check("volcano")
        
        google_available = google_status.status == ProviderStatus.AVAILABLE
        volcano_available = volcano_status.status == ProviderStatus.AVAILABLE
        
        logger.info(f"Google提供商状态: {google_status.status.value}")
        logger.info(f"Volcano提供商状态: {volcano_status.status.value}")
        
        if not google_available:
            logger.error("Google提供商不可用，无法运行集成测试")
            return False
            
        if not volcano_available:
            logger.error("Volcano提供商不可用，无法运行集成测试")
            return False
        
        # 检查配置
        if not settings.google_api_key:
            logger.error("Google API密钥未配置")
            return False
            
        if not settings.ark_api_key:
            logger.error("Volcano API密钥未配置")
            return False
        
        logger.info("所有前提条件检查通过")
        return True
    
    def run_compatibility_tests(self) -> Dict[str, Any]:
        """运行智能体兼容性测试"""
        logger.info("开始运行智能体兼容性测试...")
        
        # 运行兼容性测试
        exit_code = pytest.main([
            "tests/test_agent_volcano_compatibility.py",
            "-v",
            "--tb=short",
            "--json-report",
            "--json-report-file=tests/compatibility_test_report.json"
        ])
        
        # 读取测试报告
        try:
            with open("tests/compatibility_test_report.json", 'r') as f:
                report = json.load(f)
            
            return {
                "exit_code": exit_code,
                "summary": report.get("summary", {}),
                "tests": report.get("tests", []),
                "duration": report.get("duration", 0)
            }
        except Exception as e:
            logger.error(f"读取兼容性测试报告失败: {e}")
            return {"exit_code": exit_code, "error": str(e)}
    
    def run_switching_tests(self) -> Dict[str, Any]:
        """运行提供商切换测试"""
        logger.info("开始运行提供商切换测试...")
        
        # 运行切换测试
        exit_code = pytest.main([
            "tests/test_provider_switching.py",
            "-v",
            "--tb=short",
            "--json-report",
            "--json-report-file=tests/switching_test_report.json"
        ])
        
        # 读取测试报告
        try:
            with open("tests/switching_test_report.json", 'r') as f:
                report = json.load(f)
            
            return {
                "exit_code": exit_code,
                "summary": report.get("summary", {}),
                "tests": report.get("tests", []),
                "duration": report.get("duration", 0)
            }
        except Exception as e:
            logger.error(f"读取切换测试报告失败: {e}")
            return {"exit_code": exit_code, "error": str(e)}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有集成测试"""
        logger.info("开始运行完整集成测试套件...")
        
        self.start_time = time.time()
        
        # 检查前提条件
        if not self.check_prerequisites():
            return {
                "success": False,
                "error": "前提条件检查失败",
                "duration": 0
            }
        
        results = {
            "success": True,
            "start_time": datetime.now().isoformat(),
            "compatibility_tests": {},
            "switching_tests": {},
            "overall_summary": {},
            "recommendations": []
        }
        
        try:
            # 运行兼容性测试
            compatibility_results = self.run_compatibility_tests()
            results["compatibility_tests"] = compatibility_results
            
            # 运行切换测试
            switching_results = self.run_switching_tests()
            results["switching_tests"] = switching_results
            
            # 生成总体摘要
            results["overall_summary"] = self._generate_overall_summary(
                compatibility_results, switching_results
            )
            
            # 生成建议
            results["recommendations"] = self._generate_recommendations(
                compatibility_results, switching_results
            )
            
        except Exception as e:
            logger.error(f"集成测试执行失败: {e}")
            results["success"] = False
            results["error"] = str(e)
        
        self.end_time = time.time()
        results["duration"] = self.end_time - self.start_time
        results["end_time"] = datetime.now().isoformat()
        
        # 保存完整报告
        self._save_integration_report(results)
        
        return results
    
    def _generate_overall_summary(self, compatibility_results: Dict, switching_results: Dict) -> Dict[str, Any]:
        """生成总体摘要"""
        summary = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "success_rate": 0.0,
            "total_duration": 0.0
        }
        
        # 汇总兼容性测试结果
        if "summary" in compatibility_results:
            comp_summary = compatibility_results["summary"]
            summary["total_tests"] += comp_summary.get("total", 0)
            summary["passed_tests"] += comp_summary.get("passed", 0)
            summary["failed_tests"] += comp_summary.get("failed", 0)
            summary["skipped_tests"] += comp_summary.get("skipped", 0)
            summary["total_duration"] += compatibility_results.get("duration", 0)
        
        # 汇总切换测试结果
        if "summary" in switching_results:
            switch_summary = switching_results["summary"]
            summary["total_tests"] += switch_summary.get("total", 0)
            summary["passed_tests"] += switch_summary.get("passed", 0)
            summary["failed_tests"] += switch_summary.get("failed", 0)
            summary["skipped_tests"] += switch_summary.get("skipped", 0)
            summary["total_duration"] += switching_results.get("duration", 0)
        
        # 计算成功率
        if summary["total_tests"] > 0:
            summary["success_rate"] = summary["passed_tests"] / summary["total_tests"]
        
        return summary
    
    def _generate_recommendations(self, compatibility_results: Dict, switching_results: Dict) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于兼容性测试结果的建议
        if compatibility_results.get("exit_code", 0) != 0:
            recommendations.append("智能体兼容性测试存在失败，建议检查Volcano提供商的响应格式和质量")
        
        # 基于切换测试结果的建议
        if switching_results.get("exit_code", 0) != 0:
            recommendations.append("提供商切换测试存在失败，建议优化切换机制和回退逻辑")
        
        # 基于总体成功率的建议
        overall_summary = self._generate_overall_summary(compatibility_results, switching_results)
        success_rate = overall_summary.get("success_rate", 0)
        
        if success_rate < 0.8:
            recommendations.append(f"总体测试成功率较低({success_rate:.1%})，建议全面检查Volcano集成实现")
        elif success_rate < 0.9:
            recommendations.append(f"测试成功率良好({success_rate:.1%})，但仍有改进空间")
        else:
            recommendations.append(f"测试成功率优秀({success_rate:.1%})，Volcano集成质量良好")
        
        # 性能相关建议
        total_duration = overall_summary.get("total_duration", 0)
        if total_duration > 300:  # 5分钟
            recommendations.append("测试执行时间较长，建议优化提供商响应速度")
        
        # 如果没有其他建议，添加通用建议
        if not recommendations:
            recommendations.append("所有测试通过，建议定期运行集成测试以确保持续稳定性")
        
        return recommendations
    
    def _save_integration_report(self, results: Dict[str, Any]):
        """保存集成测试报告"""
        report_filename = f"tests/integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"集成测试报告已保存到: {report_filename}")
            
            # 同时保存最新报告
            with open("tests/latest_integration_report.json", 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存集成测试报告失败: {e}")
    
    def print_summary(self, results: Dict[str, Any]):
        """打印测试摘要"""
        print("\n" + "="*80)
        print("集成测试摘要")
        print("="*80)
        
        if not results.get("success", False):
            print(f"❌ 测试执行失败: {results.get('error', '未知错误')}")
            return
        
        overall_summary = results.get("overall_summary", {})
        
        print(f"📊 总体统计:")
        print(f"   总测试数: {overall_summary.get('total_tests', 0)}")
        print(f"   通过: {overall_summary.get('passed_tests', 0)}")
        print(f"   失败: {overall_summary.get('failed_tests', 0)}")
        print(f"   跳过: {overall_summary.get('skipped_tests', 0)}")
        print(f"   成功率: {overall_summary.get('success_rate', 0):.1%}")
        print(f"   总耗时: {overall_summary.get('total_duration', 0):.1f}s")
        
        # 兼容性测试结果
        comp_results = results.get("compatibility_tests", {})
        comp_exit_code = comp_results.get("exit_code", -1)
        comp_status = "✅ 通过" if comp_exit_code == 0 else "❌ 失败"
        print(f"\n🤖 智能体兼容性测试: {comp_status}")
        
        if "summary" in comp_results:
            comp_summary = comp_results["summary"]
            print(f"   测试数: {comp_summary.get('total', 0)}")
            print(f"   通过: {comp_summary.get('passed', 0)}")
            print(f"   失败: {comp_summary.get('failed', 0)}")
        
        # 切换测试结果
        switch_results = results.get("switching_tests", {})
        switch_exit_code = switch_results.get("exit_code", -1)
        switch_status = "✅ 通过" if switch_exit_code == 0 else "❌ 失败"
        print(f"\n🔄 提供商切换测试: {switch_status}")
        
        if "summary" in switch_results:
            switch_summary = switch_results["summary"]
            print(f"   测试数: {switch_summary.get('total', 0)}")
            print(f"   通过: {switch_summary.get('passed', 0)}")
            print(f"   失败: {switch_summary.get('failed', 0)}")
        
        # 建议
        recommendations = results.get("recommendations", [])
        if recommendations:
            print(f"\n💡 改进建议:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("\n" + "="*80)
    
    def run_quick_test(self) -> Dict[str, Any]:
        """运行快速测试（仅核心功能）"""
        logger.info("开始运行快速集成测试...")
        
        self.start_time = time.time()
        
        if not self.check_prerequisites():
            return {
                "success": False,
                "error": "前提条件检查失败"
            }
        
        # 运行核心测试
        exit_code = pytest.main([
            "tests/test_agent_volcano_compatibility.py::TestAgentVolcanoCompatibility::test_agent_creation_volcano",
            "tests/test_agent_volcano_compatibility.py::TestAgentVolcanoCompatibility::test_agent_basic_functionality_volcano",
            "tests/test_provider_switching.py::TestProviderSwitching::test_dynamic_provider_switching",
            "tests/test_provider_switching.py::TestProviderSwitching::test_fallback_during_analysis",
            "-v",
            "--tb=short"
        ])
        
        self.end_time = time.time()
        
        return {
            "success": exit_code == 0,
            "exit_code": exit_code,
            "duration": self.end_time - self.start_time,
            "test_type": "quick"
        }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="运行Volcano API集成测试")
    parser.add_argument("--quick", action="store_true", help="运行快速测试")
    parser.add_argument("--compatibility-only", action="store_true", help="仅运行兼容性测试")
    parser.add_argument("--switching-only", action="store_true", help="仅运行切换测试")
    
    args = parser.parse_args()
    
    runner = IntegrationTestRunner()
    
    if args.quick:
        results = runner.run_quick_test()
        print(f"\n快速测试完成: {'✅ 通过' if results['success'] else '❌ 失败'}")
        print(f"耗时: {results['duration']:.1f}s")
        
    elif args.compatibility_only:
        results = runner.run_compatibility_tests()
        print(f"\n兼容性测试完成: {'✅ 通过' if results['exit_code'] == 0 else '❌ 失败'}")
        
    elif args.switching_only:
        results = runner.run_switching_tests()
        print(f"\n切换测试完成: {'✅ 通过' if results['exit_code'] == 0 else '❌ 失败'}")
        
    else:
        results = runner.run_all_tests()
        runner.print_summary(results)
    
    # 返回适当的退出码
    if isinstance(results, dict):
        if "exit_code" in results:
            sys.exit(results["exit_code"])
        elif not results.get("success", False):
            sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()