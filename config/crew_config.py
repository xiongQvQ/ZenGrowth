"""
CrewAI智能体团队配置
定义智能体角色、目标和协作关系
"""

from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.base import BaseLanguageModel
from typing import Optional
import logging

from config.settings import get_google_api_key, settings
from config.llm_provider_manager import get_provider_manager

# 设置日志
logger = logging.getLogger(__name__)


def get_llm(provider: Optional[str] = None, **kwargs) -> BaseLanguageModel:
    """
    获取配置的LLM模型
    
    Args:
        provider: 指定的LLM提供商 ('google', 'volcano', 等)
        **kwargs: 额外的配置参数
        
    Returns:
        LLM实例
        
    Note:
        为了保持向后兼容性，如果没有指定provider，将使用默认提供商
        如果LLMProviderManager不可用，将回退到原始的Google LLM实现
    """
    try:
        # 尝试使用LLMProviderManager
        provider_manager = get_provider_manager()
        return provider_manager.get_llm(provider=provider, **kwargs)
        
    except Exception as e:
        # 如果LLMProviderManager失败，回退到原始实现
        logger.warning(f"LLMProviderManager不可用，回退到Google LLM: {e}")
        
        # 向后兼容：如果指定了非Google提供商但无法使用管理器，记录警告
        if provider and provider != "google":
            logger.warning(f"无法使用指定的提供商 '{provider}'，回退到Google LLM")
        
        return ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=get_google_api_key(),
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )


# 智能体角色定义
AGENT_ROLES = {
    "data_processor": {
        "role": "数据处理专家",
        "goal": "解析和预处理GA4事件数据，确保数据质量和完整性",
        "backstory": "你是一位经验丰富的数据工程师，专门处理大规模用户行为数据。"
                    "你精通各种数据格式解析，能够快速识别数据质量问题并提供解决方案。"
    },
    
    "event_analyst": {
        "role": "事件分析专家", 
        "goal": "深入分析用户事件模式，识别关键行为趋势和异常",
        "backstory": "你是一位资深的用户行为分析师，擅长从海量事件数据中发现有价值的模式。"
                    "你能够识别用户行为的关键节点，并提供数据驱动的业务洞察。"
    },
    
    "retention_analyst": {
        "role": "留存分析专家",
        "goal": "计算用户留存率，分析用户生命周期和流失模式",
        "backstory": "你是一位专业的用户留存分析师，深谙用户生命周期管理。"
                    "你能够准确计算各种留存指标，并识别影响用户留存的关键因素。"
    },
    
    "conversion_analyst": {
        "role": "转化分析专家",
        "goal": "构建转化漏斗，识别转化瓶颈和优化机会",
        "backstory": "你是一位经验丰富的转化优化专家，专注于提升用户转化率。"
                    "你擅长构建复杂的转化漏斗，并能准确识别转化路径中的关键问题。"
    },
    
    "segmentation_analyst": {
        "role": "用户分群专家",
        "goal": "基于用户行为和属性进行智能分群，生成用户画像",
        "backstory": "你是一位用户研究专家，精通各种聚类算法和用户画像技术。"
                    "你能够从复杂的用户数据中识别有意义的用户群体，并提供精准的营销建议。"
    },
    
    "path_analyst": {
        "role": "路径分析专家",
        "goal": "分析用户行为路径，优化用户体验流程",
        "backstory": "你是一位用户体验分析师，专注于用户行为路径优化。"
                    "你能够重构用户的完整行为轨迹，识别最优路径和体验痛点。"
    },
    
    "report_generator": {
        "role": "报告生成专家",
        "goal": "汇总分析结果，生成综合性的业务洞察报告",
        "backstory": "你是一位资深的业务分析师，擅长将复杂的数据分析结果转化为清晰的业务建议。"
                    "你能够整合多维度的分析结果，提供可执行的战略建议。"
    }
}


def create_agent(agent_type: str, tools: list = None, provider: Optional[str] = None, **llm_kwargs) -> Agent:
    """
    创建指定类型的智能体
    
    Args:
        agent_type: 智能体类型
        tools: 智能体工具列表
        provider: LLM提供商 ('google', 'volcano', 等)
        **llm_kwargs: 传递给LLM的额外参数
        
    Returns:
        Agent实例
        
    Raises:
        ValueError: 当智能体类型未知时
    """
    if agent_type not in AGENT_ROLES:
        raise ValueError(f"未知的智能体类型: {agent_type}")
    
    role_config = AGENT_ROLES[agent_type]
    
    # 获取LLM实例，支持提供商选择
    llm_instance = get_llm(provider=provider, **llm_kwargs)
    
    return Agent(
        role=role_config["role"],
        goal=role_config["goal"],
        backstory=role_config["backstory"],
        tools=tools or [],
        llm=llm_instance,
        verbose=True,
        allow_delegation=True,
        max_iter=3
    )


def create_task(description: str, agent: Agent, expected_output: str = None) -> Task:
    """创建智能体任务"""
    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output or "分析结果和建议"
    )


class CrewManager:
    """CrewAI团队管理器"""
    
    def __init__(self, default_provider: Optional[str] = None):
        """
        初始化团队管理器
        
        Args:
            default_provider: 默认LLM提供商
        """
        self.agents = {}
        self.tasks = []
        self.crew = None
        self.default_provider = default_provider
        self.agent_providers = {}  # 记录每个智能体使用的提供商
    
    def add_agent(self, agent_type: str, tools: list = None, provider: Optional[str] = None, **llm_kwargs):
        """
        添加智能体到团队
        
        Args:
            agent_type: 智能体类型
            tools: 智能体工具列表
            provider: LLM提供商，如果为None则使用默认提供商
            **llm_kwargs: 传递给LLM的额外参数
        """
        # 确定使用的提供商
        effective_provider = provider or self.default_provider
        
        # 创建智能体
        agent = create_agent(agent_type, tools, provider=effective_provider, **llm_kwargs)
        self.agents[agent_type] = agent
        
        # 记录提供商信息
        self.agent_providers[agent_type] = effective_provider
        
        logger.info(f"添加智能体 {agent_type}，使用提供商: {effective_provider or '默认'}")
    
    def add_task(self, task_description: str, agent_type: str, expected_output: str = None):
        """添加任务"""
        if agent_type not in self.agents:
            raise ValueError(f"智能体 {agent_type} 不存在，请先添加智能体")
        
        task = create_task(task_description, self.agents[agent_type], expected_output)
        self.tasks.append(task)
        return task
    
    def create_crew(self):
        """创建智能体团队"""
        if not self.agents or not self.tasks:
            raise ValueError("请先添加智能体和任务")
        
        self.crew = Crew(
            agents=list(self.agents.values()),
            tasks=self.tasks,
            verbose=True,
            process="sequential"  # 可选: sequential, hierarchical
        )
        return self.crew
    
    def execute(self, inputs: dict = None):
        """执行智能体团队任务"""
        if not self.crew:
            self.create_crew()
        
        return self.crew.kickoff(inputs=inputs or {})


# 向后兼容性函数
def get_available_providers() -> list:
    """
    获取可用的LLM提供商列表
    
    Returns:
        可用提供商名称列表
    """
    try:
        provider_manager = get_provider_manager()
        return provider_manager.get_available_providers()
    except Exception as e:
        logger.warning(f"无法获取提供商列表: {e}")
        return ["google"]  # 回退到默认的Google提供商


def check_provider_health(provider: str) -> bool:
    """
    检查提供商健康状态
    
    Args:
        provider: 提供商名称
        
    Returns:
        是否健康
    """
    try:
        provider_manager = get_provider_manager()
        result = provider_manager.health_check(provider)
        return result.status.value in ["available", "degraded"]
    except Exception as e:
        logger.warning(f"无法检查提供商 {provider} 的健康状态: {e}")
        return provider == "google"  # 假设Google提供商总是可用


def get_provider_info(provider: str = None) -> dict:
    """
    获取提供商信息
    
    Args:
        provider: 提供商名称，如果为None则返回所有提供商信息
        
    Returns:
        提供商信息字典
    """
    try:
        provider_manager = get_provider_manager()
        if provider:
            return provider_manager.get_provider_info(provider) or {}
        else:
            return provider_manager.get_system_info()
    except Exception as e:
        logger.warning(f"无法获取提供商信息: {e}")
        return {}


def create_multi_provider_crew(agent_configs: list, default_provider: str = None) -> CrewManager:
    """
    创建支持多提供商的智能体团队
    
    Args:
        agent_configs: 智能体配置列表，每个配置包含 {
            'type': str,
            'tools': list,
            'provider': str (可选),
            'llm_kwargs': dict (可选)
        }
        default_provider: 默认提供商
        
    Returns:
        配置好的CrewManager实例
        
    Example:
        configs = [
            {'type': 'event_analyst', 'provider': 'volcano'},
            {'type': 'retention_analyst', 'provider': 'google'},
            {'type': 'report_generator'}  # 使用默认提供商
        ]
        crew_manager = create_multi_provider_crew(configs, default_provider='google')
    """
    crew_manager = CrewManager(default_provider=default_provider)
    
    for config in agent_configs:
        agent_type = config['type']
        tools = config.get('tools', [])
        provider = config.get('provider')
        llm_kwargs = config.get('llm_kwargs', {})
        
        crew_manager.add_agent(
            agent_type=agent_type,
            tools=tools,
            provider=provider,
            **llm_kwargs
        )
    
    logger.info(f"创建多提供商智能体团队，包含 {len(agent_configs)} 个智能体")
    return crew_manager


# 向后兼容的便利函数
def create_google_agent(agent_type: str, tools: list = None) -> Agent:
    """
    创建使用Google LLM的智能体（向后兼容）
    
    Args:
        agent_type: 智能体类型
        tools: 工具列表
        
    Returns:
        Agent实例
    """
    return create_agent(agent_type, tools, provider="google")


def create_volcano_agent(agent_type: str, tools: list = None) -> Agent:
    """
    创建使用Volcano LLM的智能体
    
    Args:
        agent_type: 智能体类型
        tools: 工具列表
        
    Returns:
        Agent实例
    """
    return create_agent(agent_type, tools, provider="volcano")
    
    def set_default_provider(self, provider: str):
        """
        设置默认提供商
        
        Args:
            provider: 提供商名称
        """
        self.default_provider = provider
        logger.info(f"设置默认提供商为: {provider}")
    
    def get_agent_provider(self, agent_type: str) -> Optional[str]:
        """
        获取智能体使用的提供商
        
        Args:
            agent_type: 智能体类型
            
        Returns:
            提供商名称，如果不存在则返回None
        """
        return self.agent_providers.get(agent_type)
    
    def get_all_agent_providers(self) -> dict:
        """
        获取所有智能体的提供商信息
        
        Returns:
            智能体类型到提供商的映射字典
        """
        return self.agent_providers.copy()
    
    def update_agent_provider(self, agent_type: str, provider: str, **llm_kwargs):
        """
        更新智能体的提供商
        
        Args:
            agent_type: 智能体类型
            provider: 新的提供商
            **llm_kwargs: 传递给LLM的额外参数
        """
        if agent_type not in self.agents:
            raise ValueError(f"智能体 {agent_type} 不存在")
        
        # 获取原有的工具
        original_agent = self.agents[agent_type]
        tools = original_agent.tools if hasattr(original_agent, 'tools') else []
        
        # 重新创建智能体
        new_agent = create_agent(agent_type, tools, provider=provider, **llm_kwargs)
        self.agents[agent_type] = new_agent
        
        # 更新提供商记录
        self.agent_providers[agent_type] = provider
        
        # 如果已经创建了crew，需要重新创建
        if self.crew:
            logger.warning("智能体提供商已更新，需要重新创建团队")
            self.crew = None
        
        logger.info(f"智能体 {agent_type} 的提供商已更新为: {provider}")
    
    def get_crew_info(self) -> dict:
        """
        获取团队信息
        
        Returns:
            团队信息字典
        """
        return {
            "total_agents": len(self.agents),
            "total_tasks": len(self.tasks),
            "default_provider": self.default_provider,
            "agent_providers": self.agent_providers.copy(),
            "crew_created": self.crew is not None
        }