#!/usr/bin/env python3
"""
Volcano多模态分析使用示例

本示例展示如何使用Volcano API进行多模态用户行为分析，
包括文本和图像内容的综合分析。

使用前请确保：
1. 已配置ARK_API_KEY环境变量
2. 已启用多模态功能
3. 图片URL可访问或使用本地图片
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

# 导入必要的模块
try:
    from config.volcano_llm_client import VolcanoLLMClient
    from config.multimodal_content_handler import MultiModalContentHandler
    from config.llm_provider_manager import LLMProviderManager
    from utils.logger import setup_logger
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保已正确安装所有依赖")
    exit(1)

# 设置日志
logger = setup_logger(__name__)

class VolcanoMultiModalDemo:
    """Volcano多模态分析演示类"""
    
    def __init__(self):
        """初始化演示环境"""
        self.content_handler = MultiModalContentHandler()
        self.provider_manager = LLMProviderManager()
        self.results = {}
        
        # 检查配置
        self._check_configuration()
    
    def _check_configuration(self):
        """检查配置是否正确"""
        ark_api_key = os.getenv('ARK_API_KEY')
        if not ark_api_key:
            raise ValueError("请设置ARK_API_KEY环境变量")
        
        enable_multimodal = os.getenv('ENABLE_MULTIMODAL', 'true').lower() == 'true'
        if not enable_multimodal:
            logger.warning("多模态功能未启用，将只进行文本分析")
    
    def run_comprehensive_demo(self):
        """运行综合演示"""
        print("🚀 开始Volcano多模态分析演示")
        print("=" * 50)
        
        # 1. 基础连接测试
        print("\n1️⃣ 测试Volcano API连接...")
        self._test_volcano_connection()
        
        # 2. 文本分析示例
        print("\n2️⃣ 执行文本分析示例...")
        self._demo_text_analysis()
        
        # 3. 多模态分析示例
        print("\n3️⃣ 执行多模态分析示例...")
        self._demo_multimodal_analysis()
        
        # 4. 用户行为分析示例
        print("\n4️⃣ 执行用户行为分析示例...")
        self._demo_user_behavior_analysis()
        
        # 5. 提供商切换演示
        print("\n5️⃣ 演示提供商自动切换...")
        self._demo_provider_fallback()
        
        # 6. 生成分析报告
        print("\n6️⃣ 生成分析报告...")
        self._generate_demo_report()
        
        print("\n✅ 演示完成！")
    
    def _test_volcano_connection(self):
        """测试Volcano API连接"""
        try:
            llm = self.provider_manager.get_llm(provider="volcano")
            
            test_prompt = "请简单介绍一下你的能力"
            response = llm.invoke(test_prompt)
            
            print(f"✅ Volcano API连接成功")
            print(f"📝 响应示例: {response[:100]}...")
            
            self.results['connection_test'] = {
                'status': 'success',
                'response_preview': response[:200]
            }
            
        except Exception as e:
            print(f"❌ Volcano API连接失败: {e}")
            self.results['connection_test'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def _demo_text_analysis(self):
        """演示文本分析功能"""
        try:
            llm = self.provider_manager.get_llm(provider="volcano")
            
            # 示例用户行为文本数据
            user_behavior_text = """
            用户在电商网站的行为记录：
            - 浏览了运动鞋类别页面，停留3分钟
            - 查看了5款不同品牌的运动鞋详情
            - 将2款鞋子加入购物车
            - 查看了用户评价和尺码指南
            - 最终购买了一款Nike运动鞋
            - 购买后查看了配送信息
            """
            
            analysis_prompt = f"""
            请分析以下用户行为数据，提供洞察和建议：
            
            {user_behavior_text}
            
            请从以下角度分析：
            1. 用户购买意图强度
            2. 决策过程特点
            3. 可能的优化建议
            4. 用户类型判断
            
            请以JSON格式返回结构化分析结果。
            """
            
            response = llm.invoke(analysis_prompt)
            
            print("✅ 文本分析完成")
            print(f"📊 分析结果: {response[:200]}...")
            
            self.results['text_analysis'] = {
                'input': user_behavior_text,
                'analysis': response
            }
            
        except Exception as e:
            print(f"❌ 文本分析失败: {e}")
            self.results['text_analysis'] = {'error': str(e)}
    
    def _demo_multimodal_analysis(self):
        """演示多模态分析功能"""
        try:
            llm = self.provider_manager.get_llm(provider="volcano")
            
            if not hasattr(llm, 'supports_multimodal') or not llm.supports_multimodal():
                print("⚠️ 当前LLM不支持多模态，跳过此演示")
                return
            
            # 构建多模态内容
            multimodal_content = [
                {
                    "type": "text",
                    "text": """请分析这个电商场景：用户正在浏览运动鞋商品页面。
                    请结合图片内容和文本描述，分析用户可能的购买意图和偏好。"""
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/sample_sneaker.jpg",  # 示例图片URL
                        "detail": "high"
                    }
                }
            ]
            
            # 验证和处理内容
            processed_content = self.content_handler.prepare_content(multimodal_content)
            
            # 构建多模态分析提示
            messages = [
                {
                    "role": "system",
                    "content": "你是一个专业的电商用户行为分析师，擅长分析多模态数据。"
                },
                {
                    "role": "user",
                    "content": processed_content
                }
            ]
            
            # 执行多模态分析
            response = llm.invoke(messages)
            
            print("✅ 多模态分析完成")
            print(f"🖼️ 分析结果: {response[:200]}...")
            
            self.results['multimodal_analysis'] = {
                'content_types': ['text', 'image'],
                'analysis': response
            }
            
        except Exception as e:
            print(f"❌ 多模态分析失败: {e}")
            print("💡 提示: 请检查图片URL是否可访问，或使用本地图片")
            self.results['multimodal_analysis'] = {'error': str(e)}
    
    def _demo_user_behavior_analysis(self):
        """演示用户行为分析"""
        try:
            # 模拟用户行为数据
            user_behavior_data = {
                "user_id": "user_12345",
                "session_data": {
                    "duration_minutes": 25,
                    "page_views": 12,
                    "events": [
                        {"event": "page_view", "page": "homepage", "timestamp": "2024-01-15T10:00:00"},
                        {"event": "search", "query": "运动鞋", "timestamp": "2024-01-15T10:02:00"},
                        {"event": "product_view", "product_id": "shoe_001", "timestamp": "2024-01-15T10:05:00"},
                        {"event": "add_to_cart", "product_id": "shoe_001", "timestamp": "2024-01-15T10:15:00"},
                        {"event": "checkout", "total": 299.99, "timestamp": "2024-01-15T10:20:00"}
                    ]
                },
                "user_profile": {
                    "age_group": "25-34",
                    "gender": "male",
                    "location": "北京",
                    "previous_purchases": 3
                }
            }
            
            # 分析用户行为模式
            analysis_result = self._analyze_user_behavior_pattern(user_behavior_data)
            
            print("✅ 用户行为分析完成")
            print(f"👤 用户类型: {analysis_result.get('user_type', 'unknown')}")
            print(f"🎯 购买意图: {analysis_result.get('purchase_intent', 'unknown')}")
            
            self.results['user_behavior_analysis'] = analysis_result
            
        except Exception as e:
            print(f"❌ 用户行为分析失败: {e}")
            self.results['user_behavior_analysis'] = {'error': str(e)}
    
    def _analyze_user_behavior_pattern(self, behavior_data: Dict) -> Dict:
        """分析用户行为模式"""
        try:
            llm = self.provider_manager.get_llm(provider="volcano")
            
            prompt = f"""
            请分析以下用户行为数据，识别用户类型和购买模式：
            
            {json.dumps(behavior_data, indent=2, ensure_ascii=False)}
            
            请提供以下分析：
            1. 用户类型分类（如：目标明确型、比较型、冲动型等）
            2. 购买意图强度（1-10分）
            3. 决策速度评估
            4. 个性化推荐策略
            5. 潜在流失风险评估
            
            请以JSON格式返回结构化结果。
            """
            
            response = llm.invoke(prompt)
            
            # 尝试解析JSON响应
            try:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return {"raw_analysis": response}
            except:
                return {"raw_analysis": response}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _demo_provider_fallback(self):
        """演示提供商自动切换"""
        try:
            print("🔄 测试提供商自动切换机制...")
            
            # 尝试使用不存在的提供商，触发fallback
            try:
                llm = self.provider_manager.get_llm(provider="nonexistent")
                response = llm.invoke("测试fallback机制")
                print("✅ Fallback机制工作正常")
                
                self.results['fallback_test'] = {
                    'status': 'success',
                    'fallback_triggered': True
                }
                
            except Exception as e:
                print(f"⚠️ Fallback测试: {e}")
                
                # 尝试正常的fallback场景
                llm = self.provider_manager.get_llm()  # 使用默认提供商
                response = llm.invoke("测试默认提供商")
                print("✅ 默认提供商工作正常")
                
                self.results['fallback_test'] = {
                    'status': 'partial_success',
                    'default_provider_works': True
                }
                
        except Exception as e:
            print(f"❌ 提供商切换测试失败: {e}")
            self.results['fallback_test'] = {'error': str(e)}
    
    def _generate_demo_report(self):
        """生成演示报告"""
        try:
            report = {
                "demo_info": {
                    "timestamp": datetime.now().isoformat(),
                    "demo_version": "1.0.0",
                    "volcano_integration": "enabled"
                },
                "test_results": self.results,
                "summary": self._generate_summary()
            }
            
            # 保存报告
            report_filename = f"volcano_multimodal_demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_path = os.path.join("reports", report_filename)
            
            # 确保reports目录存在
            os.makedirs("reports", exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"📄 演示报告已保存: {report_path}")
            
            # 打印摘要
            print("\n📊 演示摘要:")
            for key, value in report["summary"].items():
                print(f"  {key}: {value}")
                
        except Exception as e:
            print(f"❌ 生成报告失败: {e}")
    
    def _generate_summary(self) -> Dict:
        """生成演示摘要"""
        summary = {
            "总测试项目": len(self.results),
            "成功项目": 0,
            "失败项目": 0,
            "部分成功项目": 0
        }
        
        for test_name, result in self.results.items():
            if isinstance(result, dict):
                if result.get('status') == 'success':
                    summary["成功项目"] += 1
                elif result.get('status') == 'failed' or 'error' in result:
                    summary["失败项目"] += 1
                elif result.get('status') == 'partial_success':
                    summary["部分成功项目"] += 1
                else:
                    summary["成功项目"] += 1  # 默认认为成功
            else:
                summary["成功项目"] += 1
        
        return summary

def main():
    """主函数"""
    try:
        # 创建演示实例
        demo = VolcanoMultiModalDemo()
        
        # 运行演示
        demo.run_comprehensive_demo()
        
    except Exception as e:
        print(f"❌ 演示运行失败: {e}")
        print("\n💡 故障排除建议:")
        print("1. 检查ARK_API_KEY环境变量是否正确设置")
        print("2. 确认网络连接正常")
        print("3. 验证Volcano API服务状态")
        print("4. 查看详细错误日志")

if __name__ == "__main__":
    main()