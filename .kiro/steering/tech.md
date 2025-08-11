# Technology Stack & Build System

## Core Technologies

### AI & Machine Learning
- **CrewAI**: Multi-agent framework for AI collaboration
- **Google Gemini-2.5-pro**: LLM for intelligent insights and recommendations
- **LangChain**: LLM integration and chain management
- **scikit-learn**: Machine learning algorithms for clustering and analysis

### Web Framework & UI
- **Streamlit**: Main web application framework
- **Plotly**: Interactive data visualization
- **Matplotlib & Seaborn**: Statistical plotting and charts

### Data Processing
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing
- **SciPy**: Scientific computing algorithms

### Configuration & Validation
- **Pydantic**: Data validation and settings management
- **python-dotenv**: Environment variable management
- **jsonschema**: JSON data validation

### Development & Testing
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Code linting
- **loguru**: Advanced logging

## Build System

### Environment Setup
```bash
# Automated setup
python setup.py

# Manual setup with venv
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt

# Conda environment setup (recommended)
conda activate useranalyse_env
pip install -r requirements.txt
```

### Common Commands

#### Development
```bash
# Activate conda environment first
conda activate useranalyse_env

# Start application
streamlit run main.py

# Run with custom port
streamlit run main.py --server.port 8502

# Run tests
pytest
pytest -v  # verbose output
pytest --cov  # with coverage

# Code formatting
black .
flake8 .
```

#### Data Processing
```bash
# Activate conda environment first
conda activate useranalyse_env

# Validate basic setup
python test_basic_setup.py

# Test complete setup
python test_setup.py

# Run specific agent tests
python test_*_agent_standalone.py
```

## Configuration Management

### Environment Variables (.env)
```env
GOOGLE_API_KEY=your_api_key_here
LLM_MODEL=gemini-2.5-pro
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4000
LOG_LEVEL=INFO
```

### System Configuration
- `config/settings.py`: Central configuration management
- `config/crew_config.py`: CrewAI agent configurations
- `config/analysis_config.json`: Analysis parameters
- `config/system_config.json`: System-wide settings

## Architecture Patterns

### Agent-Based Architecture
- Each analysis type has a dedicated agent (event, retention, conversion, etc.)
- Agents use specialized tools and engines for their domain
- CrewAI orchestrates multi-agent collaboration

### Modular Design
- **agents/**: CrewAI agent implementations
- **engines/**: Core analysis algorithms
- **tools/**: Data processing utilities
- **visualization/**: Chart and visualization components
- **utils/**: Shared utilities and helpers

### Data Flow Pattern
1. **Upload** → GA4 NDJSON files via Streamlit interface
2. **Parse** → GA4DataParser extracts structured data
3. **Validate** → DataValidator ensures data quality
4. **Process** → Analysis engines perform computations
5. **Visualize** → Chart generators create interactive plots
6. **Export** → ReportExporter generates output files