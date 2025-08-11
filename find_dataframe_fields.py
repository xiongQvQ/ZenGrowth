#!/usr/bin/env python3
"""
查找所有可能导致Pydantic DataFrame错误的字段

这个脚本会查找所有dataclass定义，并检查是否有DataFrame类型的字段
"""

import os
import re
import glob

def find_dataframe_fields():
    """查找所有DataFrame字段"""
    print("查找所有可能的DataFrame字段...")
    
    # 查找所有Python文件
    python_files = []
    for pattern in ['**/*.py', 'agents/*.py', 'engines/*.py', 'config/*.py', 'tools/*.py']:
        python_files.extend(glob.glob(pattern, recursive=True))
    
    # 去重并排序
    python_files = sorted(list(set(python_files)))
    
    dataframe_issues = []
    
    for file_path in python_files:
        # 跳过测试文件和一些特殊文件
        if any(skip in file_path for skip in ['test_', '__pycache__', '.pyc', 'find_dataframe_fields.py']):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找dataclass定义
            dataclass_pattern = r'@dataclass\s*\nclass\s+(\w+).*?:\s*(.*?)(?=\n\n|\nclass|\ndef|\n@|\Z)'
            dataclass_matches = re.findall(dataclass_pattern, content, re.DOTALL)
            
            for class_name, class_body in dataclass_matches:
                # 在类体中查找DataFrame字段
                dataframe_field_pattern = r'(\w+):\s*pd\.DataFrame'
                field_matches = re.findall(dataframe_field_pattern, class_body)
                
                if field_matches:
                    dataframe_issues.append({
                        'file': file_path,
                        'class': class_name,
                        'fields': field_matches
                    })
                    print(f"发现DataFrame字段: {file_path} -> {class_name}.{field_matches}")
            
            # 也查找直接的DataFrame类型注解
            direct_dataframe_pattern = r'(\w+):\s*pd\.DataFrame'
            direct_matches = re.findall(direct_dataframe_pattern, content)
            
            if direct_matches:
                # 检查这些是否在dataclass中
                lines = content.split('\n')
                in_dataclass = False
                current_class = None
                
                for i, line in enumerate(lines):
                    if '@dataclass' in line:
                        in_dataclass = True
                    elif line.startswith('class ') and in_dataclass:
                        current_class = re.search(r'class\s+(\w+)', line)
                        if current_class:
                            current_class = current_class.group(1)
                    elif line.strip() == '' or (line.startswith('class ') and not in_dataclass):
                        in_dataclass = False
                        current_class = None
                    elif in_dataclass and current_class:
                        for field in direct_matches:
                            if f'{field}:' in line and 'pd.DataFrame' in line:
                                issue_found = False
                                for issue in dataframe_issues:
                                    if issue['file'] == file_path and issue['class'] == current_class:
                                        issue_found = True
                                        break
                                
                                if not issue_found:
                                    dataframe_issues.append({
                                        'file': file_path,
                                        'class': current_class,
                                        'fields': [field]
                                    })
                                    print(f"发现DataFrame字段: {file_path} -> {current_class}.{field}")
                
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")
    
    return dataframe_issues

def main():
    """主函数"""
    print("开始查找DataFrame字段...")
    
    issues = find_dataframe_fields()
    
    print(f"\n总结:")
    print(f"发现 {len(issues)} 个可能的问题")
    
    if issues:
        print("\n需要修复的DataFrame字段:")
        for issue in issues:
            print(f"  文件: {issue['file']}")
            print(f"  类: {issue['class']}")
            print(f"  字段: {', '.join(issue['fields'])}")
            print()
    else:
        print("✅ 没有发现DataFrame字段问题")

if __name__ == "__main__":
    main()