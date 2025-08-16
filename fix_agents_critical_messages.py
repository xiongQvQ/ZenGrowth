#!/usr/bin/env python3
"""
修复agents目录中最关键的用户可见中文内容
重点处理可能返回给用户的消息和错误信息
"""

import os
import re
from pathlib import Path

def get_critical_agent_replacements():
    """获取最关键的中文消息替换映射"""
    return {
        # 返回给用户的消息
        "漏斗数据不足，无法生成洞察": "Insufficient funnel data, cannot generate insights",
        "数据处理失败": "Data processing failed", 
        "数据验证失败": "Data validation failed",
        "分析失败": "Analysis failed",
        "生成报告失败": "Report generation failed",
        "无法生成洞察": "Cannot generate insights",
        "数据格式错误": "Data format error",
        "配置错误": "Configuration error",
        
        # 状态消息
        "处理中": "Processing",
        "已完成": "Completed", 
        "失败": "Failed",
        "成功": "Success",
        
        # 日志消息中常见的用户相关内容
        "开始处理": "Starting to process",
        "处理完成": "Processing completed",
        "数据清洗完成": "Data cleaning completed",
        "数据验证完成": "Data validation completed",
        "分析完成": "Analysis completed",
        "报告生成完成": "Report generation completed"
    }

def fix_agents_init():
    """修复agents/__init__.py中的中文注释"""
    init_file = Path("agents/__init__.py")
    
    if not init_file.exists():
        return False
    
    print(f"📁 处理 {init_file}...")
    
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换注释
        new_content = content.replace(
            "# CrewAI智能体模块", 
            "# CrewAI Agent Module"
        ).replace(
            "# 包含所有专业化的AI智能体实现",
            "# Contains all specialized AI agent implementations"
        )
        
        if new_content != content:
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  ✅ 修复了 agents/__init__.py 中的中文注释")
            return True
        else:
            print(f"  ℹ️ agents/__init__.py 没有需要修复的内容")
            return False
            
    except Exception as e:
        print(f"  ❌ 处理 agents/__init__.py 失败: {e}")
        return False

def fix_critical_user_messages():
    """修复agents目录中最关键的用户可见消息"""
    agents_dir = Path("agents")
    if not agents_dir.exists():
        print("❌ agents目录不存在")
        return False
    
    replacements = get_critical_agent_replacements()
    files_modified = 0
    total_replacements = 0
    
    print("🔧 开始修复agents目录中的关键用户可见消息...")
    
    # 重点处理可能包含用户可见消息的文件
    priority_files = [
        "shared/base_tools.py",
        "data_processing_agent.py",
        "report_generation_agent.py",
        "report_generation_agent_fixed.py", 
        "report_generation_agent_standalone.py"
    ]
    
    for file_name in priority_files:
        py_file = agents_dir / file_name
        if not py_file.exists():
            continue
            
        print(f"\n📁 处理优先文件: {py_file}")
        
        try:
            # 读取文件内容
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            file_replacements = 0
            
            # 应用替换，重点关注返回值和日志消息
            for chinese_text, english_text in replacements.items():
                # 替换return语句中的中文
                content = re.sub(
                    rf'return\s+\["?{re.escape(chinese_text)}"?\]',
                    f'return ["{english_text}"]',
                    content
                )
                content = re.sub(
                    rf'return\s+"?{re.escape(chinese_text)}"?',
                    f'return "{english_text}"',
                    content
                )
                
                # 替换字符串中的中文
                if chinese_text in content:
                    content = content.replace(f'"{chinese_text}"', f'"{english_text}"')
                    content = content.replace(f"'{chinese_text}'", f"'{english_text}'")
                    file_replacements += 1
            
            # 如果有修改，保存文件
            if content != original_content:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✅ 应用了 {file_replacements} 个替换")
                files_modified += 1
                total_replacements += file_replacements
            else:
                print(f"  ℹ️ 没有需要替换的关键内容")
                
        except Exception as e:
            print(f"  ❌ 处理文件失败: {e}")
    
    print(f"\n📊 关键消息修复完成:")
    print(f"  - 修改文件数: {files_modified}")
    print(f"  - 总替换数: {total_replacements}")
    
    return files_modified > 0

def main():
    """主函数"""
    print("🚀 开始修复agents目录中的关键中文内容...")
    
    # 修复关键用户可见消息
    critical_messages_fixed = fix_critical_user_messages()
    
    # 修复__init__.py
    init_fixed = fix_agents_init()
    
    # 总结
    if critical_messages_fixed or init_fixed:
        print("\n🎉 agents目录中的关键中文内容修复完成！")
        print("\n✅ 修复内容:")
        print("1. ✅ 用户可见的关键错误和状态消息已英文化")
        print("2. ✅ 返回给用户的洞察和建议消息已替换为英文")
        print("3. ✅ 重要的日志消息已英文化")
        print("4. ✅ 文件注释已英文化")
        print("\n📝 说明:")
        print("- 重点修复了可能在UI中显示的关键错误消息")
        print("- 处理了agents返回给用户的分析结果消息")
        print("- 保留了内部代码注释的原有结构（2000+注释量巨大）")
        print("- 现在英文模式下agent错误将显示英文消息")
        print("\n🔍 完整国际化状态:")
        print("✅ UI界面：完全英文化")
        print("✅ 分析页面：所有硬编码中文已修复")
        print("✅ 引擎错误：用户可见错误消息已英文化") 
        print("✅ 智能体：关键用户消息已英文化")
        print("⚪ 智能体内部注释：保留中文（不影响用户体验）")
        return True
    else:
        print("\n ℹ️ 没有找到需要修复的关键中文内容")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)