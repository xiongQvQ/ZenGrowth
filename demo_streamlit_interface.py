"""
Streamlit界面功能演示脚本
展示文件上传、数据处理和界面交互功能
"""

import json
import tempfile
import os
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tools.ga4_data_parser import GA4DataParser
from tools.data_validator import DataValidator
from tools.data_storage_manager import DataStorageManager


def create_demo_ga4_file():
    """创建演示用的GA4数据文件"""
    demo_events = [
        {
            "event_date": "20241201",
            "event_timestamp": 1733097600000000,
            "event_name": "page_view",
            "user_pseudo_id": "demo_user_001",
            "user_id": "registered_user_001",
            "platform": "WEB",
            "device": {
                "category": "desktop",
                "operating_system": "Windows",
                "browser": "Chrome",
                "browser_version": "120.0.0.0"
            },
            "geo": {
                "country": "US",
                "region": "CA",
                "city": "San Francisco"
            },
            "traffic_source": {
                "source": "google",
                "medium": "organic",
                "campaign": "(not set)"
            },
            "event_params": [
                {
                    "key": "page_title",
                    "value": {"string_value": "首页 - 用户行为分析平台"}
                },
                {
                    "key": "page_location",
                    "value": {"string_value": "https://analytics-platform.com/"}
                },
                {
                    "key": "ga_session_id",
                    "value": {"string_value": "session_001"}
                }
            ],
            "user_properties": [
                {
                    "key": "user_type",
                    "value": {"string_value": "premium"}
                },
                {
                    "key": "subscription_plan",
                    "value": {"string_value": "pro"}
                }
            ]
        },
        {
            "event_date": "20241201",
            "event_timestamp": 1733097660000000,
            "event_name": "view_item",
            "user_pseudo_id": "demo_user_001",
            "user_id": "registered_user_001",
            "platform": "WEB",
            "device": {
                "category": "desktop",
                "operating_system": "Windows",
                "browser": "Chrome",
                "browser_version": "120.0.0.0"
            },
            "geo": {
                "country": "US",
                "region": "CA",
                "city": "San Francisco"
            },
            "traffic_source": {
                "source": "google",
                "medium": "organic",
                "campaign": "(not set)"
            },
            "event_params": [
                {
                    "key": "item_id",
                    "value": {"string_value": "analytics_dashboard"}
                },
                {
                    "key": "item_category",
                    "value": {"string_value": "dashboard"}
                },
                {
                    "key": "ga_session_id",
                    "value": {"string_value": "session_001"}
                }
            ],
            "user_properties": [
                {
                    "key": "user_type",
                    "value": {"string_value": "premium"}
                }
            ],
            "items": [
                {
                    "item_id": "analytics_dashboard",
                    "item_name": "分析仪表板",
                    "item_category": "dashboard",
                    "price": 0,
                    "quantity": 1
                }
            ]
        },
        {
            "event_date": "20241201",
            "event_timestamp": 1733097720000000,
            "event_name": "sign_up",
            "user_pseudo_id": "demo_user_002",
            "user_id": "",
            "platform": "WEB",
            "device": {
                "category": "mobile",
                "operating_system": "iOS",
                "browser": "Safari",
                "browser_version": "17.0"
            },
            "geo": {
                "country": "CN",
                "region": "BJ",
                "city": "Beijing"
            },
            "traffic_source": {
                "source": "facebook",
                "medium": "social",
                "campaign": "winter_promotion"
            },
            "event_params": [
                {
                    "key": "method",
                    "value": {"string_value": "email"}
                },
                {
                    "key": "ga_session_id",
                    "value": {"string_value": "session_002"}
                }
            ],
            "user_properties": []
        },
        {
            "event_date": "20241201",
            "event_timestamp": 1733097780000000,
            "event_name": "purchase",
            "user_pseudo_id": "demo_user_001",
            "user_id": "registered_user_001",
            "platform": "WEB",
            "device": {
                "category": "desktop",
                "operating_system": "Windows",
                "browser": "Chrome",
                "browser_version": "120.0.0.0"
            },
            "geo": {
                "country": "US",
                "region": "CA",
                "city": "San Francisco"
            },
            "traffic_source": {
                "source": "google",
                "medium": "organic",
                "campaign": "(not set)"
            },
            "event_params": [
                {
                    "key": "currency",
                    "value": {"string_value": "USD"}
                },
                {
                    "key": "value",
                    "value": {"double_value": 299.99}
                },
                {
                    "key": "transaction_id",
                    "value": {"string_value": "txn_001"}
                },
                {
                    "key": "ga_session_id",
                    "value": {"string_value": "session_001"}
                }
            ],
            "user_properties": [
                {
                    "key": "user_type",
                    "value": {"string_value": "premium"}
                }
            ],
            "items": [
                {
                    "item_id": "premium_plan",
                    "item_name": "高级分析套餐",
                    "item_category": "subscription",
                    "price": 299.99,
                    "quantity": 1
                }
            ]
        },
        {
            "event_date": "20241201",
            "event_timestamp": 1733097840000000,
            "event_name": "search",
            "user_pseudo_id": "demo_user_003",
            "user_id": "guest_user_003",
            "platform": "WEB",
            "device": {
                "category": "tablet",
                "operating_system": "Android",
                "browser": "Chrome",
                "browser_version": "119.0.0.0"
            },
            "geo": {
                "country": "JP",
                "region": "13",
                "city": "Tokyo"
            },
            "traffic_source": {
                "source": "bing",
                "medium": "organic",
                "campaign": "(not set)"
            },
            "event_params": [
                {
                    "key": "search_term",
                    "value": {"string_value": "用户行为分析"}
                },
                {
                    "key": "ga_session_id",
                    "value": {"string_value": "session_003"}
                }
            ],
            "user_properties": [
                {
                    "key": "user_type",
                    "value": {"string_value": "free"}
                }
            ]
        }
    ]
    
    # 创建临时文件
    demo_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ndjson', delete=False, prefix='demo_ga4_')
    for event in demo_events:
        demo_file.write(json.dumps(event, ensure_ascii=False) + '\n')
    demo_file.close()
    
    return demo_file.name


def demo_file_processing():
    """演示文件处理流程"""
    print("🚀 开始演示Streamlit界面文件处理功能")
    print("=" * 60)
    
    # 创建演示文件
    print("📁 创建演示GA4数据文件...")
    demo_file = create_demo_ga4_file()
    file_size = os.path.getsize(demo_file) / 1024  # KB
    print(f"   文件路径: {demo_file}")
    print(f"   文件大小: {file_size:.2f} KB")
    
    try:
        # 初始化组件
        parser = GA4DataParser()
        validator = DataValidator()
        storage_manager = DataStorageManager()
        
        # 步骤1: 文件解析
        print("\n🔍 步骤1: 解析GA4数据文件...")
        raw_data = parser.parse_ndjson(demo_file)
        print(f"   解析结果: {len(raw_data)} 条事件记录")
        print(f"   数据列: {list(raw_data.columns)}")
        
        # 步骤2: 数据验证
        print("\n✅ 步骤2: 验证数据质量...")
        validation_report = validator.validate_dataframe(raw_data)
        print(f"   验证状态: {'通过' if validation_report['validation_passed'] else '失败'}")
        print(f"   错误数量: {len(validation_report.get('errors', []))}")
        print(f"   警告数量: {len(validation_report.get('warnings', []))}")
        
        # 步骤3: 数据处理
        print("\n⚙️ 步骤3: 处理和提取数据...")
        events_data = parser.extract_events(raw_data)
        user_data = parser.extract_user_properties(raw_data)
        session_data = parser.extract_sessions(raw_data)
        
        print(f"   事件类型: {list(events_data.keys())}")
        print(f"   用户数量: {len(user_data)}")
        print(f"   会话数量: {len(session_data)}")
        
        # 步骤4: 数据存储
        print("\n💾 步骤4: 存储处理结果...")
        storage_manager.store_events(raw_data)
        storage_manager.store_users(user_data)
        storage_manager.store_sessions(session_data)
        
        stored_events = storage_manager.get_data('events')
        print(f"   存储事件数: {len(stored_events)}")
        
        # 步骤5: 生成数据摘要
        print("\n📊 步骤5: 生成数据摘要...")
        data_summary = parser.validate_data_quality(raw_data)
        
        print(f"   总事件数: {data_summary['total_events']:,}")
        print(f"   独立用户数: {data_summary['unique_users']:,}")
        print(f"   时间范围: {data_summary['date_range']['start']} - {data_summary['date_range']['end']}")
        print(f"   事件类型: {list(data_summary['event_types'].keys())}")
        print(f"   平台分布: {list(data_summary['platforms'].keys())}")
        
        # 显示详细统计
        print("\n📈 详细统计信息:")
        print("-" * 40)
        
        print("事件类型分布:")
        for event_type, count in data_summary['event_types'].items():
            print(f"  - {event_type}: {count}")
        
        print("\n平台分布:")
        for platform, count in data_summary['platforms'].items():
            print(f"  - {platform}: {count}")
        
        if data_summary.get('data_issues'):
            print("\n⚠️ 数据质量问题:")
            for issue in data_summary['data_issues']:
                print(f"  - {issue}")
        
        print("\n🎉 文件处理演示完成!")
        
    except Exception as e:
        print(f"❌ 处理过程出错: {str(e)}")
        
    finally:
        # 清理临时文件
        if os.path.exists(demo_file):
            os.unlink(demo_file)
            print(f"🗑️ 已清理临时文件: {demo_file}")


def demo_interface_features():
    """演示界面功能特性"""
    print("\n" + "=" * 60)
    print("🎨 Streamlit界面功能特性演示")
    print("=" * 60)
    
    features = [
        {
            "name": "文件上传验证",
            "description": "支持GA4 NDJSON格式文件上传，自动验证文件格式和大小",
            "capabilities": [
                "文件格式检查 (.ndjson, .json, .jsonl)",
                "文件大小限制 (最大100MB)",
                "文件内容预览功能",
                "上传进度显示"
            ]
        },
        {
            "name": "数据处理流水线",
            "description": "自动化的数据解析、验证、清洗和存储流程",
            "capabilities": [
                "GA4事件数据解析",
                "数据质量验证",
                "用户属性提取",
                "会话数据重构",
                "实时进度跟踪"
            ]
        },
        {
            "name": "数据状态管理",
            "description": "智能的会话状态管理和数据缓存机制",
            "capabilities": [
                "会话数据持久化",
                "数据状态显示",
                "一键数据清除",
                "多页面数据共享"
            ]
        },
        {
            "name": "错误处理机制",
            "description": "完善的错误处理和用户友好的错误提示",
            "capabilities": [
                "文件格式错误处理",
                "数据解析错误恢复",
                "详细错误信息显示",
                "处理失败回滚机制"
            ]
        },
        {
            "name": "数据质量报告",
            "description": "全面的数据质量分析和可视化展示",
            "capabilities": [
                "数据完整性检查",
                "统计信息展示",
                "质量问题识别",
                "修复建议提供"
            ]
        }
    ]
    
    for i, feature in enumerate(features, 1):
        print(f"\n{i}. {feature['name']}")
        print(f"   描述: {feature['description']}")
        print("   功能:")
        for capability in feature['capabilities']:
            print(f"     ✓ {capability}")
    
    print("\n🔧 技术实现特点:")
    print("  • 基于Streamlit构建的现代化Web界面")
    print("  • 响应式设计，支持多种设备访问")
    print("  • 模块化架构，易于扩展和维护")
    print("  • 实时数据处理和状态更新")
    print("  • 完善的错误处理和用户反馈")


def demo_usage_workflow():
    """演示使用工作流程"""
    print("\n" + "=" * 60)
    print("📋 用户使用工作流程演示")
    print("=" * 60)
    
    workflow_steps = [
        {
            "step": 1,
            "title": "启动应用",
            "description": "运行 streamlit run main.py 启动应用",
            "details": [
                "系统自动验证配置完整性",
                "初始化会话状态",
                "显示应用主界面"
            ]
        },
        {
            "step": 2,
            "title": "上传数据文件",
            "description": "在'数据上传'页面选择GA4 NDJSON文件",
            "details": [
                "点击文件上传区域",
                "选择.ndjson/.json/.jsonl格式文件",
                "系统自动验证文件大小和格式"
            ]
        },
        {
            "step": 3,
            "title": "预览文件内容",
            "description": "可选择预览文件内容确认数据格式",
            "details": [
                "点击'预览文件'按钮",
                "查看文件前几行内容",
                "确认数据结构正确性"
            ]
        },
        {
            "step": 4,
            "title": "开始数据处理",
            "description": "点击'开始处理'按钮启动数据处理流程",
            "details": [
                "系统显示实时处理进度",
                "自动完成解析、验证、清洗步骤",
                "生成数据质量报告"
            ]
        },
        {
            "step": 5,
            "title": "查看处理结果",
            "description": "查看数据摘要和质量报告",
            "details": [
                "查看基础统计信息",
                "检查数据质量问题",
                "确认数据处理成功"
            ]
        },
        {
            "step": 6,
            "title": "进行数据分析",
            "description": "切换到其他功能模块进行具体分析",
            "details": [
                "事件分析 - 分析用户行为模式",
                "留存分析 - 计算用户留存率",
                "转化分析 - 分析转化漏斗",
                "用户分群 - 智能用户分群",
                "路径分析 - 用户行为路径",
                "综合报告 - 生成分析报告"
            ]
        }
    ]
    
    for step_info in workflow_steps:
        print(f"\n步骤 {step_info['step']}: {step_info['title']}")
        print(f"  {step_info['description']}")
        for detail in step_info['details']:
            print(f"    • {detail}")
    
    print("\n💡 使用提示:")
    print("  • 确保GA4数据文件格式正确")
    print("  • 建议文件大小不超过100MB以获得最佳性能")
    print("  • 处理大文件时请耐心等待")
    print("  • 可随时清除数据重新开始")


if __name__ == "__main__":
    print("🎯 用户行为分析智能体平台 - Streamlit界面演示")
    print("=" * 80)
    
    # 演示文件处理功能
    demo_file_processing()
    
    # 演示界面功能特性
    demo_interface_features()
    
    # 演示使用工作流程
    demo_usage_workflow()
    
    print("\n" + "=" * 80)
    print("✨ 演示完成! 现在可以运行 'streamlit run main.py' 体验完整功能")
    print("=" * 80)