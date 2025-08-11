"""
系统配置管理
包含API配置、模型配置和系统参数设置
"""

import os
from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Settings(BaseSettings):
    """系统配置类"""
    
    # Google Gemini API配置
    google_api_key: Optional[str] = Field(
        default=None,
        env="GOOGLE_API_KEY",
        description="Google Gemini API密钥"
    )
    
    # Volcano API配置
    ark_api_key: Optional[str] = Field(
        default=None,
        env="ARK_API_KEY",
        description="Volcano ARK API密钥"
    )
    
    ark_base_url: str = Field(
        default="https://ark.cn-beijing.volces.com/api/v3",
        env="ARK_BASE_URL",
        description="Volcano ARK API基础URL"
    )
    
    ark_model: str = Field(
        default="doubao-seed-1-6-250615",
        env="ARK_MODEL",
        description="Volcano Doubao模型名称"
    )
    
    # LLM提供商配置
    default_llm_provider: str = Field(
        default="google",
        env="DEFAULT_LLM_PROVIDER",
        description="默认LLM提供商 (google, volcano)"
    )
    
    enabled_providers: List[str] = Field(
        default=["google", "volcano"],
        env="ENABLED_PROVIDERS",
        description="启用的LLM提供商列表"
    )
    
    # 回退配置
    enable_fallback: bool = Field(
        default=True,
        env="ENABLE_FALLBACK",
        description="启用提供商回退机制"
    )
    
    fallback_order: List[str] = Field(
        default=["google", "volcano"],
        env="FALLBACK_ORDER",
        description="提供商回退顺序"
    )
    
    # 多模态配置
    enable_multimodal: bool = Field(
        default=True,
        env="ENABLE_MULTIMODAL",
        description="启用多模态内容支持"
    )
    
    max_image_size_mb: int = Field(
        default=10,
        env="MAX_IMAGE_SIZE_MB",
        description="最大图片大小（MB）"
    )
    
    # 模型配置
    llm_model: str = Field(
        default="gemini-2.5-pro",
        description="使用的LLM模型名称"
    )
    
    llm_temperature: float = Field(
        default=0.1,
        description="LLM温度参数，控制输出随机性"
    )
    
    llm_max_tokens: int = Field(
        default=4000,
        description="LLM最大输出token数"
    )
    
    # 数据处理配置
    max_file_size_mb: int = Field(
        default=100,
        description="最大文件上传大小（MB）"
    )
    
    chunk_size: int = Field(
        default=10000,
        description="数据处理块大小"
    )
    
    # 分析配置
    retention_periods: list = Field(
        default=[1, 7, 14, 30],
        description="留存分析时间段（天）"
    )
    
    min_cluster_size: int = Field(
        default=100,
        description="用户分群最小群体大小"
    )
    
    # Streamlit配置
    app_title: str = Field(
        default="用户行为分析智能体平台",
        description="应用标题"
    )
    
    app_icon: str = Field(
        default="📊",
        description="应用图标"
    )
    
    # 日志配置
    log_level: str = Field(
        default="INFO",
        description="日志级别"
    )
    
    log_file: str = Field(
        default="logs/app.log",
        description="日志文件路径"
    )
    
    @validator('default_llm_provider')
    def validate_default_provider(cls, v):
        """验证默认LLM提供商"""
        valid_providers = ['google', 'volcano']
        if v not in valid_providers:
            raise ValueError(f"默认提供商必须是以下之一: {valid_providers}")
        return v
    
    @validator('enabled_providers')
    def validate_enabled_providers(cls, v):
        """验证启用的提供商列表"""
        valid_providers = ['google', 'volcano']
        for provider in v:
            if provider not in valid_providers:
                raise ValueError(f"提供商 '{provider}' 不在有效列表中: {valid_providers}")
        return v
    
    @validator('fallback_order')
    def validate_fallback_order(cls, v):
        """验证回退顺序"""
        valid_providers = ['google', 'volcano']
        for provider in v:
            if provider not in valid_providers:
                raise ValueError(f"回退提供商 '{provider}' 不在有效列表中: {valid_providers}")
        return v
    
    @validator('max_image_size_mb')
    def validate_image_size(cls, v):
        """验证图片大小限制"""
        if v <= 0 or v > 100:
            raise ValueError("图片大小必须在1-100MB之间")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
settings = Settings()


def get_google_api_key() -> str:
    """获取Google API密钥"""
    api_key = settings.google_api_key
    if not api_key:
        raise ValueError(
            "Google API密钥未设置。请在.env文件中设置GOOGLE_API_KEY环境变量"
        )
    return api_key


def get_ark_api_key() -> str:
    """获取Volcano ARK API密钥"""
    api_key = settings.ark_api_key
    if not api_key:
        raise ValueError(
            "Volcano ARK API密钥未设置。请在.env文件中设置ARK_API_KEY环境变量"
        )
    return api_key


def get_provider_api_key(provider: str) -> str:
    """根据提供商获取对应的API密钥"""
    if provider == "google":
        return get_google_api_key()
    elif provider == "volcano":
        return get_ark_api_key()
    else:
        raise ValueError(f"不支持的提供商: {provider}")


def validate_provider_config(provider: str) -> bool:
    """验证特定提供商的配置"""
    try:
        if provider == "google":
            get_google_api_key()
            return True
        elif provider == "volcano":
            get_ark_api_key()
            # 验证Volcano特定配置
            if not settings.ark_base_url:
                raise ValueError("Volcano ARK基础URL未设置")
            if not settings.ark_model:
                raise ValueError("Volcano模型名称未设置")
            return True
        else:
            raise ValueError(f"不支持的提供商: {provider}")
    except ValueError as e:
        print(f"提供商 {provider} 配置验证失败: {e}")
        return False


def get_available_providers() -> List[str]:
    """获取可用的提供商列表（已配置API密钥的）"""
    available = []
    for provider in settings.enabled_providers:
        if validate_provider_config(provider):
            available.append(provider)
    return available


def validate_config() -> bool:
    """验证配置完整性"""
    try:
        # 验证默认提供商是否在启用列表中
        if settings.default_llm_provider not in settings.enabled_providers:
            print(f"警告: 默认提供商 '{settings.default_llm_provider}' 不在启用列表中")
            return False
        
        # 验证至少有一个提供商可用
        available_providers = get_available_providers()
        if not available_providers:
            print("错误: 没有可用的LLM提供商，请检查API密钥配置")
            return False
        
        # 验证默认提供商是否可用
        if settings.default_llm_provider not in available_providers:
            print(f"警告: 默认提供商 '{settings.default_llm_provider}' 配置不完整")
            if settings.enable_fallback and available_providers:
                print(f"将使用回退提供商: {available_providers[0]}")
            else:
                return False
        
        # 验证回退配置
        if settings.enable_fallback:
            fallback_available = [p for p in settings.fallback_order if p in available_providers]
            if not fallback_available:
                print("警告: 启用了回退机制但没有可用的回退提供商")
        
        print(f"配置验证成功。可用提供商: {available_providers}")
        return True
        
    except Exception as e:
        print(f"配置验证失败: {e}")
        return False


def get_provider_config(provider: str) -> dict:
    """获取特定提供商的配置信息"""
    if provider == "google":
        return {
            "api_key": settings.google_api_key,
            "model": settings.llm_model,
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
            "supports_multimodal": False
        }
    elif provider == "volcano":
        return {
            "api_key": settings.ark_api_key,
            "base_url": settings.ark_base_url,
            "model": settings.ark_model,
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
            "supports_multimodal": settings.enable_multimodal
        }
    else:
        raise ValueError(f"不支持的提供商: {provider}")