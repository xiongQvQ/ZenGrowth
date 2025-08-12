import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current working directory: {sys.path[0]}")

try:
    import streamlit
    print(f"Streamlit version: {streamlit.__version__}")
except ImportError:
    print("Streamlit not installed")

try:
    import pandas as pd
    print(f"Pandas version: {pd.__version__}")
except ImportError:
    print("Pandas not installed")

print("Basic imports test completed.")