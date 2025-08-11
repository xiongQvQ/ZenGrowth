# Volcano多模态分析配置指南

## 📋 概述

本指南详细介绍如何配置和使用Volcano（火山引擎）豆包大模型进行多模态用户行为分析。Volcano API支持文本和图像的混合分析，为用户行为分析提供更丰富的洞察。

## 🚀 快速开始

### 1. 获取API密钥

1. **注册火山引擎账号**
   - 访问 [火山引擎官网](https://www.volcengine.com/)
   - 注册并完成实名认证

2. **开通豆包大模型服务**
   - 登录 [火山引擎控制台](https://console.volcengine.com/)
   - 搜索"豆包大模型"或"ARK"
   - 开通服务并获取API密钥

3. **获取ARK API密钥**
   - 在控制台中创建应用
   - 复制生成的API密钥（格式通常为 `ak-xxxxxx`）

### 2. 环境配置

#### 配置环境变量

在项目根目录的 `.env` 文件中添加以下配置：

```env
# Volcano ARK API配置
ARK_API_KEY=ak-your_actual_api_key_here
ARK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_MODEL=doubao-seed-1-6-250615

# LLM提供商配置
DEFAULT_LLM_PROVIDER=volcano
ENABLED_PROVIDERS=["google", "volcano"]
ENABLE_FALLBACK=true
FALLBACK_ORDER=["volcano", "google"]

# 多模态配置
ENABLE_MULTIMODAL=true
MAX_IMAGE_SIZE_MB=10
SUPPORTED_IMAGE_FORMATS=["jpg", "jpeg", "png", "gif", "webp"]
IMAGE_ANALYSIS_TIMEOUT=120

# 性能优化配置
MULTIMODAL_BATCH_SIZE=5
ENABLE_IMAGE_PREPROCESSING=true
IMAGE_QUALITY_OPTIMIZATION=true
```

#### 验证配置

运行以下命令验证配置是否正确：

```bash
python -c "
from config.volcano_llm_client import VolcanoLLMClient
import os

api_key = os.getenv('ARK_API_KEY')
if api_key:
    print('✅ ARK_API_KEY 已配置')
    client = VolcanoLLMClient(api_key=api_key)
    print('✅ Volcano客户端初始化成功')
else:
    print('❌ ARK_API_KEY 未配置')
"
```

## 🖼️ 多模态分析使用指南

### 基础多模态分析

```python
from config.multimodal_content_handler import MultiModalContentHandler
from config.llm_provider_manager import LLMProviderManager

# 初始化组件
content_handler = MultiModalContentHandler()
provider_manager = LLMProviderManager()

# 获取支持多模态的LLM
llm = provider_manager.get_llm(provider="volcano")

# 准备多模态内容
multimodal_content = [
    {
        "type": "text",
        "text": "请分析这个用户界面截图，识别用户可能的行为模式"
    },
    {
        "type": "image_url",
        "image_url": {
            "url": "https://example.com/user_interface_screenshot.png",
            "detail": "high"  # 可选: auto, low, high
        }
    }
]

# 执行分析
response = llm.invoke(multimodal_content)
print(response)
```

### 高级多模态分析示例

```python
class AdvancedMultiModalAnalyzer:
    """高级多模态分析器"""
    
    def __init__(self):
        self.content_handler = MultiModalContentHandler()
        self.provider_manager = LLMProviderManager()
    
    def analyze_user_journey_with_screenshots(self, journey_data):
        """分析包含截图的用户旅程"""
        
        # 构建分析内容
        content = [
            {
                "type": "text",
                "text": f"""
                用户旅程分析任务：
                用户ID: {journey_data['user_id']}
                会话时长: {journey_data['session_duration']}分钟
                页面访问数: {journey_data['page_views']}
                
                请结合以下截图分析用户行为模式：
                """
            }
        ]
        
        # 添加截图
        for i, screenshot in enumerate(journey_data['screenshots']):
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": screenshot['url'],
                    "detail": "high"
                }
            })
            content.append({
                "type": "text",
                "text": f"截图{i+1}: {screenshot['description']}"
            })
        
        # 添加分析要求
        content.append({
            "type": "text",
            "text": """
            请提供以下分析：
            1. 用户界面交互模式识别
            2. 视觉注意力热点分析
            3. 用户体验问题识别
            4. 转化优化建议
            
            请以JSON格式返回结构化结果。
            """
        })
        
        # 执行分析
        llm = self.provider_manager.get_llm(provider="volcano")
        
        try:
            response = llm.invoke(content)
            return self._parse_analysis_result(response)
        except Exception as e:
            return {"error": f"分析失败: {e}"}
    
    def analyze_product_visual_appeal(self, product_data):
        """分析商品视觉吸引力"""
        
        content = [
            {
                "type": "text",
                "text": f"""
                商品视觉分析任务：
                商品名称: {product_data['name']}
                类别: {product_data['category']}
                价格: {product_data['price']}
                
                请分析以下商品图片的视觉吸引力：
                """
            }
        ]
        
        # 添加商品图片
        for image in product_data['images']:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": image['url'],
                    "detail": "high"
                }
            })
        
        content.append({
            "type": "text",
            "text": """
            请从以下维度分析：
            1. 视觉吸引力评分（1-10分）
            2. 色彩搭配效果
            3. 构图和布局质量
            4. 品牌形象一致性
            5. 目标用户群体匹配度
            6. 改进建议
            
            请以JSON格式返回详细分析结果。
            """
        })
        
        llm = self.provider_manager.get_llm(provider="volcano")
        response = llm.invoke(content)
        return self._parse_analysis_result(response)
    
    def _parse_analysis_result(self, response):
        """解析分析结果"""
        try:
            import json
            import re
            
            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"raw_response": response}
        except Exception as e:
            return {"raw_response": response, "parse_error": str(e)}

# 使用示例
analyzer = AdvancedMultiModalAnalyzer()

# 用户旅程分析
journey_data = {
    "user_id": "user_12345",
    "session_duration": 15,
    "page_views": 8,
    "screenshots": [
        {
            "url": "https://example.com/homepage_screenshot.png",
            "description": "用户首次访问首页"
        },
        {
            "url": "https://example.com/product_page_screenshot.png", 
            "description": "用户浏览商品详情页"
        }
    ]
}

result = analyzer.analyze_user_journey_with_screenshots(journey_data)
print(json.dumps(result, indent=2, ensure_ascii=False))
```

## 🔧 配置优化

### 性能优化配置

```env
# 图片处理优化
IMAGE_PREPROCESSING_ENABLED=true
IMAGE_MAX_DIMENSION=1024
IMAGE_COMPRESSION_QUALITY=85
IMAGE_FORMAT_CONVERSION=true

# 批处理配置
MULTIMODAL_BATCH_SIZE=3
BATCH_PROCESSING_TIMEOUT=300
ENABLE_PARALLEL_PROCESSING=true

# 缓存配置
ENABLE_MULTIMODAL_CACHE=true
CACHE_EXPIRY_HOURS=24
CACHE_MAX_SIZE_MB=500
```

### 错误处理配置

```env
# 重试配置
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=2
EXPONENTIAL_BACKOFF=true

# 降级策略
ENABLE_GRACEFUL_DEGRADATION=true
FALLBACK_TO_TEXT_ONLY=true
SKIP_INVALID_IMAGES=true
```

## 📊 监控和日志

### 启用详细日志

```python
import logging

# 配置多模态分析日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/multimodal_analysis.log'),
        logging.StreamHandler()
    ]
)

# 获取专用日志器
multimodal_logger = logging.getLogger('multimodal_analysis')
```

### 性能监控

```python
import time
from functools import wraps

def monitor_multimodal_performance(func):
    """多模态分析性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            
            execution_time = time.time() - start_time
            multimodal_logger.info(f"多模态分析完成: {func.__name__}, 耗时: {execution_time:.2f}秒")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            multimodal_logger.error(f"多模态分析失败: {func.__name__}, 耗时: {execution_time:.2f}秒, 错误: {e}")
            raise
    
    return wrapper

# 使用示例
@monitor_multimodal_performance
def analyze_with_monitoring(content):
    llm = provider_manager.get_llm(provider="volcano")
    return llm.invoke(content)
```

## 🚨 故障排除

### 常见问题及解决方案

#### 1. API认证失败

**问题**: `Authentication failed with ARK API`

**解决方案**:
```bash
# 检查API密钥格式
echo $ARK_API_KEY | grep -E '^ak-[a-zA-Z0-9]+'

# 测试API连接
curl -H "Authorization: Bearer $ARK_API_KEY" \
     -H "Content-Type: application/json" \
     https://ark.cn-beijing.volces.com/api/v3/models
```

#### 2. 图片处理失败

**问题**: `Image processing failed or timeout`

**解决方案**:
```python
# 图片预处理和验证
from PIL import Image
import requests

def preprocess_image(image_url, max_size=(1024, 1024)):
    """预处理图片"""
    try:
        # 下载图片
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # 打开并处理图片
        with Image.open(BytesIO(response.content)) as img:
            # 转换格式
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 调整大小
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 保存处理后的图片
            output = BytesIO()
            img.save(output, format='JPEG', quality=85)
            
            return output.getvalue()
            
    except Exception as e:
        print(f"图片预处理失败: {e}")
        return None
```

#### 3. 多模态分析超时

**问题**: `Multimodal analysis timeout`

**解决方案**:
```python
# 异步处理大批量多模态内容
import asyncio

async def process_multimodal_async(content_batches):
    """异步处理多模态内容"""
    tasks = []
    
    for batch in content_batches:
        task = asyncio.create_task(process_single_batch(batch))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

async def process_single_batch(batch):
    """处理单个批次"""
    try:
        llm = provider_manager.get_llm(provider="volcano")
        return await llm.ainvoke(batch)  # 异步调用
    except Exception as e:
        return {"error": str(e)}
```

## 📈 最佳实践

### 1. 图片质量优化

```python
def optimize_images_for_analysis(images):
    """优化图片用于分析"""
    optimized_images = []
    
    for image in images:
        # 检查图片大小
        if image['size_mb'] > 5:
            # 压缩大图片
            compressed_url = compress_image(image['url'])
            optimized_images.append({
                **image,
                'url': compressed_url,
                'optimized': True
            })
        else:
            optimized_images.append(image)
    
    return optimized_images
```

### 2. 内容类型检测

```python
def detect_content_types(content_list):
    """检测内容类型并分类处理"""
    text_content = []
    image_content = []
    
    for item in content_list:
        if item['type'] == 'text':
            text_content.append(item)
        elif item['type'] == 'image_url':
            # 验证图片URL
            if validate_image_url(item['image_url']['url']):
                image_content.append(item)
            else:
                print(f"跳过无效图片: {item['image_url']['url']}")
    
    return text_content, image_content
```

### 3. 结果缓存策略

```python
import hashlib
import json

def cache_multimodal_results(content, result, cache_duration=3600):
    """缓存多模态分析结果"""
    # 生成内容哈希作为缓存键
    content_hash = hashlib.md5(
        json.dumps(content, sort_keys=True).encode()
    ).hexdigest()
    
    cache_key = f"multimodal_analysis:{content_hash}"
    
    # 存储到缓存（这里使用Redis示例）
    import redis
    r = redis.Redis()
    r.setex(cache_key, cache_duration, json.dumps(result))
    
    return cache_key
```

## 📚 API参考

### MultiModalContentHandler

```python
class MultiModalContentHandler:
    """多模态内容处理器"""
    
    def prepare_content(self, content: List[Dict]) -> List[Dict]:
        """准备多模态内容"""
        pass
    
    def validate_image_url(self, url: str) -> bool:
        """验证图片URL"""
        pass
    
    def format_for_provider(self, content: List[Dict], provider: str) -> Any:
        """为特定提供商格式化内容"""
        pass
```

### VolcanoLLMClient

```python
class VolcanoLLMClient:
    """Volcano LLM客户端"""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        """初始化客户端"""
        pass
    
    def invoke(self, content: Union[str, List[Dict]]) -> str:
        """同步调用"""
        pass
    
    async def ainvoke(self, content: Union[str, List[Dict]]) -> str:
        """异步调用"""
        pass
    
    def supports_multimodal(self) -> bool:
        """检查是否支持多模态"""
        return True
```

---

## 📞 获取帮助

如果在配置或使用过程中遇到问题：

1. **查看日志**: 检查 `logs/multimodal_analysis.log`
2. **运行诊断**: 使用 `demo_volcano_multimodal_usage.py` 进行测试
3. **检查配置**: 验证所有环境变量是否正确设置
4. **联系支持**: 提交详细的错误信息和配置信息

**常用诊断命令**:
```bash
# 检查环境变量
env | grep -E "(ARK_|MULTIMODAL|VOLCANO)"

# 测试API连接
python demo_volcano_multimodal_usage.py

# 查看详细日志
tail -f logs/multimodal_analysis.log
```

---

*本配置指南持续更新中，如有疑问或建议，欢迎反馈。*