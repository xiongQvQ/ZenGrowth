"""
Volcano (火山引擎) Doubao LLM客户端实现
基于OpenAI兼容API的LangChain集成
"""

import logging
import time
import re
import base64
import random
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional, Union, Iterator, Literal
from pydantic import Field, BaseModel
from enum import Enum

from langchain_core.language_models.llms import LLM
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.outputs import LLMResult, Generation
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from pydantic import model_validator

try:
    from openai import OpenAI
    from openai.types.chat import ChatCompletion
    from openai import APIError, APIConnectionError, RateLimitError, APITimeoutError, AuthenticationError
except ImportError:
    raise ImportError(
        "OpenAI package not found. Please install it with: pip install openai>=1.0.0"
    )

from config.settings import settings, get_ark_api_key
from config.multimodal_content_handler import (
    MultiModalContentHandler,
    TextContent,
    ImageContent,
    ImageUrl,
    MultiModalRequest
)

# 设置日志
logger = logging.getLogger(__name__)


class VolcanoErrorType(Enum):
    """Volcano API错误类型枚举"""
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    API_CONNECTION_ERROR = "api_connection_error"
    API_TIMEOUT_ERROR = "api_timeout_error"
    CONTENT_FILTER_ERROR = "content_filter_error"
    MODEL_OVERLOADED_ERROR = "model_overloaded_error"
    INVALID_REQUEST_ERROR = "invalid_request_error"
    QUOTA_EXCEEDED_ERROR = "quota_exceeded_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


class VolcanoAPIException(Exception):
    """Volcano API自定义异常类"""
    
    def __init__(
        self,
        message: str,
        error_type: VolcanoErrorType,
        original_error: Optional[Exception] = None,
        retry_after: Optional[int] = None,
        request_id: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.original_error = original_error
        self.retry_after = retry_after
        self.request_id = request_id
        self.status_code = status_code
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "message": self.message,
            "error_type": self.error_type.value,
            "original_error": str(self.original_error) if self.original_error else None,
            "retry_after": self.retry_after,
            "request_id": self.request_id,
            "status_code": self.status_code,
            "timestamp": self.timestamp
        }
    
    def __str__(self) -> str:
        return f"VolcanoAPIException({self.error_type.value}): {self.message}"


class RetryConfig(BaseModel):
    """重试配置"""
    max_retries: int = Field(default=3, ge=0, le=10)
    base_delay: float = Field(default=1.0, ge=0.1, le=60.0)
    max_delay: float = Field(default=60.0, ge=1.0, le=300.0)
    exponential_base: float = Field(default=2.0, ge=1.1, le=10.0)
    jitter: bool = Field(default=True)
    retry_on_timeout: bool = Field(default=True)
    retry_on_connection_error: bool = Field(default=True)
    retry_on_rate_limit: bool = Field(default=True)
    retry_on_server_error: bool = Field(default=True)


class ErrorHandler:
    """Volcano API错误处理器"""
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        self.retry_config = retry_config or RetryConfig()
        self.error_counts = {}
        self.last_errors = {}
    
    def classify_error(self, error: Exception) -> VolcanoErrorType:
        """
        分类错误类型
        
        Args:
            error: 原始异常
            
        Returns:
            错误类型
        """
        if isinstance(error, AuthenticationError):
            return VolcanoErrorType.AUTHENTICATION_ERROR
        elif isinstance(error, RateLimitError):
            return VolcanoErrorType.RATE_LIMIT_ERROR
        elif isinstance(error, APITimeoutError):
            return VolcanoErrorType.API_TIMEOUT_ERROR
        elif isinstance(error, APIConnectionError):
            return VolcanoErrorType.API_CONNECTION_ERROR
        elif isinstance(error, APIError):
            # 根据状态码进一步分类
            if hasattr(error, 'status_code'):
                status_code = error.status_code
                if status_code == 429:
                    return VolcanoErrorType.RATE_LIMIT_ERROR
                elif status_code == 401:
                    return VolcanoErrorType.AUTHENTICATION_ERROR
                elif status_code == 403:
                    return VolcanoErrorType.QUOTA_EXCEEDED_ERROR
                elif status_code == 400:
                    return VolcanoErrorType.INVALID_REQUEST_ERROR
                elif status_code == 503:
                    return VolcanoErrorType.MODEL_OVERLOADED_ERROR
                elif 500 <= status_code < 600:
                    return VolcanoErrorType.API_CONNECTION_ERROR
            
            # 根据错误消息进一步分类
            error_msg = str(error).lower()
            if "content filter" in error_msg or "safety" in error_msg:
                return VolcanoErrorType.CONTENT_FILTER_ERROR
            elif "quota" in error_msg or "limit" in error_msg:
                return VolcanoErrorType.QUOTA_EXCEEDED_ERROR
            elif "overloaded" in error_msg or "busy" in error_msg:
                return VolcanoErrorType.MODEL_OVERLOADED_ERROR
            
            return VolcanoErrorType.UNKNOWN_ERROR
        else:
            # 网络相关错误
            error_msg = str(error).lower()
            if any(keyword in error_msg for keyword in ["connection", "network", "dns", "timeout"]):
                return VolcanoErrorType.NETWORK_ERROR
            
            return VolcanoErrorType.UNKNOWN_ERROR
    
    def should_retry(self, error_type: VolcanoErrorType, attempt: int) -> bool:
        """
        判断是否应该重试
        
        Args:
            error_type: 错误类型
            attempt: 当前尝试次数
            
        Returns:
            是否应该重试
        """
        if attempt >= self.retry_config.max_retries:
            return False
        
        # 根据错误类型决定是否重试
        retry_map = {
            VolcanoErrorType.RATE_LIMIT_ERROR: self.retry_config.retry_on_rate_limit,
            VolcanoErrorType.API_TIMEOUT_ERROR: self.retry_config.retry_on_timeout,
            VolcanoErrorType.API_CONNECTION_ERROR: self.retry_config.retry_on_connection_error,
            VolcanoErrorType.NETWORK_ERROR: self.retry_config.retry_on_connection_error,
            VolcanoErrorType.MODEL_OVERLOADED_ERROR: self.retry_config.retry_on_server_error,
            VolcanoErrorType.AUTHENTICATION_ERROR: False,  # 认证错误不重试
            VolcanoErrorType.QUOTA_EXCEEDED_ERROR: False,  # 配额错误不重试
            VolcanoErrorType.CONTENT_FILTER_ERROR: False,  # 内容过滤错误不重试
            VolcanoErrorType.INVALID_REQUEST_ERROR: False,  # 无效请求不重试
        }
        
        return retry_map.get(error_type, False)
    
    def calculate_delay(self, attempt: int, error_type: VolcanoErrorType, retry_after: Optional[int] = None) -> float:
        """
        计算重试延迟时间
        
        Args:
            attempt: 当前尝试次数
            error_type: 错误类型
            retry_after: 服务器建议的重试时间
            
        Returns:
            延迟时间（秒）
        """
        if retry_after is not None:
            # 使用服务器建议的重试时间
            delay = min(retry_after, self.retry_config.max_delay)
        else:
            # 指数退避
            delay = self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt)
            delay = min(delay, self.retry_config.max_delay)
        
        # 添加抖动以避免雷群效应
        if self.retry_config.jitter:
            jitter_range = delay * 0.1  # 10%的抖动
            delay += random.uniform(-jitter_range, jitter_range)
        
        # 对于速率限制错误，使用更长的延迟
        if error_type == VolcanoErrorType.RATE_LIMIT_ERROR:
            delay = max(delay, 5.0)  # 至少等待5秒
        
        return max(delay, 0.1)  # 最小延迟0.1秒
    
    def create_exception(self, error: Exception, error_type: VolcanoErrorType) -> VolcanoAPIException:
        """
        创建自定义异常
        
        Args:
            error: 原始异常
            error_type: 错误类型
            
        Returns:
            自定义异常
        """
        # 提取错误信息
        message = str(error)
        retry_after = None
        request_id = None
        status_code = None
        
        if hasattr(error, 'response') and error.response:
            # 提取HTTP响应信息
            if hasattr(error.response, 'status_code'):
                status_code = error.response.status_code
            
            if hasattr(error.response, 'headers'):
                headers = error.response.headers
                retry_after = headers.get('Retry-After')
                if retry_after:
                    try:
                        retry_after = int(retry_after)
                    except ValueError:
                        retry_after = None
                
                request_id = headers.get('X-Request-ID') or headers.get('Request-ID')
        
        return VolcanoAPIException(
            message=message,
            error_type=error_type,
            original_error=error,
            retry_after=retry_after,
            request_id=request_id,
            status_code=status_code
        )
    
    def log_error(self, exception: VolcanoAPIException, attempt: int, will_retry: bool):
        """
        记录错误日志
        
        Args:
            exception: 异常对象
            attempt: 尝试次数
            will_retry: 是否会重试
        """
        error_info = {
            "error_type": exception.error_type.value,
            "message": exception.message,
            "attempt": attempt,
            "will_retry": will_retry,
            "request_id": exception.request_id,
            "status_code": exception.status_code,
            "timestamp": exception.timestamp
        }
        
        if will_retry:
            logger.warning(f"Volcano API错误 (将重试): {error_info}")
        else:
            logger.error(f"Volcano API错误 (不重试): {error_info}")
        
        # 更新错误统计
        error_key = exception.error_type.value
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.last_errors[error_key] = exception.timestamp
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        获取错误统计信息
        
        Returns:
            错误统计字典
        """
        return {
            "error_counts": self.error_counts.copy(),
            "last_errors": self.last_errors.copy(),
            "retry_config": self.retry_config.model_dump()
        }


# 多模态内容模型已移至 config.multimodal_content_handler


class MultiModalContentHandler:
    """多模态内容处理器"""
    
    def __init__(self, max_image_size_mb: int = 10):
        self.max_image_size_mb = max_image_size_mb
        self.supported_image_formats = {
            'jpeg', 'jpg', 'png', 'gif', 'webp', 'bmp'
        }
        # MIME类型映射
        self.supported_mime_types = {
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
            'image/webp', 'image/bmp'
        }
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
        准备多模态内容，转换为API格式
        
        Args:
            content: 输入内容，可以是字符串、字典列表或内容对象列表
            
        Returns:
            API格式的内容列表
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
            decoded_size = len(base64.b64decode(base64_data))
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
                
                # 限制图片数量（可配置）
                if image_count > 10:  # 最多10张图片
                    logger.error(f"图片数量超过限制: {image_count}")
                    return False
            
            else:
                logger.error(f"不支持的内容类型: {content_type}")
                return False
        
        # 至少需要有文本或图片
        if not has_text and image_count == 0:
            logger.error("内容中没有有效的文本或图片")
            return False
        
        return True
    
    def process_image_url(self, url: str, detail: str = "auto") -> Dict[str, Any]:
        """
        处理图片URL，进行增强验证和格式化
        
        Args:
            url: 图片URL
            detail: 图片详细程度 (auto, low, high)
            
        Returns:
            处理后的图片内容字典
        """
        if not self.validate_image_url(url):
            raise ValueError(f"无效的图片URL: {url}")
        
        # 标准化detail参数
        valid_details = {"auto", "low", "high"}
        if detail not in valid_details:
            logger.warning(f"无效的detail参数: {detail}, 使用默认值 'auto'")
            detail = "auto"
        
        # 获取图片信息
        image_info = self.get_image_info(url)
        
        return {
            "type": "image_url",
            "image_url": {
                "url": url,
                "detail": detail
            },
            "metadata": image_info
        }
    
    def get_image_info(self, url: str) -> Dict[str, Any]:
        """
        获取图片信息
        
        Args:
            url: 图片URL
            
        Returns:
            图片信息字典
        """
        info = {
            "url": url,
            "type": "unknown",
            "size_mb": None,
            "format": None,
            "is_data_url": False,
            "is_valid": False
        }
        
        try:
            if url.startswith("data:"):
                info.update(self._analyze_data_url(url))
            elif url.startswith(("http://", "https://")):
                info.update(self._analyze_http_url(url))
            
            info["is_valid"] = self.validate_image_url(url)
        except Exception as e:
            logger.error(f"分析图片URL失败: {e}")
            info["error"] = str(e)
        
        return info
    
    def _analyze_data_url(self, url: str) -> Dict[str, Any]:
        """分析data URL"""
        info = {"is_data_url": True, "type": "data_url"}
        
        match = self.data_url_pattern.match(url)
        if match:
            mime_type, base64_data = match.groups()
            info["format"] = mime_type
            
            try:
                decoded_size = len(base64.b64decode(base64_data))
                info["size_mb"] = decoded_size / (1024 * 1024)
            except Exception as e:
                info["decode_error"] = str(e)
        
        return info
    
    def _analyze_http_url(self, url: str) -> Dict[str, Any]:
        """分析HTTP URL"""
        info = {"is_data_url": False, "type": "http_url"}
        
        try:
            parsed = urlparse(url)
            info["domain"] = parsed.netloc
            info["path"] = parsed.path
            
            # 尝试从路径提取格式
            if parsed.path:
                extension = parsed.path.split('.')[-1].lower()
                if extension in self.supported_image_formats:
                    info["format"] = extension
        except Exception as e:
            info["parse_error"] = str(e)
        
        return info
    
    def validate_image_dimensions(self, width: int, height: int) -> bool:
        """
        验证图片尺寸
        
        Args:
            width: 图片宽度
            height: 图片高度
            
        Returns:
            是否符合尺寸要求
        """
        if width < self.min_image_dimension or height < self.min_image_dimension:
            logger.error(f"图片尺寸过小: {width}x{height} < {self.min_image_dimension}x{self.min_image_dimension}")
            return False
        
        if width > self.max_image_dimension or height > self.max_image_dimension:
            logger.error(f"图片尺寸过大: {width}x{height} > {self.max_image_dimension}x{self.max_image_dimension}")
            return False
        
        return True
    
    def create_image_content_with_validation(self, url: str, detail: str = "auto") -> Dict[str, Any]:
        """
        创建经过验证的图片内容
        
        Args:
            url: 图片URL
            detail: 图片详细程度
            
        Returns:
            验证后的图片内容
        """
        # 验证URL
        if not self.validate_image_url(url):
            raise ValueError(f"图片URL验证失败: {url}")
        
        # 处理图片
        return self.process_image_url(url, detail)
    
    def batch_validate_images(self, image_urls: List[str]) -> Dict[str, Any]:
        """
        批量验证图片URL
        
        Args:
            image_urls: 图片URL列表
            
        Returns:
            验证结果字典
        """
        results = {
            "total": len(image_urls),
            "valid": 0,
            "invalid": 0,
            "details": [],
            "errors": []
        }
        
        for i, url in enumerate(image_urls):
            try:
                is_valid = self.validate_image_url(url)
                image_info = self.get_image_info(url)
                
                result = {
                    "index": i,
                    "url": url,
                    "is_valid": is_valid,
                    "info": image_info
                }
                
                results["details"].append(result)
                
                if is_valid:
                    results["valid"] += 1
                else:
                    results["invalid"] += 1
                    
            except Exception as e:
                error_info = {
                    "index": i,
                    "url": url,
                    "error": str(e)
                }
                results["errors"].append(error_info)
                results["invalid"] += 1
        
        return results
    
    def format_for_provider(self, content: List[Dict[str, Any]], provider: str) -> List[Dict[str, Any]]:
        """
        为特定提供商格式化内容
        
        Args:
            content: 内容列表
            provider: 提供商名称
            
        Returns:
            格式化后的内容
        """
        if provider == "volcano":
            # Volcano使用OpenAI兼容格式
            return content
        elif provider == "google":
            # Google可能需要不同的格式
            return self._format_for_google(content)
        else:
            # 默认返回原格式
            return content
    
    def _format_for_google(self, content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """为Google格式化内容（如果需要）"""
        # Google Gemini可能有不同的多模态格式要求
        # 这里先返回原格式，后续可以根据需要调整
        return content
    
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
    
    def enhance_content_with_metadata(self, content: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        为内容添加元数据信息
        
        Args:
            content: 内容列表
            
        Returns:
            增强后的内容列表
        """
        enhanced_content = []
        
        for i, item in enumerate(content):
            enhanced_item = item.copy()
            enhanced_item["_metadata"] = {
                "index": i,
                "timestamp": time.time()
            }
            
            if item.get("type") == "image_url":
                image_url = item.get("image_url", {})
                url = image_url.get("url", "")
                if url:
                    try:
                        image_info = self.get_image_info(url)
                        enhanced_item["_metadata"]["image_info"] = image_info
                    except Exception as e:
                        enhanced_item["_metadata"]["image_error"] = str(e)
            
            enhanced_content.append(enhanced_item)
        
        return enhanced_content
    
    def create_content_summary(self, content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        创建内容摘要
        
        Args:
            content: 内容列表
            
        Returns:
            内容摘要字典
        """
        summary = {
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
            summary["content_types"].add(item_type)
            
            if item_type == "text":
                summary["text_items"] += 1
                text = item.get("text", "")
                summary["text_length"] += len(text)
                # 粗略估算token数量 (1 token ≈ 4 characters for Chinese)
                summary["estimated_tokens"] += len(text) // 4
                
            elif item_type == "image_url":
                summary["image_items"] += 1
                image_url = item.get("image_url", {})
                url = image_url.get("url", "")
                if url:
                    summary["image_urls"].append(url)
                # 图片大约消耗85个token (根据OpenAI文档)
                summary["estimated_tokens"] += 85
        
        summary["content_types"] = list(summary["content_types"])
        summary["has_multimodal"] = summary["image_items"] > 0
        
        return summary


class VolcanoLLMClient(LLM):
    """
    Volcano (火山引擎) Doubao LLM客户端
    
    基于OpenAI兼容API实现，支持文本生成和多模态内容处理
    """
    
    # 客户端配置
    client: Optional[Any] = Field(default=None, exclude=True)
    api_key: Optional[str] = Field(default=None, exclude=True)
    base_url: str = Field(default="https://ark.cn-beijing.volces.com/api/v3")
    model: str = Field(default="doubao-seed-1-6-250615")
    
    # 生成参数
    temperature: float = Field(default=0.1)
    max_tokens: int = Field(default=4000)
    top_p: float = Field(default=1.0)
    frequency_penalty: float = Field(default=0.0)
    presence_penalty: float = Field(default=0.0)
    
    # 重试配置 - 使用简单字段避免序列化问题
    max_retries: int = Field(default=3)
    base_delay: float = Field(default=1.0)
    max_delay: float = Field(default=60.0)
    exponential_base: float = Field(default=2.0)
    jitter: bool = Field(default=True)
    
    # 内部配置对象（不序列化）
    retry_config: Optional[RetryConfig] = Field(default=None, exclude=True)
    error_handler: Optional[ErrorHandler] = Field(default=None, exclude=True)
    
    # 多模态支持
    supports_multimodal: bool = Field(default=True)
    max_image_size_mb: int = Field(default=10)
    
    # 内容处理器
    content_handler: Optional[MultiModalContentHandler] = Field(default=None, exclude=True)
    
    class Config:
        """Pydantic配置"""
        arbitrary_types_allowed = True
    
    @model_validator(mode='before')
    @classmethod
    def validate_environment(cls, values: Dict) -> Dict:
        """验证环境配置"""
        # 获取API密钥
        api_key = values.get("api_key")
        if not api_key:
            try:
                api_key = get_ark_api_key()
                values["api_key"] = api_key
            except ValueError as e:
                logger.warning(f"Volcano API密钥未配置: {e}")
                raise ValueError(f"Volcano API密钥未配置: {e}")
        
        # 创建OpenAI客户端
        try:
            client = OpenAI(
                api_key=api_key,
                base_url=values.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")
            )
            values["client"] = client
            logger.info("Volcano LLM客户端初始化成功")
        except Exception as e:
            logger.error(f"Volcano LLM客户端初始化失败: {e}")
            raise ValueError(f"Volcano LLM客户端初始化失败: {e}")
        
        # 创建多模态内容处理器
        max_image_size = values.get("max_image_size_mb", 10)
        values["content_handler"] = MultiModalContentHandler(max_image_size_mb=max_image_size)
        
        # 创建重试配置对象
        retry_config = RetryConfig(
            max_retries=values.get("max_retries", 3),
            base_delay=values.get("base_delay", 1.0),
            max_delay=values.get("max_delay", 60.0),
            exponential_base=values.get("exponential_base", 2.0),
            jitter=values.get("jitter", True)
        )
        values["retry_config"] = retry_config
        
        # 创建错误处理器
        values["error_handler"] = ErrorHandler(retry_config=retry_config)
        
        return values
    
    @property
    def _llm_type(self) -> str:
        """返回LLM类型标识"""
        return "volcano_doubao"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        调用Volcano API生成文本
        
        Args:
            prompt: 输入提示文本
            stop: 停止词列表
            run_manager: 回调管理器
            **kwargs: 其他参数
            
        Returns:
            生成的文本内容
        """
        if run_manager:
            run_manager.on_llm_start(
                serialized={"name": self._llm_type},
                prompts=[prompt]
            )
        
        try:
            # 准备请求参数
            messages = [{"role": "user", "content": prompt}]
            
            # 调用API
            response = self._make_api_call(messages, stop=stop, **kwargs)
            
            # 提取响应内容
            content = response.choices[0].message.content
            
            if run_manager:
                run_manager.on_llm_end(LLMResult(generations=[[Generation(text=content)]]))
            
            return content
            
        except VolcanoAPIException as e:
            logger.error(f"Volcano API调用失败: {e}")
            if run_manager:
                run_manager.on_llm_error(e)
            raise e
        except Exception as e:
            # 处理未预期的异常
            error_type = self.error_handler.classify_error(e)
            volcano_exception = self.error_handler.create_exception(e, error_type)
            logger.error(f"Volcano API调用出现未预期错误: {volcano_exception}")
            if run_manager:
                run_manager.on_llm_error(volcano_exception)
            raise volcano_exception
    
    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """
        批量生成文本
        
        Args:
            prompts: 提示文本列表
            stop: 停止词列表
            run_manager: 回调管理器
            **kwargs: 其他参数
            
        Returns:
            LLM生成结果
        """
        generations = []
        
        for i, prompt in enumerate(prompts):
            try:
                content = self._call(prompt, stop=stop, run_manager=run_manager, **kwargs)
                generations.append([Generation(text=content)])
            except VolcanoAPIException as e:
                logger.error(f"生成文本失败 (prompt {i+1}/{len(prompts)}): {e}")
                generations.append([Generation(
                    text="", 
                    generation_info={
                        "error": e.message,
                        "error_type": e.error_type.value,
                        "request_id": e.request_id,
                        "status_code": e.status_code
                    }
                )])
            except Exception as e:
                # 处理未预期的异常
                error_type = self.error_handler.classify_error(e)
                volcano_exception = self.error_handler.create_exception(e, error_type)
                logger.error(f"生成文本出现未预期错误 (prompt {i+1}/{len(prompts)}): {volcano_exception}")
                generations.append([Generation(
                    text="", 
                    generation_info={
                        "error": volcano_exception.message,
                        "error_type": volcano_exception.error_type.value,
                        "original_error": str(e)
                    }
                )])
        
        return LLMResult(generations=generations)
    
    def _make_api_call(
        self,
        messages: List[Dict[str, Any]],
        stop: Optional[List[str]] = None,
        **kwargs: Any
    ) -> ChatCompletion:
        """
        执行API调用，包含增强的错误处理和重试逻辑
        
        Args:
            messages: 消息列表
            stop: 停止词列表
            **kwargs: 其他参数
            
        Returns:
            API响应
            
        Raises:
            VolcanoAPIException: 包含详细错误信息的自定义异常
        """
        # 合并参数
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "top_p": kwargs.get("top_p", self.top_p),
            "frequency_penalty": kwargs.get("frequency_penalty", self.frequency_penalty),
            "presence_penalty": kwargs.get("presence_penalty", self.presence_penalty),
        }
        
        if stop:
            params["stop"] = stop
        
        # 记录请求开始时间和上下文
        request_start_time = time.time()
        request_context = {
            "model": self.model,
            "message_count": len(messages),
            "has_images": any(
                isinstance(msg.get("content"), list) and 
                any(item.get("type") == "image_url" for item in msg.get("content", []))
                for msg in messages
            ),
            "max_tokens": params["max_tokens"],
            "temperature": params["temperature"]
        }
        
        logger.info(f"开始Volcano API调用: {request_context}")
        
        # 执行重试逻辑
        last_exception = None
        
        for attempt in range(self.retry_config.max_retries + 1):  # +1 for initial attempt
            try:
                # 记录单次尝试开始时间
                attempt_start_time = time.time()
                
                # 执行API调用
                response = self.client.chat.completions.create(**params)
                
                # 记录成功信息
                attempt_end_time = time.time()
                total_time = attempt_end_time - request_start_time
                attempt_time = attempt_end_time - attempt_start_time
                
                success_info = {
                    "model": self.model,
                    "attempt": attempt + 1,
                    "attempt_time": f"{attempt_time:.2f}s",
                    "total_time": f"{total_time:.2f}s",
                    "tokens_used": getattr(response.usage, 'total_tokens', None) if hasattr(response, 'usage') else None
                }
                
                logger.info(f"Volcano API调用成功: {success_info}")
                
                return response
                
            except Exception as original_error:
                # 分类错误
                error_type = self.error_handler.classify_error(original_error)
                
                # 创建自定义异常
                volcano_exception = self.error_handler.create_exception(original_error, error_type)
                
                # 判断是否应该重试
                will_retry = (
                    attempt < self.retry_config.max_retries and 
                    self.error_handler.should_retry(error_type, attempt)
                )
                
                # 记录错误日志
                self.error_handler.log_error(volcano_exception, attempt + 1, will_retry)
                
                # 如果不重试，抛出异常
                if not will_retry:
                    # 记录最终失败信息
                    total_time = time.time() - request_start_time
                    failure_info = {
                        "model": self.model,
                        "total_attempts": attempt + 1,
                        "total_time": f"{total_time:.2f}s",
                        "final_error_type": error_type.value,
                        "request_context": request_context
                    }
                    
                    logger.error(f"Volcano API调用最终失败: {failure_info}")
                    raise volcano_exception
                
                # 计算重试延迟
                delay = self.error_handler.calculate_delay(
                    attempt, 
                    error_type, 
                    volcano_exception.retry_after
                )
                
                # 记录重试信息
                retry_info = {
                    "attempt": attempt + 1,
                    "max_retries": self.retry_config.max_retries,
                    "error_type": error_type.value,
                    "delay": f"{delay:.1f}s",
                    "retry_after": volcano_exception.retry_after
                }
                
                logger.info(f"准备重试Volcano API调用: {retry_info}")
                
                # 等待重试
                time.sleep(delay)
                last_exception = volcano_exception
        
        # 这里不应该到达，但为了安全起见
        if last_exception:
            raise last_exception
        else:
            raise VolcanoAPIException(
                message="未知错误：重试循环异常退出",
                error_type=VolcanoErrorType.UNKNOWN_ERROR
            )
    
    def generate_with_messages(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any
    ) -> str:
        """
        使用消息列表生成文本
        
        Args:
            messages: LangChain消息列表
            stop: 停止词列表
            **kwargs: 其他参数
            
        Returns:
            生成的文本内容
        """
        # 转换消息格式
        api_messages = self._convert_messages(messages)
        
        # 调用API
        response = self._make_api_call(api_messages, stop=stop, **kwargs)
        
        return response.choices[0].message.content
    
    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        """
        将LangChain消息转换为API格式
        
        Args:
            messages: LangChain消息列表
            
        Returns:
            API消息格式列表
        """
        api_messages = []
        
        for message in messages:
            if isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, SystemMessage):
                role = "system"
            elif isinstance(message, AIMessage):
                role = "assistant"
            else:
                role = "user"  # 默认为用户消息
            
            # 处理内容
            content = message.content
            if isinstance(content, str):
                api_messages.append({"role": role, "content": content})
            elif isinstance(content, list):
                # 多模态内容 - 使用内容处理器处理
                processed_content = self.content_handler.prepare_content(content)
                if self.content_handler.validate_content(processed_content):
                    api_messages.append({"role": role, "content": processed_content})
                else:
                    # 如果多模态内容无效，回退到纯文本
                    text_content = self.content_handler.extract_text_content(processed_content)
                    if text_content:
                        api_messages.append({"role": role, "content": text_content})
                        logger.warning("多模态内容验证失败，回退到纯文本模式")
                    else:
                        logger.error("无法提取有效内容，跳过此消息")
            else:
                # 转换为字符串
                api_messages.append({"role": role, "content": str(content)})
        
        return api_messages
    
    def process_multimodal_content(
        self,
        content: Union[str, List[Dict], List[Union[TextContent, ImageContent]]],
        **kwargs
    ) -> str:
        """
        处理多模态内容并生成响应
        
        Args:
            content: 多模态内容
            **kwargs: 其他参数
            
        Returns:
            生成的文本内容
        """
        # 准备内容
        processed_content = self.content_handler.prepare_content(content)
        
        # 验证内容
        if not self.content_handler.validate_content(processed_content):
            # 如果多模态内容无效，尝试纯文本模式
            text_content = self.content_handler.extract_text_content(processed_content)
            if not text_content:
                raise ValueError("无法处理提供的内容：既不是有效的多模态内容，也没有文本内容")
            
            logger.warning("多模态内容验证失败，使用纯文本模式")
            return self._call(text_content, **kwargs)
        
        # 创建消息
        messages = [{"role": "user", "content": processed_content}]
        
        # 调用API
        response = self._make_api_call(messages, **kwargs)
        
        return response.choices[0].message.content
    
    def validate_image_url(self, url: str) -> bool:
        """
        验证图片URL（委托给内容处理器）
        
        Args:
            url: 图片URL
            
        Returns:
            是否有效
        """
        return self.content_handler.validate_image_url(url)
    
    def validate_image_content(self, content: List[Dict[str, Any]]) -> bool:
        """
        验证图片内容格式（委托给内容处理器）
        
        Args:
            content: 多模态内容列表
            
        Returns:
            是否有效
        """
        return self.content_handler.validate_content(content)
    
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
        **parameters
    ) -> MultiModalRequest:
        """
        创建多模态请求对象
        
        Args:
            text: 文本内容
            image_urls: 图片URL列表
            analysis_type: 分析类型
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
            provider="volcano",
            analysis_type=analysis_type,
            parameters=parameters
        )
    
    def analyze_with_images(
        self,
        text: str,
        image_urls: List[str],
        analysis_type: str = "visual_analysis",
        **kwargs
    ) -> str:
        """
        使用文本和图片进行分析
        
        Args:
            text: 分析文本
            image_urls: 图片URL列表
            analysis_type: 分析类型
            **kwargs: 其他参数
            
        Returns:
            分析结果
        """
        try:
            # 创建多模态请求
            request = self.create_multimodal_request(
                text=text,
                image_urls=image_urls,
                analysis_type=analysis_type,
                **kwargs
            )
            
            # 处理内容
            return self.process_multimodal_content(request.content, **kwargs)
            
        except Exception as e:
            logger.error(f"图片分析失败: {e}")
            # 回退到纯文本分析
            logger.info("回退到纯文本分析模式")
            return self._call(text, **kwargs)
    
    def validate_multimodal_request(self, content: Union[str, List[Dict], List[Union[TextContent, ImageContent]]]) -> Dict[str, Any]:
        """
        验证多模态请求的完整性
        
        Args:
            content: 多模态内容
            
        Returns:
            验证结果字典
        """
        try:
            # 准备内容
            processed_content = self.content_handler.prepare_content(content)
            
            # 验证内容结构
            structure_validation = self.content_handler.validate_content_structure(processed_content)
            
            # 创建内容摘要
            content_summary = self.content_handler.create_content_summary(processed_content)
            
            return {
                "is_valid": structure_validation["is_valid"],
                "validation_details": structure_validation,
                "content_summary": content_summary,
                "processed_content": processed_content
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "error": str(e),
                "validation_details": {"errors": [str(e)]},
                "content_summary": None,
                "processed_content": None
            }
    
    def process_multimodal_content_with_validation(
        self,
        content: Union[str, List[Dict], List[Union[TextContent, ImageContent]]],
        strict_validation: bool = True,
        **kwargs
    ) -> str:
        """
        处理多模态内容并生成响应（带完整验证）
        
        Args:
            content: 多模态内容
            strict_validation: 是否启用严格验证
            **kwargs: 其他参数
            
        Returns:
            生成的文本内容
        """
        # 验证请求
        validation_result = self.validate_multimodal_request(content)
        
        if not validation_result["is_valid"]:
            if strict_validation:
                error_msg = f"多模态内容验证失败: {validation_result.get('error', '未知错误')}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            else:
                # 尝试提取文本内容进行处理
                logger.warning("多模态内容验证失败，尝试提取文本内容")
                processed_content = validation_result.get("processed_content", [])
                if processed_content:
                    text_content = self.content_handler.extract_text_content(processed_content)
                    if text_content:
                        return self._call(text_content, **kwargs)
                
                raise ValueError("无法处理提供的内容")
        
        # 使用验证后的内容
        processed_content = validation_result["processed_content"]
        
        # 标准化内容
        normalized_content = self.content_handler.normalize_content(processed_content)
        
        # 创建消息
        messages = [{"role": "user", "content": normalized_content}]
        
        # 调用API
        response = self._make_api_call(messages, **kwargs)
        
        return response.choices[0].message.content
    
    def create_enhanced_multimodal_request(
        self,
        text: Optional[str] = None,
        image_urls: Optional[List[str]] = None,
        image_details: Optional[List[str]] = None,
        analysis_type: str = "general",
        validate_images: bool = True,
        **parameters
    ) -> MultiModalRequest:
        """
        创建增强的多模态请求对象
        
        Args:
            text: 文本内容
            image_urls: 图片URL列表
            image_details: 图片详细程度列表 (对应image_urls)
            analysis_type: 分析类型
            validate_images: 是否验证图片
            **parameters: 其他参数
            
        Returns:
            多模态请求对象
        """
        content = []
        
        if text:
            content.append(self.create_text_content(text))
        
        if image_urls:
            if image_details and len(image_details) != len(image_urls):
                logger.warning("图片详细程度列表长度与URL列表不匹配，使用默认值")
                image_details = None
            
            for i, url in enumerate(image_urls):
                detail = image_details[i] if image_details else "auto"
                
                if validate_images:
                    # 验证图片URL
                    if not self.validate_image_url(url):
                        logger.error(f"跳过无效的图片URL: {url}")
                        continue
                
                content.append(self.create_image_content(url, detail))
        
        if not content:
            raise ValueError("必须提供文本或图片内容")
        
        return MultiModalRequest(
            content=content,
            provider="volcano",
            analysis_type=analysis_type,
            parameters=parameters
        )
    
    def batch_analyze_with_images(
        self,
        requests: List[Dict[str, Any]],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        批量处理多模态分析请求
        
        Args:
            requests: 请求列表，每个请求包含text和image_urls
            **kwargs: 其他参数
            
        Returns:
            分析结果列表
        """
        results = []
        
        for i, request in enumerate(requests):
            try:
                text = request.get("text", "")
                image_urls = request.get("image_urls", [])
                analysis_type = request.get("analysis_type", "general")
                
                result = self.analyze_with_images(
                    text=text,
                    image_urls=image_urls,
                    analysis_type=analysis_type,
                    **kwargs
                )
                
                results.append({
                    "index": i,
                    "success": True,
                    "result": result,
                    "request": request
                })
                
            except Exception as e:
                logger.error(f"批量分析第{i+1}个请求失败: {e}")
                results.append({
                    "index": i,
                    "success": False,
                    "error": str(e),
                    "request": request
                })
        
        return results
    
    def get_content_info(self, content: Union[str, List[Dict]]) -> Dict[str, Any]:
        """
        获取内容信息统计
        
        Args:
            content: 内容
            
        Returns:
            内容信息字典
        """
        if isinstance(content, str):
            return {
                "type": "text_only",
                "text_length": len(content),
                "image_count": 0,
                "is_multimodal": False
            }
        
        processed_content = self.content_handler.prepare_content(content)
        text_content = self.content_handler.extract_text_content(processed_content)
        image_urls = self.content_handler.get_image_urls(processed_content)
        
        return {
            "type": "multimodal" if image_urls else "text_only",
            "text_length": len(text_content),
            "image_count": len(image_urls),
            "is_multimodal": len(image_urls) > 0,
            "image_urls": image_urls,
            "is_valid": self.content_handler.validate_content(processed_content)
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        return {
            "provider": "volcano",
            "model": self.model,
            "base_url": self.base_url,
            "supports_multimodal": self.supports_multimodal,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "max_image_size_mb": self.max_image_size_mb,
            "supported_image_formats": list(self.content_handler.supported_image_formats) if self.content_handler else [],
            "multimodal_features": {
                "text_and_image": True,
                "image_analysis": True,
                "content_validation": True,
                "fallback_to_text": True
            }
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试API连接并返回详细信息
        
        Returns:
            连接测试结果字典
        """
        test_start_time = time.time()
        test_result = {
            "success": False,
            "response_time": 0.0,
            "error": None,
            "error_type": None,
            "model_info": self.get_model_info(),
            "timestamp": test_start_time
        }
        
        try:
            # 使用简单的测试消息
            test_message = "Hello, this is a connection test."
            response = self._call(test_message, max_tokens=10)
            
            test_end_time = time.time()
            test_result.update({
                "success": True,
                "response_time": test_end_time - test_start_time,
                "response_preview": response[:50] + "..." if len(response) > 50 else response
            })
            
            logger.info(f"Volcano API连接测试成功: {test_result['response_time']:.2f}s")
            return test_result
            
        except VolcanoAPIException as e:
            test_end_time = time.time()
            test_result.update({
                "success": False,
                "response_time": test_end_time - test_start_time,
                "error": e.message,
                "error_type": e.error_type.value,
                "request_id": e.request_id,
                "status_code": e.status_code
            })
            
            logger.error(f"Volcano API连接测试失败: {e}")
            return test_result
            
        except Exception as e:
            test_end_time = time.time()
            error_type = self.error_handler.classify_error(e)
            test_result.update({
                "success": False,
                "response_time": test_end_time - test_start_time,
                "error": str(e),
                "error_type": error_type.value
            })
            
            logger.error(f"Volcano API连接测试出现未预期错误: {e}")
            return test_result
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        获取错误统计信息
        
        Returns:
            错误统计字典
        """
        return self.error_handler.get_error_stats()
    
    def reset_error_statistics(self):
        """重置错误统计信息"""
        self.error_handler.error_counts.clear()
        self.error_handler.last_errors.clear()
        logger.info("Volcano API错误统计信息已重置")
    
    def update_retry_config(self, **kwargs):
        """
        更新重试配置
        
        Args:
            **kwargs: 重试配置参数
        """
        # 更新重试配置
        for key, value in kwargs.items():
            if hasattr(self.retry_config, key):
                setattr(self.retry_config, key, value)
                # 同时更新实例属性
                if hasattr(self, key):
                    setattr(self, key, value)
                logger.info(f"更新重试配置: {key} = {value}")
            else:
                logger.warning(f"未知的重试配置参数: {key}")
        
        # 重新创建错误处理器
        self.error_handler = ErrorHandler(retry_config=self.retry_config)
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        获取客户端健康状态
        
        Returns:
            健康状态字典
        """
        # 执行连接测试
        connection_test = self.test_connection()
        
        # 获取错误统计
        error_stats = self.get_error_statistics()
        
        # 计算健康分数
        health_score = 100.0
        
        # 根据连接测试结果调整分数
        if not connection_test["success"]:
            health_score -= 50.0
        elif connection_test["response_time"] > 10.0:
            health_score -= 20.0
        elif connection_test["response_time"] > 5.0:
            health_score -= 10.0
        
        # 根据错误统计调整分数
        total_errors = sum(error_stats["error_counts"].values())
        if total_errors > 10:
            health_score -= 30.0
        elif total_errors > 5:
            health_score -= 15.0
        elif total_errors > 0:
            health_score -= 5.0
        
        # 检查最近错误
        current_time = time.time()
        recent_errors = sum(
            1 for timestamp in error_stats["last_errors"].values()
            if current_time - timestamp < 300  # 5分钟内的错误
        )
        
        if recent_errors > 3:
            health_score -= 20.0
        elif recent_errors > 1:
            health_score -= 10.0
        
        health_score = max(0.0, health_score)
        
        # 确定健康状态
        if health_score >= 80:
            status = "healthy"
        elif health_score >= 60:
            status = "degraded"
        elif health_score >= 30:
            status = "unhealthy"
        else:
            status = "critical"
        
        return {
            "status": status,
            "health_score": health_score,
            "connection_test": connection_test,
            "error_statistics": error_stats,
            "recent_errors": recent_errors,
            "timestamp": current_time,
            "recommendations": self._get_health_recommendations(status, connection_test, error_stats)
        }
    
    def _get_health_recommendations(
        self, 
        status: str, 
        connection_test: Dict[str, Any], 
        error_stats: Dict[str, Any]
    ) -> List[str]:
        """
        根据健康状态生成建议
        
        Args:
            status: 健康状态
            connection_test: 连接测试结果
            error_stats: 错误统计
            
        Returns:
            建议列表
        """
        recommendations = []
        
        if not connection_test["success"]:
            recommendations.append("检查网络连接和API密钥配置")
            recommendations.append("验证Volcano API服务是否正常")
        
        if connection_test.get("response_time", 0) > 5.0:
            recommendations.append("响应时间较慢，考虑检查网络状况")
        
        error_counts = error_stats["error_counts"]
        
        if error_counts.get("rate_limit_error", 0) > 0:
            recommendations.append("遇到速率限制，考虑增加重试延迟或减少请求频率")
        
        if error_counts.get("authentication_error", 0) > 0:
            recommendations.append("认证失败，请检查API密钥是否正确")
        
        if error_counts.get("quota_exceeded_error", 0) > 0:
            recommendations.append("API配额已用完，请检查账户余额或升级套餐")
        
        if error_counts.get("model_overloaded_error", 0) > 0:
            recommendations.append("模型过载，考虑使用其他模型或稍后重试")
        
        if sum(error_counts.values()) > 5:
            recommendations.append("错误频率较高，建议检查请求参数和网络环境")
        
        if status in ["unhealthy", "critical"]:
            recommendations.append("考虑启用备用LLM提供商")
            recommendations.append("检查系统日志以获取更多错误详情")
        
        return recommendations


def create_volcano_llm(**kwargs) -> VolcanoLLMClient:
    """
    创建Volcano LLM客户端实例
    
    Args:
        **kwargs: 客户端配置参数
        
    Returns:
        Volcano LLM客户端实例
    """
    # 从settings获取默认配置
    default_config = {
        "base_url": settings.ark_base_url,
        "model": settings.ark_model,
        "temperature": settings.llm_temperature,
        "max_tokens": settings.llm_max_tokens,
        "supports_multimodal": settings.enable_multimodal,
        "max_image_size_mb": settings.max_image_size_mb
    }
    
    # 处理重试配置
    retry_config = kwargs.pop("retry_config", None)
    if retry_config:
        if isinstance(retry_config, dict):
            # 将字典参数直接合并到配置中
            default_config.update(retry_config)
        elif isinstance(retry_config, RetryConfig):
            # 从RetryConfig对象提取参数
            default_config.update({
                "max_retries": retry_config.max_retries,
                "base_delay": retry_config.base_delay,
                "max_delay": retry_config.max_delay,
                "exponential_base": retry_config.exponential_base,
                "jitter": retry_config.jitter
            })
    
    # 合并用户配置
    config = {**default_config, **kwargs}
    
    return VolcanoLLMClient(**config)


def create_volcano_llm_with_custom_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    **kwargs
) -> VolcanoLLMClient:
    """
    创建带有自定义重试配置的Volcano LLM客户端
    
    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间
        max_delay: 最大延迟时间
        exponential_base: 指数退避基数
        jitter: 是否添加抖动
        **kwargs: 其他客户端配置参数
        
    Returns:
        Volcano LLM客户端实例
    """
    retry_config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter
    )
    
    return create_volcano_llm(retry_config=retry_config, **kwargs)


# 便捷函数
def create_text_content(text: str) -> TextContent:
    """创建文本内容"""
    return TextContent(type="text", text=text)


def create_image_content(url: str, detail: str = "auto") -> ImageContent:
    """创建图片内容"""
    return ImageContent(
        type="image_url",
        image_url=ImageUrl(url=url, detail=detail)
    )


def create_multimodal_content(
    text: Optional[str] = None,
    image_urls: Optional[List[str]] = None
) -> List[Union[TextContent, ImageContent]]:
    """
    创建多模态内容列表
    
    Args:
        text: 文本内容
        image_urls: 图片URL列表
        
    Returns:
        多模态内容列表
    """
    content = []
    
    if text:
        content.append(create_text_content(text))
    
    if image_urls:
        for url in image_urls:
            content.append(create_image_content(url))
    
    return content