"""
Antonio Evo Tools System v0.5.0
Complete adaptive agent toolkit with self-awareness and growth capabilities

Tools Categories:
- COMPUTATION: Calculator, CodeExecutor
- KNOWLEDGE: WebSearch, EvoMemorySearch
- SYSTEM: HardwareMonitor, GPIOController, SelfUpgrade, SelfOptimize
- ASSISTANT: AskUser

Architecture:
- ToolSelector: Routes questions to best tool
- ToolOrchestrator: Chains multiple tools for complex tasks
- Each tool has can_handle() for self-awareness

Platform-aware: Adapts to Pi/Mac/Linux/Windows automatically
"""

# Legacy broker (kept for compatibility)
try:
    from .broker import ActionBroker, ToolResult as BrokerToolResult, ToolType as BrokerToolType
    BROKER_AVAILABLE = True
except ImportError:
    BROKER_AVAILABLE = False

# New adaptive tools system
from .base import Tool, ToolResult, ToolType
from .tool_selector import ToolSelector, ToolOrchestrator, quick_select
from .calculator import CalculatorTool
from .web_search import WebSearchTool
from .code_executor import CodeExecutorTool
from .gpio_controller import GPIOControllerTool
from .ask_user import AskUserTool, ClarificationContext
from .evomemory_search import EvoMemorySearchTool
from .hardware_monitor import HardwareMonitorTool
from .self_upgrade import SelfUpgradeTool
from .self_optimize import SelfOptimizeTool

__all__ = [
    # Base classes
    'Tool',
    'ToolResult',
    'ToolType',

    # Tool selection
    'ToolSelector',
    'ToolOrchestrator',
    'quick_select',

    # Computation tools
    'CalculatorTool',
    'CodeExecutorTool',

    # Knowledge tools
    'WebSearchTool',
    'EvoMemorySearchTool',

    # System tools
    'HardwareMonitorTool',
    'GPIOControllerTool',
    'SelfUpgradeTool',
    'SelfOptimizeTool',

    # Assistant tools
    'AskUserTool',
    'ClarificationContext',
]

# Add broker if available
if BROKER_AVAILABLE:
    __all__.extend(['ActionBroker', 'BrokerToolResult', 'BrokerToolType'])

__version__ = '0.5.0'
__author__ = 'Antonio Consales'


def create_default_toolset(evomemory=None, enable_gpio=True):
    """
    Create the default set of tools for Antonio

    Args:
        evomemory: EvoMemory instance (optional)
        enable_gpio: Enable GPIO control (Pi only)

    Returns:
        List of initialized tools
    """

    # Initialize hardware monitor first (others depend on it)
    hardware_monitor = HardwareMonitorTool()

    # Create all tools
    tools = [
        # Computation
        CalculatorTool(),
        CodeExecutorTool(),

        # Knowledge
        WebSearchTool(),
        EvoMemorySearchTool(evomemory_instance=evomemory),

        # System
        hardware_monitor,
        GPIOControllerTool(enable_gpio=enable_gpio),
        SelfUpgradeTool(
            hardware_monitor=hardware_monitor,
            evomemory=evomemory
        ),
        SelfOptimizeTool(
            evomemory=evomemory,
            hardware_monitor=hardware_monitor
        ),

        # Assistant
        AskUserTool(),
    ]

    return tools


def create_tool_selector(evomemory=None, enable_gpio=True, min_confidence=0.6):
    """
    Create a ToolSelector with default toolset

    Args:
        evomemory: EvoMemory instance (optional)
        enable_gpio: Enable GPIO control (Pi only)
        min_confidence: Minimum confidence to use tool (0-1)

    Returns:
        Configured ToolSelector instance
    """

    tools = create_default_toolset(evomemory=evomemory, enable_gpio=enable_gpio)
    selector = ToolSelector(tools, min_confidence=min_confidence)

    return selector
