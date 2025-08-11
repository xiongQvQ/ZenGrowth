"""
测试数据生成器
为智能体兼容性测试生成模拟的GA4数据
"""

import json
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid


def generate_test_ga4_data(num_users: int = 100, num_events: int = 1000) -> Dict[str, Any]:
    """
    生成测试用的GA4数据
    
    Args:
        num_users: 用户数量
        num_events: 事件数量
        
    Returns:
        包含用户和事件数据的字典
    """
    users = generate_test_users(num_users)
    events = generate_test_events(num_events, users)
    
    return {
        "users": users,
        "events": events,
        "summary": {
            "total_users": len(users),
            "total_events": len(events),
            "date_range": {
                "start": (datetime.now() - timedelta(days=30)).isoformat(),
                "end": datetime.now().isoformat()
            }
        }
    }


def generate_test_users(num_users: int = 100) -> List[Dict[str, Any]]:
    """
    生成测试用户数据
    
    Args:
        num_users: 用户数量
        
    Returns:
        用户数据列表
    """
    users = []
    
    for i in range(num_users):
        user_id = f"user_{i:04d}"
        
        # 随机用户属性
        user_type = random.choice(["new", "returning", "loyal"])
        device_category = random.choice(["desktop", "mobile", "tablet"])
        country = random.choice(["CN", "US", "JP", "UK", "DE"])
        
        user = {
            "user_id": user_id,
            "user_pseudo_id": str(uuid.uuid4()),
            "first_visit_date": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
            "user_properties": {
                "user_type": user_type,
                "device_category": device_category,
                "country": country,
                "age_group": random.choice(["18-24", "25-34", "35-44", "45-54", "55+"]),
                "gender": random.choice(["male", "female", "unknown"]),
                "interests": random.sample([
                    "technology", "sports", "travel", "food", "fashion", 
                    "music", "books", "movies", "gaming", "fitness"
                ], k=random.randint(1, 3))
            }
        }
        
        users.append(user)
    
    return users


def generate_test_events(num_events: int = 1000, users: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    生成测试事件数据
    
    Args:
        num_events: 事件数量
        users: 用户数据列表
        
    Returns:
        事件数据列表
    """
    if users is None:
        users = generate_test_users(50)
    
    events = []
    
    # 定义事件类型和参数
    event_types = {
        "page_view": {
            "page_title": ["首页", "产品页", "关于我们", "联系我们", "购物车"],
            "page_location": ["/", "/products", "/about", "/contact", "/cart"],
            "engagement_time_msec": lambda: random.randint(5000, 300000)
        },
        "purchase": {
            "currency": "CNY",
            "value": lambda: round(random.uniform(50, 2000), 2),
            "transaction_id": lambda: f"txn_{random.randint(100000, 999999)}",
            "items": lambda: generate_purchase_items()
        },
        "add_to_cart": {
            "currency": "CNY", 
            "value": lambda: round(random.uniform(20, 500), 2),
            "items": lambda: generate_cart_items()
        },
        "view_item": {
            "currency": "CNY",
            "value": lambda: round(random.uniform(20, 500), 2),
            "item_id": lambda: f"item_{random.randint(1000, 9999)}",
            "item_name": lambda: random.choice([
                "智能手机", "笔记本电脑", "运动鞋", "咖啡机", "书籍", 
                "耳机", "背包", "手表", "相机", "游戏机"
            ])
        },
        "search": {
            "search_term": lambda: random.choice([
                "手机", "电脑", "鞋子", "咖啡", "书", "耳机", "包", "手表", "相机", "游戏"
            ])
        },
        "login": {
            "method": lambda: random.choice(["email", "google", "facebook", "wechat"])
        },
        "sign_up": {
            "method": lambda: random.choice(["email", "google", "facebook", "wechat"])
        },
        "share": {
            "content_type": lambda: random.choice(["product", "article", "video"]),
            "item_id": lambda: f"content_{random.randint(1000, 9999)}"
        }
    }
    
    for i in range(num_events):
        user = random.choice(users)
        event_name = random.choice(list(event_types.keys()))
        event_params = event_types[event_name].copy()
        
        # 处理参数中的函数
        processed_params = {}
        for key, value in event_params.items():
            if callable(value):
                processed_params[key] = value()
            else:
                processed_params[key] = value
        
        # 生成事件时间戳
        event_timestamp = datetime.now() - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        event = {
            "event_name": event_name,
            "event_timestamp": int(event_timestamp.timestamp() * 1000000),  # 微秒时间戳
            "event_date": event_timestamp.strftime("%Y%m%d"),
            "user_id": user["user_id"],
            "user_pseudo_id": user["user_pseudo_id"],
            "event_params": processed_params,
            "user_properties": user["user_properties"],
            "device": {
                "category": user["user_properties"]["device_category"],
                "operating_system": random.choice(["Android", "iOS", "Windows", "macOS"]),
                "browser": random.choice(["Chrome", "Safari", "Firefox", "Edge"])
            },
            "geo": {
                "country": user["user_properties"]["country"],
                "city": generate_city_for_country(user["user_properties"]["country"])
            },
            "traffic_source": {
                "source": random.choice(["google", "direct", "facebook", "email", "referral"]),
                "medium": random.choice(["organic", "cpc", "social", "email", "referral"]),
                "campaign": random.choice(["summer_sale", "new_product", "brand_awareness", "(not set)"])
            }
        }
        
        events.append(event)
    
    # 按时间戳排序
    events.sort(key=lambda x: x["event_timestamp"])
    
    return events


def generate_purchase_items() -> List[Dict[str, Any]]:
    """生成购买商品列表"""
    num_items = random.randint(1, 5)
    items = []
    
    for i in range(num_items):
        item = {
            "item_id": f"item_{random.randint(1000, 9999)}",
            "item_name": random.choice([
                "智能手机", "笔记本电脑", "运动鞋", "咖啡机", "书籍",
                "耳机", "背包", "手表", "相机", "游戏机"
            ]),
            "item_category": random.choice([
                "电子产品", "服装", "家居", "图书", "运动", "美妆", "食品"
            ]),
            "price": round(random.uniform(20, 1000), 2),
            "quantity": random.randint(1, 3)
        }
        items.append(item)
    
    return items


def generate_cart_items() -> List[Dict[str, Any]]:
    """生成购物车商品列表"""
    return generate_purchase_items()  # 复用购买商品生成逻辑


def generate_city_for_country(country: str) -> str:
    """根据国家生成城市"""
    cities = {
        "CN": ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"],
        "US": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia"],
        "JP": ["Tokyo", "Osaka", "Kyoto", "Yokohama", "Kobe", "Nagoya"],
        "UK": ["London", "Manchester", "Birmingham", "Liverpool", "Leeds", "Sheffield"],
        "DE": ["Berlin", "Munich", "Hamburg", "Cologne", "Frankfurt", "Stuttgart"]
    }
    
    return random.choice(cities.get(country, ["Unknown City"]))


def generate_retention_cohort_data() -> Dict[str, Any]:
    """生成留存分析测试数据"""
    cohort_data = {}
    
    # 生成过去12个月的队列数据
    for month in range(12):
        cohort_date = datetime.now() - timedelta(days=30 * month)
        cohort_name = cohort_date.strftime("%Y-%m")
        
        # 初始用户数
        initial_users = random.randint(500, 2000)
        
        # 生成各期留存数据
        retention_data = {
            "cohort_date": cohort_name,
            "initial_users": initial_users,
            "retention": {}
        }
        
        # 计算各期留存用户数（递减）
        current_users = initial_users
        for period in range(min(month + 1, 12)):  # 最多12期数据
            # 留存率逐期递减
            retention_rate = max(0.3, 1.0 - period * 0.1 - random.uniform(0, 0.1))
            retained_users = int(current_users * retention_rate)
            
            retention_data["retention"][f"period_{period}"] = {
                "users": retained_users,
                "rate": retained_users / initial_users
            }
            
            current_users = retained_users
        
        cohort_data[cohort_name] = retention_data
    
    return cohort_data


def generate_conversion_funnel_data() -> Dict[str, Any]:
    """生成转化漏斗测试数据"""
    # 定义漏斗步骤
    funnel_steps = [
        {"name": "访问网站", "users": 10000},
        {"name": "浏览产品", "users": 6000},
        {"name": "查看详情", "users": 3000},
        {"name": "加入购物车", "users": 1500},
        {"name": "开始结账", "users": 800},
        {"name": "完成支付", "users": 400}
    ]
    
    # 计算转化率
    for i, step in enumerate(funnel_steps):
        if i == 0:
            step["conversion_rate"] = 1.0
        else:
            step["conversion_rate"] = step["users"] / funnel_steps[0]["users"]
            step["step_conversion_rate"] = step["users"] / funnel_steps[i-1]["users"]
    
    return {
        "funnel_name": "购买转化漏斗",
        "steps": funnel_steps,
        "overall_conversion_rate": funnel_steps[-1]["users"] / funnel_steps[0]["users"],
        "total_drop_off": funnel_steps[0]["users"] - funnel_steps[-1]["users"]
    }


def generate_user_segmentation_data() -> Dict[str, Any]:
    """生成用户分群测试数据"""
    segments = {
        "高价值用户": {
            "count": 500,
            "characteristics": {
                "avg_order_value": 800,
                "purchase_frequency": 5.2,
                "lifetime_value": 4000,
                "retention_rate": 0.85
            },
            "behaviors": ["frequent_purchaser", "high_spender", "loyal_customer"]
        },
        "活跃用户": {
            "count": 1500,
            "characteristics": {
                "avg_order_value": 300,
                "purchase_frequency": 2.8,
                "lifetime_value": 840,
                "retention_rate": 0.65
            },
            "behaviors": ["regular_visitor", "moderate_spender", "engaged_user"]
        },
        "潜在用户": {
            "count": 3000,
            "characteristics": {
                "avg_order_value": 150,
                "purchase_frequency": 1.2,
                "lifetime_value": 180,
                "retention_rate": 0.35
            },
            "behaviors": ["occasional_visitor", "price_sensitive", "needs_nurturing"]
        },
        "流失风险用户": {
            "count": 800,
            "characteristics": {
                "avg_order_value": 200,
                "purchase_frequency": 0.5,
                "lifetime_value": 100,
                "retention_rate": 0.15
            },
            "behaviors": ["declining_engagement", "long_absence", "at_risk"]
        }
    }
    
    return segments


def generate_path_analysis_data() -> Dict[str, Any]:
    """生成路径分析测试数据"""
    paths = [
        {
            "path": ["首页", "产品列表", "产品详情", "购买"],
            "users": 1200,
            "conversion_rate": 0.15,
            "avg_time": 480  # 秒
        },
        {
            "path": ["首页", "搜索", "产品详情", "购买"],
            "users": 800,
            "conversion_rate": 0.25,
            "avg_time": 320
        },
        {
            "path": ["首页", "分类页", "产品详情", "离开"],
            "users": 2000,
            "conversion_rate": 0.05,
            "avg_time": 180
        },
        {
            "path": ["首页", "关于我们", "离开"],
            "users": 500,
            "conversion_rate": 0.01,
            "avg_time": 60
        },
        {
            "path": ["首页", "产品列表", "购物车", "结账", "购买"],
            "users": 600,
            "conversion_rate": 0.20,
            "avg_time": 600
        }
    ]
    
    return {
        "total_sessions": sum(p["users"] for p in paths),
        "paths": paths,
        "top_exit_pages": ["产品详情", "购物车", "首页"],
        "top_entry_pages": ["首页", "产品列表", "搜索结果"]
    }


def save_test_data_to_file(filename: str = "test_data.json"):
    """将测试数据保存到文件"""
    test_data = {
        "ga4_data": generate_test_ga4_data(),
        "retention_data": generate_retention_cohort_data(),
        "conversion_data": generate_conversion_funnel_data(),
        "segmentation_data": generate_user_segmentation_data(),
        "path_data": generate_path_analysis_data()
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    print(f"测试数据已保存到 {filename}")
    return test_data


if __name__ == "__main__":
    # 生成并保存测试数据
    data = save_test_data_to_file("tests/test_data.json")
    
    print("生成的测试数据统计:")
    print(f"- 用户数: {len(data['ga4_data']['users'])}")
    print(f"- 事件数: {len(data['ga4_data']['events'])}")
    print(f"- 留存队列数: {len(data['retention_data'])}")
    print(f"- 转化步骤数: {len(data['conversion_data']['steps'])}")
    print(f"- 用户分群数: {len(data['segmentation_data'])}")
    print(f"- 用户路径数: {len(data['path_data']['paths'])}")