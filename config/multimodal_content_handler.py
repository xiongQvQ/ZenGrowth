"""
多模态内容处理器
支持文本和图片内容的处理、验证和格式化
"""

import logging
import time
import re
import base64
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field

# 设置日志
logger = logging.getLogger(__name__)


class TextContent(BaseModel):
    """文本内容模型"""
    type: Literal["text"]
    text: str


class ImageUrl(BaseModel):
    """图片URL模型"""
    url: str
    detail: Optional[str] = "auto"  # auto, low, high


class ImageContent(BaseModel):
    """图片内容模型"""
    type: Literal["image_url"]
    image_url: ImageUrl


class MultiModalRequest(BaseModel):
    """多模态请求模型"""
    content: List[Union[TextContent, ImageContent]]
    provider: Optional[str] = None
    analysis_type: str
    parameters: Dict[str, Any] = {}


class MultiModalContentHandler:
    """
    多模态内容处理器
    
    支持文本和图片内容的处理、验证和格式化
    可以为不同的LLM提供商格式化内容
    """
    
    def __init__(self, max_image_size_mb: int = 10):
        """
        初始化多模态内容处理器
        
        Args:
            max_image_size_mb: 最大图片大小限制（MB）
        """
        self.max_image_size_mb = max_image_size_mb
        
        # 支持的图片格式
        self.supported_image_formats = {
            'jpeg', 'jpg', 'png', 'gif', 'webp', 'bmp'
        }
        
        # MIME类型映射
        self.supported_mime_types = {
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
            'image/webp', 'image/bmp'
        }
        
        # Data URL正则表达式
        self.data_url_pattern = re.compile(r'^data:image/([^;]+);base64,(.+)$')
        
        # 图片处理配置
        self.max_images_per_request = 10
        self.min_image_dimension = 32  # 最小图片尺寸
        self.max_image_dimension = 4096  # 最大图片尺寸
        
        # 内容验证规则
        self.validation_rules = {
            'require_text_or_image': True,
            'allow_empty_text': True,
            'validate_image_urls': True,
            'check_image_accessibility': False,  # 是否检查图片可访问性
            'strict_mime_type_check': True
        }
    
    def prepare_content(self, content: Union[str, List[Dict], List[Union[TextContent, ImageContent]]]) -> List[Dict[str, Any]]:
        """
        准备多模态内容，转换为标准API格式
        
        Args:
            content: 输入内容，可以是字符串、字典列表或内容对象列表
            
        Returns:
            标准API格式的内容列表
        """
        if isinstance(content, str):
            # 纯文本内容
            return [{"type": "text", "text": content}]
        
        if isinstance(content, list):
            api_content = []
            for item in content:
                if isinstance(item, dict):
                    # 字典格式
                    api_content.append(self._process_dict_content(item))
                elif isinstance(item, (TextContent, ImageContent)):
                    # Pydantic模型
                    api_content.append(self._process_model_content(item))
                else:
                    # 其他类型转为文本
                    api_content.append({"type": "text", "text": str(item)})
            return api_content
        
        # 其他类型转为文本
        return [{"type": "text", "text": str(content)}]
    
    def _process_dict_content(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """处理字典格式的内容"""
        content_type = item.get("type", "text")
        
        if content_type == "text":
            return {
                "type": "text",
                "text": item.get("text", str(item))
            }
        elif content_type == "image_url":
            image_url = item.get("image_url", {})
            if isinstance(image_url, str):
                image_url = {"url": image_url}
            
            return {
                "type": "image_url",
                "image_url": {
                    "url": image_url.get("url", ""),
                    "detail": image_url.get("detail", "auto")
                }
            }
        else:
            # 未知类型转为文本
            return {"type": "text", "text": str(item)}
    
    def _process_model_content(self, item: Union[TextContent, ImageContent]) -> Dict[str, Any]:
        """处理Pydantic模型内容"""
        if isinstance(item, TextContent):
            return {"type": "text", "text": item.text}
        elif isinstance(item, ImageContent):
            return {
                "type": "image_url",
                "image_url": {
                    "url": item.image_url.url,
                    "detail": item.image_url.detail
                }
            }
        else:
            return {"type": "text", "text": str(item)}
    
    def validate_image_url(self, url: str) -> bool:
        """
        验证图片URL格式和有效性
        
        Args:
            url: 图片URL
            
        Returns:
            是否有效
        """
        if not url:
            logger.error("图片URL为空")
            return False
        
        # 检查data URL格式
        if url.startswith("data:"):
            return self._validate_data_url(url)
        
        # 检查HTTP/HTTPS URL格式
        if url.startswith(("http://", "https://")):
            return self._validate_http_url(url)
        
        logger.error(f"不支持的URL格式: {url}")
        return False
    
    def _validate_data_url(self, url: str) -> bool:
        """验证data URL格式"""
        match = self.data_url_pattern.match(url)
        if not match:
            logger.error("无效的data URL格式")
            return False
        
        mime_type, base64_data = match.groups()
        
        # 检查MIME类型
        full_mime_type = f"image/{mime_type}"
        if full_mime_type not in self.supported_mime_types:
            logger.error(f"不支持的MIME类型: {full_mime_type}")
            return False
        
        # 检查base64数据大小
        try:
            # 添加必要的填充
            padded_data = base64_data
            missing_padding = len(padded_data) % 4
            if missing_padding:
                padded_data += '=' * (4 - missing_padding)
            
            decoded_size = len(base64.b64decode(padded_data))
            size_mb = decoded_size / (1024 * 1024)
            if size_mb > self.max_image_size_mb:
                logger.error(f"图片大小超过限制: {size_mb:.2f}MB > {self.max_image_size_mb}MB")
                return False
        except Exception as e:
            logger.error(f"base64解码失败: {e}")
            return False
        
        return True
    
    def _validate_http_url(self, url: str) -> bool:
        """验证HTTP/HTTPS URL格式"""
        try:
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                logger.error("URL格式不完整")
                return False
            
            # 检查文件扩展名
            path = parsed.path.lower()
            if path:
                extension = path.split('.')[-1]
                if extension not in self.supported_image_formats:
                    logger.warning(f"URL可能不是图片文件: {extension}")
            
            return True
        except Exception as e:
            logger.error(f"URL解析失败: {e}")
            return False
    
    def validate_content(self, content: List[Dict[str, Any]]) -> bool:
        """
        验证多模态内容
        
        Args:
            content: 内容列表
            
        Returns:
            是否有效
        """
        if not content:
            logger.error("内容为空")
            return False
        
        has_text = False
        image_count = 0
        
        for item in content:
            content_type = item.get("type")
            
            if content_type == "text":
                text = item.get("text", "")
                if text.strip():
                    has_text = True
            
            elif content_type == "image_url":
                image_url = item.get("image_url", {})
                url = image_url.get("url", "")
                
                if not self.validate_image_url(url):
                    return False
                
                image_count += 1
                
                # 限制图片数量
                if image_count > self.max_images_per_request:
                    logger.error(f"图片数量超过限制: {image_count}")
                    return False
            
            else:
                logger.error(f"不支持的内容类型: {content_type}")
                return False
        
        # 至少需要有文本或图片
        if self.validation_rules['require_text_or_image'] and not has_text and image_count == 0:
            logger.error("内容中没有有效的文本或图片")
            return False
        
        return True
    
    def format_for_provider(self, content: List[Dict[str, Any]], provider: str) -> Any:
        """
        为特定提供商格式化内容
        
        Args:
            content: 标准格式的内容列表
            provider: 提供商名称 (volcano, google)
            
        Returns:
            格式化后的内容
        """
        if provider == "volcano":
            # Volcano使用OpenAI兼容格式
            return self._format_for_volcano(content)
        elif provider == "google":
            # Google Gemini格式
            return self._format_for_google(content)
        else:
            # 默认返回标准格式
            logger.warning(f"未知提供商: {provider}, 使用默认格式")
            return content
    
    def _format_for_volcano(self, content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        为Volcano提供商格式化内容
        
        Args:
            content: 标准格式内容
            
        Returns:
            Volcano格式内容
        """
        # Volcano使用OpenAI兼容格式，直接返回
        return content
    
    def _format_for_google(self, content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        为Google提供商格式化内容
        
        Args:
            content: 标准格式内容
            
        Returns:
            Google格式内容
        """
        # Google Gemini可能需要不同的格式
        # 目前先返回标准格式，后续可根据需要调整
        formatted_content = []
        
        for item in content:
            if item.get("type") == "text":
                formatted_content.append({
                    "type": "text",
                    "text": item.get("text", "")
                })
            elif item.get("type") == "image_url":
                # Google可能需要不同的图片格式
                image_url = item.get("image_url", {})
                formatted_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_url.get("url", ""),
                        "detail": image_url.get("detail", "auto")
                    }
                })
        
        return formatted_content
    
    def detect_content_type(self, content: Union[str, List[Dict], List[Union[TextContent, ImageContent]]]) -> str:
        """
        检测内容类型
        
        Args:
            content: 输入内容
            
        Returns:
            内容类型 (text_only, image_only, multimodal)
        """
        if isinstance(content, str):
            return "text_only"
        
        processed_content = self.prepare_content(content)
        
        has_text = False
        has_image = False
        
        for item in processed_content:
            if item.get("type") == "text":
                text = item.get("text", "")
                if text.strip():
                    has_text = True
            elif item.get("type") == "image_url":
                has_image = True
        
        if has_text and has_image:
            return "multimodal"
        elif has_image:
            return "image_only"
        else:
            return "text_only"
    
    def extract_text_content(self, content: List[Dict[str, Any]]) -> str:
        """
        从多模态内容中提取文本部分
        
        Args:
            content: 内容列表
            
        Returns:
            合并的文本内容
        """
        text_parts = []
        for item in content:
            if item.get("type") == "text":
                text = item.get("text", "")
                if text.strip():
                    text_parts.append(text.strip())
        
        return "\n".join(text_parts)
    
    def get_image_urls(self, content: List[Dict[str, Any]]) -> List[str]:
        """
        从多模态内容中提取图片URL
        
        Args:
            content: 内容列表
            
        Returns:
            图片URL列表
        """
        urls = []
        for item in content:
            if item.get("type") == "image_url":
                image_url = item.get("image_url", {})
                url = image_url.get("url", "")
                if url:
                    urls.append(url)
        
        return urls
    
    def get_content_statistics(self, content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取内容统计信息
        
        Args:
            content: 内容列表
            
        Returns:
            统计信息字典
        """
        stats = {
            "total_items": len(content),
            "text_items": 0,
            "image_items": 0,
            "text_length": 0,
            "image_urls": [],
            "content_types": set(),
            "has_multimodal": False,
            "estimated_tokens": 0
        }
        
        for item in content:
            item_type = item.get("type")
            stats["content_types"].add(item_type)
            
            if item_type == "text":
                stats["text_items"] += 1
                text = item.get("text", "")
                stats["text_length"] += len(text)
                # 粗略估算token数量 (1 token ≈ 4 characters for Chinese)
                stats["estimated_tokens"] += len(text) // 4
                
            elif item_type == "image_url":
                stats["image_items"] += 1
                image_url = item.get("image_url", {})
                url = image_url.get("url", "")
                if url:
                    stats["image_urls"].append(url)
                # 图片大约消耗85个token (根据OpenAI文档)
                stats["estimated_tokens"] += 85
        
        stats["content_types"] = list(stats["content_types"])
        stats["has_multimodal"] = stats["image_items"] > 0
        
        return stats
    
    def validate_content_structure(self, content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证内容结构的完整性
        
        Args:
            content: 内容列表
            
        Returns:
            验证结果字典
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {
                "total_items": len(content),
                "text_items": 0,
                "image_items": 0,
                "invalid_items": 0
            }
        }
        
        if not content:
            validation_result["is_valid"] = False
            validation_result["errors"].append("内容列表为空")
            return validation_result
        
        for i, item in enumerate(content):
            item_type = item.get("type")
            
            if item_type == "text":
                validation_result["statistics"]["text_items"] += 1
                text = item.get("text", "")
                if not text.strip() and not self.validation_rules["allow_empty_text"]:
                    validation_result["warnings"].append(f"第{i+1}项文本内容为空")
                    
            elif item_type == "image_url":
                validation_result["statistics"]["image_items"] += 1
                image_url = item.get("image_url", {})
                url = image_url.get("url", "")
                
                if not url:
                    validation_result["is_valid"] = False
                    validation_result["errors"].append(f"第{i+1}项图片URL为空")
                    validation_result["statistics"]["invalid_items"] += 1
                elif self.validation_rules["validate_image_urls"] and not self.validate_image_url(url):
                    validation_result["is_valid"] = False
                    validation_result["errors"].append(f"第{i+1}项图片URL无效: {url}")
                    validation_result["statistics"]["invalid_items"] += 1
                    
            else:
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"第{i+1}项内容类型无效: {item_type}")
                validation_result["statistics"]["invalid_items"] += 1
        
        # 检查是否至少有文本或图片
        if self.validation_rules["require_text_or_image"]:
            if validation_result["statistics"]["text_items"] == 0 and validation_result["statistics"]["image_items"] == 0:
                validation_result["is_valid"] = False
                validation_result["errors"].append("内容中必须包含至少一个文本或图片项")
        
        # 检查图片数量限制
        if validation_result["statistics"]["image_items"] > self.max_images_per_request:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"图片数量超过限制: {validation_result['statistics']['image_items']} > {self.max_images_per_request}")
        
        return validation_result
    
    def normalize_content(self, content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        标准化内容格式
        
        Args:
            content: 原始内容列表
            
        Returns:
            标准化后的内容列表
        """
        normalized_content = []
        
        for item in content:
            item_type = item.get("type")
            
            if item_type == "text":
                text = item.get("text", "").strip()
                if text or self.validation_rules["allow_empty_text"]:
                    normalized_content.append({
                        "type": "text",
                        "text": text
                    })
                    
            elif item_type == "image_url":
                image_url = item.get("image_url", {})
                url = image_url.get("url", "").strip()
                detail = image_url.get("detail", "auto")
                
                if url:
                    # 标准化detail参数
                    if detail not in {"auto", "low", "high"}:
                        detail = "auto"
                    
                    normalized_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": url,
                            "detail": detail
                        }
                    })
        
        return normalized_content
    
    def create_text_content(self, text: str) -> TextContent:
        """
        创建文本内容对象
        
        Args:
            text: 文本内容
            
        Returns:
            文本内容对象
        """
        return TextContent(type="text", text=text)
    
    def create_image_content(self, url: str, detail: str = "auto") -> ImageContent:
        """
        创建图片内容对象
        
        Args:
            url: 图片URL
            detail: 图片详细程度 (auto, low, high)
            
        Returns:
            图片内容对象
        """
        if not self.validate_image_url(url):
            raise ValueError(f"无效的图片URL: {url}")
        
        return ImageContent(
            type="image_url",
            image_url=ImageUrl(url=url, detail=detail)
        )
    
    def create_multimodal_request(
        self,
        text: Optional[str] = None,
        image_urls: Optional[List[str]] = None,
        analysis_type: str = "general",
        provider: Optional[str] = None,
        **parameters
    ) -> MultiModalRequest:
        """
        创建多模态请求对象
        
        Args:
            text: 文本内容
            image_urls: 图片URL列表
            analysis_type: 分析类型
            provider: 目标提供商
            **parameters: 其他参数
            
        Returns:
            多模态请求对象
        """
        content = []
        
        if text:
            content.append(self.create_text_content(text))
        
        if image_urls:
            for url in image_urls:
                content.append(self.create_image_content(url))
        
        if not content:
            raise ValueError("必须提供文本或图片内容")
        
        return MultiModalRequest(
            content=content,
            provider=provider,
            analysis_type=analysis_type,
            parameters=parameters
        )


# 便利函数
def create_text_content(text: str) -> TextContent:
    """创建文本内容对象"""
    return TextContent(type="text", text=text)


def create_image_content(url: str, detail: str = "auto") -> ImageContent:
    """创建图片内容对象"""
    return ImageContent(
        type="image_url",
        image_url=ImageUrl(url=url, detail=detail)
    )


def create_multimodal_content(text: str, image_urls: List[str]) -> List[Union[TextContent, ImageContent]]:
    """创建混合内容列表"""
    content = [create_text_content(text)]
    for url in image_urls:
        content.append(create_image_content(url))
    return content