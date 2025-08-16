#!/usr/bin/env python3
"""
修复engines目录中用户可见的中文错误消息
重点处理可能在UI中显示的错误信息
"""

import os
import re
from pathlib import Path

def get_chinese_error_replacements():
    """获取中文错误消息的英文替换映射"""
    return {
        # ValueError messages
        "未提供事件数据且存储管理器未初始化": "Event data not provided and storage manager not initialized",
        "数据中缺少时间字段": "Missing time field in data",
        "缺少时间字段": "Missing time field",
        "必须提供漏斗步骤": "Funnel steps must be provided",
        "存储管理器未初始化": "Storage manager not initialized",
        "会话事件列表为空": "Session event list is empty",
        "数据中缺少时间信息：需要event_datetime或event_timestamp列": "Missing time information in data: event_datetime or event_timestamp column required",
        
        # Warning messages
        "事件数据为空，无法进行频次分析": "Event data is empty, cannot perform frequency analysis",
        "事件数据为空，无法进行趋势分析": "Event data is empty, cannot perform trend analysis",
        "事件数据为空，无法进行关联性分析": "Event data is empty, cannot perform correlation analysis",
        "事件数据为空，无法识别关键事件": "Event data is empty, cannot identify key events",
        "事件数据为空，无法构建转化漏斗": "Event data is empty, cannot build conversion funnel",
        "事件数据为空，无法进行漏斗分析": "Event data is empty, cannot perform funnel analysis",
        "事件数据为空，无法进行队列构建": "Event data is empty, cannot build cohorts",
        "事件数据为空，无法计算留存率": "Event data is empty, cannot calculate retention rate",
        "事件数据为空，无法重构会话": "Event data is empty, cannot reconstruct sessions",
        "事件数据为空，无法创建用户转化旅程": "Event data is empty, cannot create user conversion journeys",
        "事件数据为空，无法进行转化归因分析": "Event data is empty, cannot perform conversion attribution analysis",
        "事件数据为空，无法创建用户留存档案": "Event data is empty, cannot create user retention profiles",
        "事件数据为空，无法进行用户分群": "Event data is empty, cannot perform user segmentation",
        "没有可用的会话数据进行路径分析": "No session data available for path analysis",
        "没有足够的队列数据进行留存分析": "Not enough cohort data for retention analysis",
        
        # Error types
        "不支持的时间粒度": "Unsupported time granularity",
        "不支持的队列周期": "Unsupported cohort period", 
        "不支持的分析类型": "Unsupported analysis type",
        "不支持的聚类方法": "Unsupported clustering method",
        
        # Common operation messages
        "数据点不足，跳过趋势分析": "Insufficient data points, skipping trend analysis",
        "没有找到漏斗步骤相关的事件": "No events found for funnel steps",
        
        # Analysis completion messages (info level)
        "初始化完成": "initialization completed",
        "分析完成": "analysis completed",
        "构建了": "built",
        "个用户队列": "user cohorts",
        "个用户会话": "user sessions",
        "个用户留存档案": "user retention profiles",
        "个事件的重要性分析": "event importance analysis",
        "种事件类型的频次分析": "event type frequency analysis",
        "种事件类型的趋势分析": "event type trend analysis",
        "个事件对的关联性分析": "event pair correlation analysis",
        
        # Specific error patterns
        "支持的格式": "supported formats",
        "日, weekly/周, monthly/月": "daily, weekly, monthly",
        "daily/日, weekly/周, monthly/月": "daily, weekly, monthly"
    }

def fix_chinese_in_engines():
    """修复engines目录中的中文错误消息"""
    engines_dir = Path("engines")
    if not engines_dir.exists():
        print("❌ engines目录不存在")
        return False
    
    replacements = get_chinese_error_replacements()
    files_modified = 0
    total_replacements = 0
    
    print("🔧 开始修复engines目录中的中文错误消息...")
    
    # 处理每个Python文件
    for py_file in engines_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue  # 跳过__init__.py，只有注释
            
        print(f"\n📁 处理文件: {py_file}")
        
        try:
            # 读取文件内容
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            file_replacements = 0
            
            # 应用替换
            for chinese_text, english_text in replacements.items():
                if chinese_text in content:
                    # 替换字符串，保持引号格式
                    content = content.replace(f'"{chinese_text}"', f'"{english_text}"')
                    content = content.replace(f"'{chinese_text}'", f"'{english_text}'")
                    # 替换f-string中的内容
                    content = content.replace(f'f"{chinese_text}', f'f"{english_text}')
                    content = content.replace(f"f'{chinese_text}", f"f'{english_text}")
                    file_replacements += 1
            
            # 如果有修改，保存文件
            if content != original_content:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✅ 应用了 {file_replacements} 个替换")
                files_modified += 1
                total_replacements += file_replacements
            else:
                print(f"  ℹ️ 没有需要替换的内容")
                
        except Exception as e:
            print(f"  ❌ 处理文件失败: {e}")
    
    print(f"\n📊 修复完成:")
    print(f"  - 修改文件数: {files_modified}")
    print(f"  - 总替换数: {total_replacements}")
    
    return files_modified > 0

def fix_init_file():
    """修复__init__.py中的中文注释"""
    init_file = Path("engines/__init__.py")
    
    if not init_file.exists():
        return False
    
    print(f"\n📁 处理 {init_file}...")
    
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换注释
        new_content = content.replace(
            "# 分析引擎模块", 
            "# Analysis Engine Module"
        ).replace(
            "# 包含各种数据分析和计算引擎",
            "# Contains various data analysis and calculation engines"
        )
        
        if new_content != content:
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  ✅ 修复了 __init__.py 中的中文注释")
            return True
        else:
            print(f"  ℹ️ __init__.py 没有需要修复的内容")
            return False
            
    except Exception as e:
        print(f"  ❌ 处理 __init__.py 失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始修复engines目录中的中文内容...")
    
    # 修复用户可见的错误消息
    error_messages_fixed = fix_chinese_in_engines()
    
    # 修复__init__.py
    init_fixed = fix_init_file()
    
    if error_messages_fixed or init_fixed:
        print("\n🎉 engines目录中的用户可见中文内容修复完成！")
        print("\n✅ 修复内容:")
        print("1. ✅ 用户可见的错误和警告消息已英文化")
        print("2. ✅ ValueError和logger消息已替换为英文")
        print("3. ✅ 文件注释已英文化")
        print("\n📝 说明:")
        print("- 重点修复了可能在UI中显示的错误消息")
        print("- 保留了内部代码注释和文档字符串的原有结构")
        print("- 现在英文模式下分析错误将显示英文消息")
        return True
    else:
        print("\n ℹ️ 没有找到需要修复的中文内容")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)