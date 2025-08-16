"""
缓存组件工具模块
为常用组件提供Streamlit缓存优化
"""

import streamlit as st
from typing import Optional


@st.cache_resource
def get_cached_ga4_parser():
    """获取缓存的GA4数据解析器"""
    from tools.ga4_data_parser import GA4DataParser
    return GA4DataParser()


@st.cache_resource  
def get_cached_data_validator():
    """获取缓存的数据验证器"""
    from tools.data_validator import DataValidator
    return DataValidator()


@st.cache_resource
def get_cached_storage_manager():
    """获取缓存的数据存储管理器"""
    from tools.data_storage_manager import DataStorageManager
    return DataStorageManager()


@st.cache_resource
def get_cached_integration_manager(lazy_loading: bool = True):
    """获取缓存的集成管理器"""
    from system.integration_manager_singleton import get_integration_manager
    return get_integration_manager(lazy_loading=lazy_loading)


@st.cache_resource
def get_cached_provider_manager():
    """获取缓存的LLM提供商管理器"""
    from config.llm_provider_manager import get_provider_manager
    return get_provider_manager()


@st.cache_resource
def get_cached_state_manager():
    """获取缓存的状态管理器"""
    from ui.state import get_state_manager
    return get_state_manager()


# 数据处理缓存函数
@st.cache_data
def cached_parse_data_file(file_path: str, file_type: str = "ndjson"):
    """缓存的数据文件解析"""
    parser = get_cached_ga4_parser()
    if file_type == "ndjson":
        return parser.parse_ndjson(file_path)
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")


@st.cache_data
def cached_validate_data_quality(data_hash: int, _data = None):
    """缓存的数据质量验证
    
    Args:
        data_hash: 数据的哈希值，用于缓存键
        _data: 实际数据（下划线前缀避免哈希）
    """
    if _data is None:
        return {}
    
    parser = get_cached_ga4_parser()
    return parser.validate_data_quality(_data)


@st.cache_data
def cached_extract_events(data_hash: int, _data = None):
    """缓存的事件提取
    
    Args:
        data_hash: 数据的哈希值，用于缓存键
        _data: 实际数据（下划线前缀避免哈希）
    """
    if _data is None:
        return {}
    
    parser = get_cached_ga4_parser()
    return parser.extract_events(_data)


def clear_component_cache():
    """清理组件缓存"""
    # 清理特定的缓存函数
    get_cached_ga4_parser.clear()
    get_cached_data_validator.clear()
    get_cached_storage_manager.clear()
    get_cached_integration_manager.clear()
    get_cached_provider_manager.clear()
    get_cached_state_manager.clear()
    
    # 清理数据处理缓存
    cached_parse_data_file.clear()
    cached_validate_data_quality.clear()
    cached_extract_events.clear()


def get_cache_info():
    """获取缓存信息"""
    return {
        "ga4_parser": "Cached" if hasattr(get_cached_ga4_parser, '_cache') else "Not cached",
        "data_validator": "Cached" if hasattr(get_cached_data_validator, '_cache') else "Not cached", 
        "storage_manager": "Cached" if hasattr(get_cached_storage_manager, '_cache') else "Not cached",
        "integration_manager": "Cached" if hasattr(get_cached_integration_manager, '_cache') else "Not cached",
        "provider_manager": "Cached" if hasattr(get_cached_provider_manager, '_cache') else "Not cached"
    }