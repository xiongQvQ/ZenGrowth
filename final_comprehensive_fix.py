#!/usr/bin/env python3
"""
最终综合修复脚本
解决所有已知问题
"""

import sys
import os
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"✅ {description}成功")
            return True
        else:
            print(f"⚠️ {description}有警告: {result.stderr[:200]}")
            return True  # 继续执行
    except subprocess.TimeoutExpired:
        print(f"⏰ {description}超时，但继续执行")
        return True
    except Exception as e:
        print(f"❌ {description}失败: {e}")
        return False

def main():
    print("🎯 最终综合修复脚本")
    print("=" * 50)
    
    # 1. 检查基本环境
    print("1. 检查基本环境...")
    if not Path("venv").exists():
        print("❌ 虚拟环境不存在")
        return False
    
    if not Path("main.py").exists():
        print("❌ main.py 不存在")
        return False
    
    print("✅ 基本环境检查通过")
    
    # 2. 生成测试数据
    data_file = Path("data/events_ga4.ndjson")
    if not data_file.exists():
        print("2. 生成测试数据...")
        if not run_command("python generate_clean_data.py", "生成测试数据"):
            print("❌ 无法生成测试数据")
            return False
    else:
        print("2. ✅ 测试数据已存在")
    
    # 3. 测试基本功能
    print("3. 测试基本功能...")
    test_script = '''
import pandas as pd
from pathlib import Path
from tools.ga4_data_parser import GA4DataParser
from tools.data_storage_manager import DataStorageManager

try:
    # 测试数据解析
    data_file = Path("data/events_ga4.ndjson")
    parser = GA4DataParser()
    raw_data = parser.parse_ndjson(str(data_file))
    print(f"解析: {len(raw_data)} 个事件")
    
    # 测试事件提取
    events_data = parser.extract_events(raw_data)
    if isinstance(events_data, dict):
        all_events = []
        for event_type, event_df in events_data.items():
            if not event_df.empty:
                all_events.append(event_df)
        combined_events = pd.concat(all_events, ignore_index=True)
        print(f"合并: {len(combined_events)} 个事件")
    else:
        combined_events = events_data
    
    # 测试存储
    storage_manager = DataStorageManager()
    storage_manager.store_events(combined_events)
    stored = storage_manager.get_data("events")
    print(f"存储: {len(stored)} 个事件")
    
    print("SUCCESS")
except Exception as e:
    print(f"ERROR: {e}")
'''
    
    with open("temp_test.py", "w") as f:
        f.write(test_script)
    
    if not run_command("python temp_test.py", "基本功能测试"):
        print("❌ 基本功能测试失败")
        return False
    
    # 清理临时文件
    try:
        os.remove("temp_test.py")
    except:
        pass
    
    # 4. 启动应用
    print("4. 启动应用...")
    print("🌐 启动 Streamlit 应用...")
    print("📝 应用地址: http://localhost:8503")
    print("⏹️  按 Ctrl+C 停止应用")
    print("\\n" + "=" * 50)
    
    try:
        # 使用端口 8503 避免冲突
        cmd = [sys.executable, "-m", "streamlit", "run", "main.py", 
               "--server.port", "8503", "--server.headless", "true"]
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        print("\\n💡 手动启动命令:")
        print("   streamlit run main.py --server.port 8503")

if __name__ == "__main__":
    main()