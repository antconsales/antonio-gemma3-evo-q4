"""
Base Tool Interface
All tools inherit from this base class
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum


class ToolType(Enum):
    """Types of tools available"""
    CALCULATOR = "calculator"
    WEB_SEARCH = "web_search"
    CODE_EXECUTOR = "code_executor"
    GPIO_CONTROL = "gpio_control"
    ASK_USER = "ask_user"
    EVOMEMORY_SEARCH = "evomemory_search"
    NONE = "none"  # Use LLM directly


@dataclass
class ToolResult:
    """Result from tool execution"""
    success: bool
    output: Any
    confidence: float  # 0-1
    error: Optional[str] = None
    metadata: Optional[Dict] = None

    def __str__(self):
        if self.success:
            return f"✓ {self.output} (confidence: {self.confidence:.2f})"
        else:
            return f"✗ Error: {self.error}"


class Tool(ABC):
    """Base class for all tools"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.usage_count = 0
        self.success_rate = 1.0

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        pass

    @abstractmethod
    def can_handle(self, question: str) -> float:
        """
        Returns confidence (0-1) that this tool can handle the question
        0.0 = cannot handle
        1.0 = perfect match
        """
        pass

    def update_stats(self, success: bool):
        """Update tool usage statistics"""
        self.usage_count += 1
        # Exponential moving average
        alpha = 0.1
        self.success_rate = (alpha * (1.0 if success else 0.0) +
                           (1 - alpha) * self.success_rate)

    def __repr__(self):
        return f"{self.name} (success rate: {self.success_rate:.2f}, uses: {self.usage_count})"
