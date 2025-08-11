# 示例和最佳实践文档

## 📋 概述

本文档提供用户行为分析智能体平台的实际使用示例、最佳实践和高级用法指南。通过具体的代码示例和业务场景，帮助用户更好地理解和使用平台功能。

## 🎯 使用场景示例

### 1. 多模态用户行为分析

#### 业务背景
某电商平台希望结合用户上传的商品图片和行为数据，分析用户对不同商品类型的偏好，优化商品推荐算法。

#### 多模态数据准备
```python
# 多模态分析数据结构
multimodal_data = {
    "text_content": "用户浏览了运动鞋商品页面，停留时间3分钟，查看了5张商品图片",
    "image_content": [
        {
            "type": "image_url",
            "image_url": {
                "url": "https://example.com/product_images/sneaker_1.jpg",
                "detail": "high"
            }
        },
        {
            "type": "image_url", 
            "image_url": {
                "url": "https://example.com/user_uploads/style_preference.jpg",
                "detail": "auto"
            }
        }
    ],
    "user_behavior": {
        "page_views": 15,
        "time_on_page": 180,
        "scroll_depth": 0.85,
        "click_events": ["zoom_image", "color_selection", "size_guide"]
    }
}
```

#### 多模态分析实现
```python
from config.multimodal_content_handler import MultiModalContentHandler
from config.llm_provider_manager import LLMProviderManager

class MultiModalAnalyzer:
    """多模态分析器"""
    
    def __init__(self):
        self.content_handler = MultiModalContentHandler()
        self.provider_manager = LLMProviderManager()
    
    def analyze_user_preferences(self, multimodal_data, provider="volcano"):
        """分析用户偏好（支持多模态）"""
        
        # 1. 准备多模态内容
        content = self._prepare_multimodal_content(multimodal_data)
        
        # 2. 选择支持多模态的提供商
        llm = self.provider_manager.get_llm(provider=provider)
        
        if not llm.supports_multimodal():
            # 降级到文本分析
            return self._fallback_to_text_analysis(multimodal_data)
        
        # 3. 构建分析提示
        analysis_prompt = self._build_multimodal_prompt(content)
        
        # 4. 执行多模态分析
        try:
            result = llm.invoke(analysis_prompt)
            return self._parse_analysis_result(result)
        except Exception as e:
            print(f"多模态分析失败，降级到文本分析: {e}")
            return self._fallback_to_text_analysis(multimodal_data)
    
    def _prepare_multimodal_content(self, data):
        """准备多模态内容"""
        content = []
        
        # 添加文本内容
        if "text_content" in data:
            content.append({
                "type": "text",
                "text": data["text_content"]
            })
        
        # 添加图片内容
        if "image_content" in data:
            for image in data["image_content"]:
                # 验证图片URL
                if self.content_handler.validate_image_url(image["image_url"]["url"]):
                    content.append(image)
                else:
                    print(f"跳过无效图片: {image['image_url']['url']}")
        
        # 添加行为数据作为文本
        if "user_behavior" in data:
            behavior_text = self._format_behavior_data(data["user_behavior"])
            content.append({
                "type": "text", 
                "text": f"用户行为数据: {behavior_text}"
            })
        
        return content
    
    def _build_multimodal_prompt(self, content):
        """构建多模态分析提示"""
        return [
            {
                "role": "system",
                "content": """你是一个专业的用户行为分析师。请分析提供的多模态数据（包括文本描述、图片和行为数据），
                识别用户偏好模式，并提供以下分析：
                1. 用户兴趣类别识别
                2. 视觉偏好分析（基于图片内容）
                3. 行为模式总结
                4. 个性化推荐建议
                
                请以JSON格式返回结构化的分析结果。"""
            },
            {
                "role": "user", 
                "content": content
            }
        ]
    
    def _parse_analysis_result(self, result):
        """解析分析结果"""
        try:
            import json
            # 尝试解析JSON结果
            if isinstance(result, str):
                # 提取JSON部分
                json_start = result.find('{')
                json_end = result.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = result[json_start:json_end]
                    return json.loads(json_str)
            
            return {"raw_result": result}
        except Exception as e:
            return {
                "error": f"结果解析失败: {e}",
                "raw_result": result
            }

# 使用示例
analyzer = MultiModalAnalyzer()

# 执行多模态分析
preferences = analyzer.analyze_user_preferences(
    multimodal_data, 
    provider="volcano"  # 使用支持多模态的Volcano提供商
)

print("用户偏好分析结果:")
print(json.dumps(preferences, indent=2, ensure_ascii=False))
```

#### 多模态可视化
```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_multimodal_dashboard(analysis_results, images):
    """创建多模态分析仪表板"""
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('用户兴趣分布', '视觉偏好热力图', '行为时间线', '推荐匹配度'),
        specs=[[{"type": "pie"}, {"type": "heatmap"}],
               [{"type": "scatter"}, {"type": "bar"}]]
    )
    
    # 1. 兴趣分布饼图
    if "interest_categories" in analysis_results:
        categories = analysis_results["interest_categories"]
        fig.add_trace(
            go.Pie(
                labels=list(categories.keys()),
                values=list(categories.values()),
                name="兴趣分布"
            ),
            row=1, col=1
        )
    
    # 2. 视觉偏好热力图
    if "visual_preferences" in analysis_results:
        visual_data = analysis_results["visual_preferences"]
        fig.add_trace(
            go.Heatmap(
                z=visual_data.get("preference_matrix", []),
                x=visual_data.get("attributes", []),
                y=visual_data.get("categories", []),
                colorscale="Viridis"
            ),
            row=1, col=2
        )
    
    # 3. 行为时间线
    if "behavior_timeline" in analysis_results:
        timeline = analysis_results["behavior_timeline"]
        fig.add_trace(
            go.Scatter(
                x=timeline.get("timestamps", []),
                y=timeline.get("engagement_scores", []),
                mode='lines+markers',
                name="参与度变化"
            ),
            row=2, col=1
        )
    
    # 4. 推荐匹配度
    if "recommendations" in analysis_results:
        recommendations = analysis_results["recommendations"]
        fig.add_trace(
            go.Bar(
                x=[rec["name"] for rec in recommendations],
                y=[rec["match_score"] for rec in recommendations],
                name="推荐匹配度"
            ),
            row=2, col=2
        )
    
    # 更新布局
    fig.update_layout(
        title="多模态用户行为分析仪表板",
        height=800,
        showlegend=True
    )
    
    return fig

# 创建仪表板
dashboard = create_multimodal_dashboard(preferences, multimodal_data["image_content"])
dashboard.show()
```

### 2. 电商网站用户行为分析

#### 业务背景
某电商网站希望分析用户从浏览商品到完成购买的完整行为路径，识别转化瓶颈并优化用户体验。

#### 数据准备
```python
# 示例GA4事件数据结构
sample_events = [
    {
        "event_date": "20240115",
        "event_timestamp": 1705123200000000,
        "event_name": "page_view",
        "user_pseudo_id": "user_12345",
        "event_params": [
            {"key": "page_title", "value": {"string_value": "商品详情页"}},
            {"key": "page_location", "value": {"string_value": "/product/123"}}
        ]
    },
    {
        "event_date": "20240115", 
        "event_timestamp": 1705123260000000,
        "event_name": "add_to_cart",
        "user_pseudo_id": "user_12345",
        "event_params": [
            {"key": "item_id", "value": {"string_value": "product_123"}},
            {"key": "value", "value": {"double_value": 99.99}}
        ]
    },
    {
        "event_date": "20240115",
        "event_timestamp": 1705123320000000, 
        "event_name": "purchase",
        "user_pseudo_id": "user_12345",
        "event_params": [
            {"key": "transaction_id", "value": {"string_value": "txn_789"}},
            {"key": "value", "value": {"double_value": 99.99}}
        ]
    }
]
```

#### 分析流程
```python
from tools.ga4_data_parser import GA4DataParser
from engines.conversion_analysis_engine import ConversionAnalysisEngine
from engines.path_analysis_engine import PathAnalysisEngine
from visualization.chart_generator import ChartGenerator

# 1. 数据解析和预处理
parser = GA4DataParser()
data = parser.parse_ndjson('ecommerce_data.ndjson')
events = parser.extract_events(data)

# 2. 定义转化漏斗
funnel_steps = [
    'page_view',      # 浏览商品
    'add_to_cart',    # 加入购物车
    'begin_checkout', # 开始结账
    'purchase'        # 完成购买
]

# 3. 转化分析
conversion_engine = ConversionAnalysisEngine(storage_manager)
funnel_data = conversion_engine.build_conversion_funnel(
    funnel_steps=funnel_steps,
    conversion_window_hours=24
)

conversion_rates = conversion_engine.calculate_conversion_rates(funnel_data)
bottlenecks = conversion_engine.identify_conversion_bottlenecks(funnel_data)

# 4. 用户路径分析
path_engine = PathAnalysisEngine(storage_manager)
user_paths = path_engine.extract_user_paths(
    min_path_length=2,
    max_path_length=10
)

common_paths = path_engine.find_common_paths(
    user_paths,
    min_support=0.05
)

# 5. 可视化结果
chart_gen = ChartGenerator()
funnel_chart = chart_gen.create_conversion_funnel(
    funnel_data,
    title="电商转化漏斗分析"
)

path_chart = chart_gen.create_user_flow_diagram(
    common_paths,
    title="用户行为路径图"
)
```

#### 业务洞察
```python
def generate_ecommerce_insights(conversion_rates, bottlenecks, common_paths):
    """生成电商业务洞察"""
    insights = []
    
    # 转化率分析
    overall_conversion = conversion_rates.get('overall_conversion', 0)
    if overall_conversion < 0.02:  # 低于2%
        insights.append({
            'type': 'conversion_optimization',
            'priority': 'high',
            'message': f'整体转化率仅为{overall_conversion:.2%}，建议优化购买流程',
            'recommendations': [
                '简化结账流程',
                '优化支付页面设计',
                '提供多种支付方式',
                '增加信任标识'
            ]
        })
    
    # 瓶颈识别
    for bottleneck in bottlenecks:
        if bottleneck['drop_rate'] > 0.5:  # 流失率超过50%
            insights.append({
                'type': 'bottleneck_alert',
                'priority': 'high',
                'message': f'{bottleneck["step"]}步骤流失率高达{bottleneck["drop_rate"]:.1%}',
                'recommendations': [
                    f'重点优化{bottleneck["step"]}页面体验',
                    '分析用户在该步骤的具体行为',
                    '进行A/B测试验证优化效果'
                ]
            })
    
    # 路径优化
    bounce_paths = [path for path in common_paths if len(path['events']) == 1]
    if len(bounce_paths) > len(common_paths) * 0.3:  # 跳出路径超过30%
        insights.append({
            'type': 'engagement_optimization',
            'priority': 'medium',
            'message': '用户跳出率较高，需要提升页面吸引力',
            'recommendations': [
                '优化首页内容布局',
                '增加相关商品推荐',
                '改进页面加载速度',
                '优化移动端体验'
            ]
        })
    
    return insights
```

### 2. SaaS产品用户留存分析

#### 业务背景
某SaaS产品希望分析新用户的留存情况，识别影响用户留存的关键因素。

#### 分析实现
```python
from engines.retention_analysis_engine import RetentionAnalysisEngine
from engines.user_segmentation_engine import UserSegmentationEngine
from datetime import datetime, timedelta

# 1. 构建用户队列
retention_engine = RetentionAnalysisEngine(storage_manager)

# 按周构建新用户队列
cohorts = retention_engine.build_user_cohorts(
    cohort_type='weekly',
    date_range=('2024-01-01', '2024-03-31')
)

# 2. 计算留存率
retention_periods = [1, 7, 14, 30, 60, 90]  # 天数
retention_rates = retention_engine.calculate_retention_rates(
    cohorts, 
    periods=retention_periods
)

# 3. 用户分群分析
segmentation_engine = UserSegmentationEngine(storage_manager)

# 基于使用行为进行分群
user_features = segmentation_engine.extract_user_features([
    'session_frequency',    # 会话频率
    'feature_usage_depth',  # 功能使用深度
    'support_interactions', # 客服交互次数
    'onboarding_completion' # 入门流程完成度
])

clusters = segmentation_engine.perform_clustering(
    user_features,
    n_clusters=4,
    method='kmeans'
)

# 4. 留存驱动因素分析
def analyze_retention_drivers(retention_data, user_segments):
    """分析留存驱动因素"""
    drivers = {}
    
    for segment_id, segment_users in user_segments.items():
        segment_retention = retention_data[
            retention_data['user_id'].isin(segment_users)
        ]
        
        # 计算各时期留存率
        segment_rates = {}
        for period in retention_periods:
            period_retention = segment_retention[
                segment_retention['period'] == period
            ]['retained'].mean()
            segment_rates[f'day_{period}'] = period_retention
        
        drivers[f'segment_{segment_id}'] = {
            'retention_rates': segment_rates,
            'user_count': len(segment_users),
            'characteristics': get_segment_characteristics(segment_id)
        }
    
    return drivers

def get_segment_characteristics(segment_id):
    """获取用户群体特征"""
    characteristics = {
        0: {
            'name': '高活跃用户',
            'traits': ['频繁使用核心功能', '完成入门流程', '很少联系客服'],
            'retention_pattern': '高留存，稳定使用'
        },
        1: {
            'name': '探索型用户', 
            'traits': ['尝试多种功能', '中等使用频率', '偶尔寻求帮助'],
            'retention_pattern': '中等留存，需要引导'
        },
        2: {
            'name': '困难用户',
            'traits': ['使用频率低', '经常联系客服', '入门流程未完成'],
            'retention_pattern': '低留存，需要重点关注'
        },
        3: {
            'name': '试用用户',
            'traits': ['短期使用', '功能使用浅', '快速流失'],
            'retention_pattern': '极低留存，需要激活策略'
        }
    }
    return characteristics.get(segment_id, {})
```

#### 留存优化策略
```python
def generate_retention_strategies(retention_drivers):
    """生成留存优化策略"""
    strategies = []
    
    for segment, data in retention_drivers.items():
        day_7_retention = data['retention_rates'].get('day_7', 0)
        day_30_retention = data['retention_rates'].get('day_30', 0)
        
        if day_7_retention < 0.4:  # 7天留存低于40%
            strategies.append({
                'segment': segment,
                'priority': 'urgent',
                'focus': '早期激活',
                'actions': [
                    '优化用户入门流程',
                    '发送个性化引导邮件',
                    '提供一对一产品演示',
                    '简化核心功能使用路径'
                ],
                'metrics': ['入门完成率', '首次价值实现时间', '7天活跃率']
            })
        
        if day_30_retention < 0.2:  # 30天留存低于20%
            strategies.append({
                'segment': segment,
                'priority': 'high',
                'focus': '价值传递',
                'actions': [
                    '推送成功案例和最佳实践',
                    '提供高级功能培训',
                    '建立用户社区',
                    '定期发送价值报告'
                ],
                'metrics': ['功能采用率', '用户满意度', '30天留存率']
            })
    
    return strategies
```

### 3. 内容平台用户参与度分析

#### 业务背景
某内容平台希望分析用户的内容消费行为，优化内容推荐算法和用户体验。

#### 分析实现
```python
from engines.event_analysis_engine import EventAnalysisEngine
from engines.path_analysis_engine import PathAnalysisEngine

# 1. 内容消费事件分析
event_engine = EventAnalysisEngine(storage_manager)

# 定义内容相关事件
content_events = [
    'page_view',      # 页面浏览
    'video_start',    # 视频开始播放
    'video_progress', # 视频播放进度
    'video_complete', # 视频播放完成
    'like',          # 点赞
    'share',         # 分享
    'comment',       # 评论
    'subscribe'      # 订阅
]

# 分析事件频次和趋势
event_frequency = event_engine.analyze_event_frequency(
    event_types=content_events,
    granularity='hour'  # 按小时分析
)

event_trends = event_engine.analyze_event_trends(
    event_types=content_events,
    window_size=24  # 24小时滑动窗口
)

# 2. 内容消费路径分析
path_engine = PathAnalysisEngine(storage_manager)

# 提取用户内容消费路径
consumption_paths = path_engine.extract_user_paths(
    event_filter=content_events,
    session_timeout_minutes=60,  # 1小时会话超时
    min_path_length=3
)

# 识别高价值路径
high_value_paths = path_engine.identify_high_value_paths(
    consumption_paths,
    value_events=['like', 'share', 'comment', 'subscribe'],
    min_value_score=2.0
)

# 3. 用户参与度分群
def calculate_engagement_metrics(user_events):
    """计算用户参与度指标"""
    metrics = {}
    
    for user_id, events in user_events.groupby('user_pseudo_id'):
        user_metrics = {
            'session_count': len(events['session_id'].unique()),
            'total_events': len(events),
            'content_views': len(events[events['event_name'] == 'page_view']),
            'video_starts': len(events[events['event_name'] == 'video_start']),
            'video_completion_rate': calculate_video_completion_rate(events),
            'interaction_rate': calculate_interaction_rate(events),
            'avg_session_duration': calculate_avg_session_duration(events),
            'content_diversity': calculate_content_diversity(events)
        }
        metrics[user_id] = user_metrics
    
    return pd.DataFrame.from_dict(metrics, orient='index')

def calculate_video_completion_rate(user_events):
    """计算视频完成率"""
    video_starts = len(user_events[user_events['event_name'] == 'video_start'])
    video_completes = len(user_events[user_events['event_name'] == 'video_complete'])
    
    if video_starts == 0:
        return 0
    return video_completes / video_starts

def calculate_interaction_rate(user_events):
    """计算互动率"""
    total_views = len(user_events[user_events['event_name'] == 'page_view'])
    interactions = len(user_events[
        user_events['event_name'].isin(['like', 'share', 'comment'])
    ])
    
    if total_views == 0:
        return 0
    return interactions / total_views
```

#### 内容推荐优化
```python
def optimize_content_recommendation(engagement_metrics, consumption_paths):
    """优化内容推荐策略"""
    recommendations = {}
    
    # 基于用户参与度分群
    high_engagement = engagement_metrics[
        (engagement_metrics['interaction_rate'] > 0.1) &
        (engagement_metrics['video_completion_rate'] > 0.7)
    ]
    
    medium_engagement = engagement_metrics[
        (engagement_metrics['interaction_rate'] > 0.05) &
        (engagement_metrics['video_completion_rate'] > 0.4)
    ]
    
    low_engagement = engagement_metrics[
        (engagement_metrics['interaction_rate'] <= 0.05) |
        (engagement_metrics['video_completion_rate'] <= 0.4)
    ]
    
    # 为不同群体制定推荐策略
    recommendations['high_engagement'] = {
        'strategy': '深度内容推荐',
        'content_types': ['长视频', '专业内容', '系列内容'],
        'recommendation_count': 10,
        'personalization_weight': 0.8,
        'diversity_weight': 0.2
    }
    
    recommendations['medium_engagement'] = {
        'strategy': '兴趣探索推荐',
        'content_types': ['中等长度视频', '热门内容', '相关推荐'],
        'recommendation_count': 8,
        'personalization_weight': 0.6,
        'diversity_weight': 0.4
    }
    
    recommendations['low_engagement'] = {
        'strategy': '激活式推荐',
        'content_types': ['短视频', '热门内容', '新手友好内容'],
        'recommendation_count': 6,
        'personalization_weight': 0.3,
        'diversity_weight': 0.7
    }
    
    return recommendations
```

## 🏆 最佳实践

### 1. 数据质量管理

#### 数据验证最佳实践
```python
from tools.data_validator import DataValidator
import pandas as pd

class AdvancedDataValidator(DataValidator):
    """高级数据验证器"""
    
    def validate_business_logic(self, data: pd.DataFrame) -> dict:
        """验证业务逻辑"""
        issues = []
        
        # 1. 时间逻辑验证
        time_issues = self._validate_time_logic(data)
        issues.extend(time_issues)
        
        # 2. 事件序列验证
        sequence_issues = self._validate_event_sequences(data)
        issues.extend(sequence_issues)
        
        # 3. 数值合理性验证
        value_issues = self._validate_value_ranges(data)
        issues.extend(value_issues)
        
        return {
            'validation_passed': len(issues) == 0,
            'issues': issues,
            'recommendations': self._generate_fix_recommendations(issues)
        }
    
    def _validate_time_logic(self, data: pd.DataFrame) -> list:
        """验证时间逻辑"""
        issues = []
        
        # 检查未来时间戳
        current_timestamp = pd.Timestamp.now().timestamp() * 1000000
        future_events = data[data['event_timestamp'] > current_timestamp]
        if not future_events.empty:
            issues.append({
                'type': 'future_timestamp',
                'count': len(future_events),
                'severity': 'high',
                'message': f'发现{len(future_events)}个未来时间戳事件'
            })
        
        # 检查时间戳顺序
        for user_id in data['user_pseudo_id'].unique():
            user_events = data[data['user_pseudo_id'] == user_id].sort_values('event_timestamp')
            if not user_events['event_timestamp'].is_monotonic_increasing:
                issues.append({
                    'type': 'timestamp_order',
                    'user_id': user_id,
                    'severity': 'medium',
                    'message': f'用户{user_id}的事件时间戳顺序异常'
                })
        
        return issues
    
    def _validate_event_sequences(self, data: pd.DataFrame) -> list:
        """验证事件序列"""
        issues = []
        
        # 定义合理的事件序列规则
        sequence_rules = {
            'purchase_without_view': {
                'condition': lambda df: (df['event_name'] == 'purchase') & 
                           (~df['user_pseudo_id'].isin(
                               df[df['event_name'] == 'page_view']['user_pseudo_id']
                           )),
                'message': '发现没有页面浏览就直接购买的异常行为'
            },
            'add_to_cart_without_view': {
                'condition': lambda df: (df['event_name'] == 'add_to_cart') &
                           (~df['user_pseudo_id'].isin(
                               df[df['event_name'] == 'page_view']['user_pseudo_id']
                           )),
                'message': '发现没有页面浏览就加购物车的异常行为'
            }
        }
        
        for rule_name, rule in sequence_rules.items():
            violations = data[rule['condition'](data)]
            if not violations.empty:
                issues.append({
                    'type': 'sequence_violation',
                    'rule': rule_name,
                    'count': len(violations),
                    'severity': 'medium',
                    'message': rule['message']
                })
        
        return issues
```

#### 数据清洗最佳实践
```python
class SmartDataCleaner:
    """智能数据清洗器"""
    
    def __init__(self):
        self.cleaning_rules = self._load_cleaning_rules()
    
    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """智能数据清洗"""
        cleaned_data = data.copy()
        
        # 1. 去除重复事件
        cleaned_data = self._remove_duplicate_events(cleaned_data)
        
        # 2. 修复时间戳格式
        cleaned_data = self._fix_timestamp_format(cleaned_data)
        
        # 3. 标准化事件名称
        cleaned_data = self._standardize_event_names(cleaned_data)
        
        # 4. 填充缺失值
        cleaned_data = self._fill_missing_values(cleaned_data)
        
        # 5. 过滤异常值
        cleaned_data = self._filter_outliers(cleaned_data)
        
        return cleaned_data
    
    def _remove_duplicate_events(self, data: pd.DataFrame) -> pd.DataFrame:
        """去除重复事件"""
        # 基于用户ID、事件名称和时间戳去重
        duplicate_columns = ['user_pseudo_id', 'event_name', 'event_timestamp']
        
        # 保留最后一个重复事件
        cleaned = data.drop_duplicates(
            subset=duplicate_columns,
            keep='last'
        )
        
        removed_count = len(data) - len(cleaned)
        if removed_count > 0:
            print(f"已移除 {removed_count} 个重复事件")
        
        return cleaned
    
    def _standardize_event_names(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化事件名称"""
        # 事件名称映射规则
        event_mapping = {
            'pageview': 'page_view',
            'page-view': 'page_view',
            'click': 'click_event',
            'btn_click': 'click_event',
            'purchase_complete': 'purchase',
            'buy': 'purchase',
            'signup': 'sign_up',
            'register': 'sign_up'
        }
        
        data['event_name'] = data['event_name'].replace(event_mapping)
        return data
```

### 2. 性能优化最佳实践

#### 大数据处理优化
```python
import dask.dataframe as dd
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp

class HighPerformanceAnalyzer:
    """高性能分析器"""
    
    def __init__(self, max_workers=None):
        self.max_workers = max_workers or mp.cpu_count()
    
    def process_large_dataset(self, file_path: str, chunk_size: int = 100000):
        """处理大型数据集"""
        # 使用Dask进行并行处理
        ddf = dd.read_json(file_path, lines=True, blocksize="100MB")
        
        # 并行执行基础统计
        results = {
            'total_events': len(ddf),
            'unique_users': ddf['user_pseudo_id'].nunique().compute(),
            'event_types': ddf['event_name'].value_counts().compute(),
            'date_range': {
                'start': ddf['event_date'].min().compute(),
                'end': ddf['event_date'].max().compute()
            }
        }
        
        return results
    
    def parallel_analysis(self, data_chunks: list, analysis_func):
        """并行分析执行"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_chunk = {
                executor.submit(analysis_func, chunk): chunk 
                for chunk in data_chunks
            }
            
            # 收集结果
            for future in as_completed(future_to_chunk):
                chunk = future_to_chunk[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as exc:
                    print(f'数据块分析失败: {exc}')
        
        return results
    
    def optimize_memory_usage(self, data: pd.DataFrame) -> pd.DataFrame:
        """优化内存使用"""
        # 优化数据类型
        for col in data.columns:
            if data[col].dtype == 'object':
                # 尝试转换为category类型
                if data[col].nunique() / len(data) < 0.5:
                    data[col] = data[col].astype('category')
            elif data[col].dtype == 'int64':
                # 尝试使用更小的整数类型
                if data[col].min() >= 0:
                    if data[col].max() < 255:
                        data[col] = data[col].astype('uint8')
                    elif data[col].max() < 65535:
                        data[col] = data[col].astype('uint16')
                    elif data[col].max() < 4294967295:
                        data[col] = data[col].astype('uint32')
        
        return data
```

#### 缓存策略优化
```python
import redis
import pickle
import hashlib
from functools import wraps

class AdvancedCache:
    """高级缓存管理器"""
    
    def __init__(self, redis_url='redis://localhost:6379/0'):
        self.redis_client = redis.from_url(redis_url)
        self.default_ttl = 3600  # 1小时
    
    def cache_result(self, ttl=None, key_prefix=''):
        """结果缓存装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                cache_key = self._generate_cache_key(
                    func.__name__, args, kwargs, key_prefix
                )
                
                # 尝试从缓存获取
                cached_result = self._get_from_cache(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # 执行函数并缓存结果
                result = func(*args, **kwargs)
                self._set_to_cache(cache_key, result, ttl or self.default_ttl)
                
                return result
            return wrapper
        return decorator
    
    def _generate_cache_key(self, func_name, args, kwargs, prefix):
        """生成缓存键"""
        # 创建参数的哈希值
        params_str = f"{args}_{kwargs}"
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        
        return f"{prefix}:{func_name}:{params_hash}"
    
    def _get_from_cache(self, key):
        """从缓存获取数据"""
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return pickle.loads(cached_data)
        except Exception as e:
            print(f"缓存读取失败: {e}")
        return None
    
    def _set_to_cache(self, key, value, ttl):
        """设置缓存数据"""
        try:
            serialized_data = pickle.dumps(value)
            self.redis_client.setex(key, ttl, serialized_data)
        except Exception as e:
            print(f"缓存写入失败: {e}")

# 使用示例
cache = AdvancedCache()

@cache.cache_result(ttl=7200, key_prefix='event_analysis')
def analyze_events_cached(data, event_types):
    """带缓存的事件分析"""
    # 执行耗时的事件分析
    return perform_event_analysis(data, event_types)
```

### 3. 智能体开发最佳实践

#### 自定义智能体工具开发
```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class AdvancedAnalysisTool(BaseTool):
    """高级分析工具基类"""
    
    name: str = "advanced_analysis_tool"
    description: str = "执行高级数据分析任务"
    
    def __init__(self, storage_manager, config: Dict[str, Any] = None):
        super().__init__()
        self.storage_manager = storage_manager
        self.config = config or {}
        self.cache = {}
    
    def _run(self, **kwargs) -> Dict[str, Any]:
        """工具执行入口"""
        try:
            # 参数验证
            validated_params = self._validate_parameters(kwargs)
            
            # 检查缓存
            cache_key = self._generate_cache_key(validated_params)
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # 执行分析
            result = self._execute_analysis(validated_params)
            
            # 缓存结果
            self.cache[cache_key] = result
            
            # 后处理
            processed_result = self._post_process_result(result)
            
            return processed_result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'recommendations': self._get_error_recommendations(e)
            }
    
    def _validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """参数验证"""
        # 实现具体的参数验证逻辑
        return params
    
    def _execute_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行分析逻辑"""
        raise NotImplementedError("子类必须实现此方法")
    
    def _post_process_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """结果后处理"""
        # 添加元数据
        result['metadata'] = {
            'tool_name': self.name,
            'execution_time': self._get_execution_time(),
            'data_quality_score': self._calculate_data_quality_score(result)
        }
        
        # 生成洞察
        result['insights'] = self._generate_insights(result)
        
        return result
    
    def _generate_insights(self, result: Dict[str, Any]) -> List[str]:
        """生成业务洞察"""
        insights = []
        
        # 基于结果生成洞察
        # 这里可以使用规则引擎或机器学习模型
        
        return insights

class CustomEventAnalysisTool(AdvancedAnalysisTool):
    """自定义事件分析工具"""
    
    name: str = "custom_event_analysis"
    description: str = "执行自定义事件分析，包括高级统计和模式识别"
    
    def _execute_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行事件分析"""
        event_types = params.get('event_types', [])
        date_range = params.get('date_range')
        
        # 获取数据
        events_data = self.storage_manager.get_events({
            'event_names': event_types,
            'date_range': date_range
        })
        
        # 执行分析
        results = {
            'basic_stats': self._calculate_basic_stats(events_data),
            'trend_analysis': self._analyze_trends(events_data),
            'pattern_detection': self._detect_patterns(events_data),
            'anomaly_detection': self._detect_anomalies(events_data)
        }
        
        return results
    
    def _detect_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        """模式检测"""
        patterns = {}
        
        # 时间模式检测
        data['hour'] = pd.to_datetime(data['event_timestamp'], unit='us').dt.hour
        hourly_pattern = data.groupby('hour')['event_name'].count()
        
        patterns['hourly_distribution'] = {
            'peak_hours': hourly_pattern.nlargest(3).index.tolist(),
            'low_hours': hourly_pattern.nsmallest(3).index.tolist(),
            'pattern_strength': self._calculate_pattern_strength(hourly_pattern)
        }
        
        # 用户行为模式
        user_patterns = data.groupby('user_pseudo_id')['event_name'].apply(list)
        common_sequences = self._find_common_sequences(user_patterns)
        
        patterns['behavior_sequences'] = common_sequences
        
        return patterns
```

#### 智能体协作优化
```python
from config.crew_config import CrewManager
from typing import Dict, List

class OptimizedCrewManager(CrewManager):
    """优化的智能体团队管理器"""
    
    def __init__(self):
        super().__init__()
        self.execution_history = []
        self.performance_metrics = {}
    
    def execute_with_monitoring(self, inputs: dict = None):
        """带监控的执行"""
        import time
        
        start_time = time.time()
        
        try:
            # 执行前检查
            self._pre_execution_check()
            
            # 执行任务
            result = self.execute(inputs)
            
            # 记录执行历史
            execution_time = time.time() - start_time
            self._record_execution(result, execution_time, success=True)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._record_execution(str(e), execution_time, success=False)
            raise
    
    def _pre_execution_check(self):
        """执行前检查"""
        # 检查智能体状态
        for agent_type, agent in self.agents.items():
            if not self._check_agent_health(agent):
                raise RuntimeError(f"智能体 {agent_type} 状态异常")
        
        # 检查资源可用性
        if not self._check_resource_availability():
            raise RuntimeError("系统资源不足")
    
    def _check_agent_health(self, agent) -> bool:
        """检查智能体健康状态"""
        # 实现智能体健康检查逻辑
        return True
    
    def _record_execution(self, result, execution_time, success):
        """记录执行历史"""
        record = {
            'timestamp': pd.Timestamp.now(),
            'execution_time': execution_time,
            'success': success,
            'result_summary': self._summarize_result(result) if success else result
        }
        
        self.execution_history.append(record)
        
        # 更新性能指标
        self._update_performance_metrics(record)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        if not self.execution_history:
            return {'message': '暂无执行历史'}
        
        df = pd.DataFrame(self.execution_history)
        
        return {
            'total_executions': len(df),
            'success_rate': df['success'].mean(),
            'avg_execution_time': df['execution_time'].mean(),
            'recent_performance': df.tail(10)['success'].mean(),
            'performance_trend': self._calculate_performance_trend(df)
        }
```

### 4. 可视化最佳实践

#### 响应式图表设计
```python
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class ResponsiveChartGenerator:
    """响应式图表生成器"""
    
    def __init__(self):
        self.default_config = {
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d']
        }
        
        self.theme_colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e', 
            'success': '#2ca02c',
            'warning': '#d62728',
            'info': '#9467bd'
        }
    
    def create_adaptive_dashboard(self, data: Dict[str, pd.DataFrame]) -> go.Figure:
        """创建自适应仪表板"""
        # 根据数据量自动选择图表类型
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('事件趋势', '用户分布', '转化漏斗', '留存热力图'),
            specs=[[{"secondary_y": True}, {"type": "pie"}],
                   [{"type": "funnel"}, {"type": "heatmap"}]]
        )
        
        # 事件趋势图
        if 'events' in data and len(data['events']) > 0:
            trend_data = self._prepare_trend_data(data['events'])
            fig.add_trace(
                go.Scatter(
                    x=trend_data['date'],
                    y=trend_data['count'],
                    mode='lines+markers',
                    name='事件数量',
                    line=dict(color=self.theme_colors['primary'])
                ),
                row=1, col=1
            )
        
        # 用户分布饼图
        if 'users' in data:
            user_dist = self._prepare_user_distribution(data['users'])
            fig.add_trace(
                go.Pie(
                    labels=user_dist['category'],
                    values=user_dist['count'],
                    name="用户分布"
                ),
                row=1, col=2
            )
        
        # 转化漏斗
        if 'conversion' in data:
            funnel_data = data['conversion']
            fig.add_trace(
                go.Funnel(
                    y=funnel_data['step'],
                    x=funnel_data['users'],
                    name="转化漏斗"
                ),
                row=2, col=1
            )
        
        # 留存热力图
        if 'retention' in data:
            retention_data = data['retention']
            fig.add_trace(
                go.Heatmap(
                    z=retention_data.values,
                    x=retention_data.columns,
                    y=retention_data.index,
                    colorscale='RdYlBu_r',
                    name="留存率"
                ),
                row=2, col=2
            )
        
        # 更新布局
        fig.update_layout(
            height=800,
            showlegend=True,
            title_text="用户行为分析仪表板",
            title_x=0.5
        )
        
        return fig
    
    def create_mobile_optimized_chart(self, data: pd.DataFrame, chart_type: str) -> go.Figure:
        """创建移动端优化图表"""
        fig = None
        
        if chart_type == 'line':
            fig = px.line(
                data, 
                x='date', 
                y='value',
                title='趋势分析'
            )
        elif chart_type == 'bar':
            fig = px.bar(
                data,
                x='category',
                y='value', 
                title='分类统计'
            )
        
        if fig:
            # 移动端优化设置
            fig.update_layout(
                font_size=14,
                margin=dict(l=20, r=20, t=40, b=20),
                height=400,
                showlegend=False if len(data.columns) > 5 else True
            )
            
            # 简化工具栏
            fig.update_layout(
                config={
                    'displayModeBar': True,
                    'displaylogo': False,
                    'modeBarButtonsToRemove': [
                        'pan2d', 'lasso2d', 'zoom2d', 'zoomIn2d', 'zoomOut2d'
                    ]
                }
            )
        
        return fig
```

## 📊 业务场景模板

### 1. 电商转化优化模板
```python
def ecommerce_conversion_analysis_template():
    """电商转化分析模板"""
    return {
        'analysis_steps': [
            {
                'step': 'data_preparation',
                'description': '准备电商事件数据',
                'required_events': ['page_view', 'add_to_cart', 'begin_checkout', 'purchase'],
                'data_quality_checks': ['timestamp_validation', 'user_id_consistency', 'event_sequence_validation']
            },
            {
                'step': 'funnel_analysis', 
                'description': '构建转化漏斗',
                'parameters': {
                    'conversion_window_hours': 24,
                    'attribution_model': 'first_touch',
                    'min_users_per_step': 100
                }
            },
            {
                'step': 'bottleneck_identification',
                'description': '识别转化瓶颈',
                'thresholds': {
                    'drop_rate_alert': 0.5,
                    'conversion_rate_warning': 0.02
                }
            },
            {
                'step': 'segment_analysis',
                'description': '分群转化分析',
                'segments': ['new_users', 'returning_users', 'mobile_users', 'desktop_users']
            }
        ],
        'kpis': [
            'overall_conversion_rate',
            'step_conversion_rates', 
            'average_time_to_convert',
            'revenue_per_visitor'
        ],
        'visualizations': [
            'conversion_funnel_chart',
            'conversion_rate_trend',
            'segment_comparison_chart',
            'bottleneck_heatmap'
        ]
    }
```

### 2. SaaS用户激活模板
```python
def saas_user_activation_template():
    """SaaS用户激活分析模板"""
    return {
        'activation_events': [
            'sign_up',
            'email_verification', 
            'profile_completion',
            'first_feature_use',
            'tutorial_completion',
            'first_value_achievement'
        ],
        'analysis_framework': {
            'time_to_activation': {
                'measurement': 'hours_from_signup_to_first_value',
                'target': '<24 hours',
                'segments': ['trial_users', 'paid_users']
            },
            'activation_funnel': {
                'steps': ['signup', 'verification', 'onboarding', 'first_use', 'value_realization'],
                'success_criteria': 'completion_of_all_steps_within_7_days'
            },
            'feature_adoption': {
                'core_features': ['feature_a', 'feature_b', 'feature_c'],
                'adoption_threshold': 'use_within_first_week'
            }
        },
        'optimization_strategies': [
            'onboarding_flow_optimization',
            'email_sequence_improvement', 
            'in_app_guidance_enhancement',
            'feature_discovery_improvement'
        ]
    }
```

## 🎓 学习资源

### 推荐阅读
1. **数据分析基础**
   - 《Python数据分析实战》
   - 《用户行为数据分析》
   - 《增长黑客》

2. **机器学习应用**
   - 《机器学习实战》
   - 《用户画像：方法论与工程化解决方案》

3. **业务分析**
   - 《精益数据分析》
   - 《数据驱动增长》

### 在线课程
- Coursera: Data Analysis and Visualization
- edX: Introduction to Analytics Modeling
- Udacity: Data Analyst Nanodegree

### 实践项目
1. **个人项目**: 分析自己的网站或应用数据
2. **开源贡献**: 参与相关开源项目
3. **案例研究**: 复现知名公司的分析案例

---

*本示例和最佳实践文档将持续更新，欢迎社区贡献更多实用案例和经验分享。*