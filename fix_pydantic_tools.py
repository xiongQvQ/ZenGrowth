#!/usr/bin/env python3
"""
修复Pydantic BaseTool初始化问题

这个脚本会自动修复所有继承自BaseTool的类中的实例变量初始化问题
"""

import os
import re
import glob

def fix_tool_initialization(file_path):
    """修复单个文件中的工具初始化问题"""
    print(f"处理文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 查找所有继承自BaseTool的类
    class_pattern = r'class\s+(\w+Tool)\(BaseTool\):'
    classes = re.findall(class_pattern, content)
    
    for class_name in classes:
        print(f"  处理类: {class_name}")
        
        # 查找该类的__init__方法
        init_pattern = rf'(class\s+{class_name}\(BaseTool\):.*?def\s+__init__\(self[^)]*\):\s*super\(\).__init__\(\)\s*)((?:\s*self\.\w+\s*=.*?\n)+)'
        
        match = re.search(init_pattern, content, re.DOTALL)
        if match:
            init_header = match.group(1)
            assignments = match.group(2)
            
            # 转换赋值语句
            assignment_lines = assignments.strip().split('\n')
            new_assignments = []
            
            for line in assignment_lines:
                line = line.strip()
                if line and 'self.' in line and '=' in line:
                    # 提取变量名和值
                    var_match = re.match(r'self\.(\w+)\s*=\s*(.+)', line)
                    if var_match:
                        var_name = var_match.group(1)
                        var_value = var_match.group(2)
                        new_line = f"        object.__setattr__(self, '{var_name}', {var_value})"
                        new_assignments.append(new_line)
                        print(f"    转换: {line} -> {new_line}")
            
            if new_assignments:
                # 添加注释
                comment = "        # Initialize components as instance variables (not Pydantic fields)"
                new_init = init_header + comment + '\n' + '\n'.join(new_assignments) + '\n'
                
                # 替换原始内容
                content = content.replace(match.group(0), new_init)
    
    # 如果内容有变化，写回文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ 文件已更新")
        return True
    else:
        print(f"  ⏭️  无需更新")
        return False

def main():
    """主函数"""
    print("开始修复Pydantic BaseTool初始化问题...")
    
    # 查找所有agent文件
    agent_files = glob.glob('agents/*.py')
    
    updated_files = []
    
    for file_path in agent_files:
        # 跳过__init__.py和已经处理过的文件
        if '__init__.py' in file_path or 'standalone' in file_path or 'fixed' in file_path:
            continue
            
        try:
            if fix_tool_initialization(file_path):
                updated_files.append(file_path)
        except Exception as e:
            print(f"❌ 处理文件 {file_path} 时出错: {e}")
    
    print(f"\n修复完成！")
    print(f"更新的文件数量: {len(updated_files)}")
    for file_path in updated_files:
        print(f"  - {file_path}")

if __name__ == "__main__":
    main()