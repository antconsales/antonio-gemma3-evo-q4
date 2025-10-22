"""
Model Selector Tool
Automatically select the best LLM for each task
Antonio becomes a multi-model adaptive agent!

Strategy:
- Math/Logic → Gemma 3 (trained on reasoning)
- Code → DeepSeek Coder (specialist)
- Multilingual → Qwen 2.5 (100+ languages)
- Fast response → Phi-3 Mini (lightweight)
- Complex reasoning → Llama 3 or Mistral (larger models)
"""

import re
import subprocess
from typing import Dict, List, Optional, Tuple
from .base import Tool, ToolResult, ToolType


class ModelInfo:
    """Information about an available model"""

    def __init__(
        self,
        name: str,
        size_gb: float,
        strengths: List[str],
        weaknesses: List[str],
        speed_rating: float  # 0-1, higher = faster
    ):
        self.name = name
        self.size_gb = size_gb
        self.strengths = strengths
        self.weaknesses = weaknesses
        self.speed_rating = speed_rating


# Model registry
MODEL_REGISTRY = {
    "gemma3:1b": ModelInfo(
        name="gemma3:1b",
        size_gb=0.7,
        strengths=["math", "reasoning", "bilingual", "fast"],
        weaknesses=["complex_code", "very_long_context"],
        speed_rating=0.95
    ),
    "gemma3:3b": ModelInfo(
        name="gemma3:3b",
        size_gb=2.0,
        strengths=["math", "reasoning", "code", "bilingual"],
        weaknesses=["speed_on_pi"],
        speed_rating=0.6
    ),
    "llama3.2:1b": ModelInfo(
        name="llama3.2:1b",
        size_gb=0.7,
        strengths=["fast", "general", "efficient"],
        weaknesses=["advanced_math", "specialized_tasks"],
        speed_rating=0.98
    ),
    "llama3.2:3b": ModelInfo(
        name="llama3.2:3b",
        size_gb=2.0,
        strengths=["reasoning", "code", "general"],
        weaknesses=["speed_on_pi"],
        speed_rating=0.65
    ),
    "qwen2.5:1.5b": ModelInfo(
        name="qwen2.5:1.5b",
        size_gb=1.0,
        strengths=["multilingual", "fast", "efficient"],
        weaknesses=["specialized_reasoning"],
        speed_rating=0.9
    ),
    "phi-3:mini": ModelInfo(
        name="phi-3:mini",
        size_gb=2.3,
        strengths=["reasoning", "efficient", "code"],
        weaknesses=["speed_on_pi"],
        speed_rating=0.7
    ),
    "deepseek-coder:1.3b": ModelInfo(
        name="deepseek-coder:1.3b",
        size_gb=0.8,
        strengths=["code", "programming", "debug"],
        weaknesses=["general_conversation", "creative_writing"],
        speed_rating=0.85
    ),
    "mistral:7b": ModelInfo(
        name="mistral:7b",
        size_gb=4.1,
        strengths=["complex_reasoning", "code", "creative", "multilingual"],
        weaknesses=["requires_8gb_ram", "slow_on_pi"],
        speed_rating=0.3
    ),
}


class ModelSelectorTool(Tool):
    """
    Select the best LLM model for a given task

    Philosophy:
    - Use smallest/fastest model that can handle the task
    - Respect hardware constraints
    - Switch models transparently
    - Learn from past model performance (via EvoMemory)
    """

    def __init__(self, hardware_monitor=None, evomemory=None):
        super().__init__(
            name="ModelSelector",
            description="Select optimal LLM for each task",
            tool_type=ToolType.SYSTEM
        )

        self.hardware_monitor = hardware_monitor
        self.evomemory = evomemory
        self.current_model = None
        self.available_models = []

        # Detect available models
        self._detect_available_models()

    def can_handle(self, question: str) -> float:
        """
        Detect if model switching would improve response

        Returns confidence 0-1
        """

        # This tool is meta - it doesn't handle questions directly
        # It's called by the system to decide which model to use
        return 0.0

    async def execute(
        self,
        task_type: str = "auto_detect",
        question: str = None,
        **kwargs
    ) -> ToolResult:
        """
        Select best model for task

        Args:
            task_type: "math", "code", "general", "creative", "auto_detect"
            question: The user's question (for auto-detection)

        Returns:
            ToolResult with recommended model
        """

        # Auto-detect task type from question
        if task_type == "auto_detect" and question:
            task_type = self._detect_task_type(question)

        # Get hardware constraints
        ram_available_gb = 4.0  # Default
        if self.hardware_monitor:
            try:
                hw_summary = self.hardware_monitor._get_summary()
                ram_available_gb = hw_summary['data'].get('ram_available_gb', 4.0)
            except:
                pass

        # Select best model
        best_model, reason = self._select_best_model(
            task_type=task_type,
            ram_available_gb=ram_available_gb,
            question=question
        )

        if not best_model:
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error="No suitable model found"
            )

        self.update_stats(success=True)

        formatted = f"""🤖 **MODEL RECOMMENDATION**

**Task**: {task_type}
**Recommended**: {best_model.name}
**Reason**: {reason}

**Model Info**:
- Size: {best_model.size_gb:.1f} GB
- Speed: {best_model.speed_rating * 100:.0f}/100
- Strengths: {', '.join(best_model.strengths)}

RAM Available: {ram_available_gb:.1f} GB ✅"""

        return ToolResult(
            success=True,
            output=formatted,
            confidence=0.9,
            metadata={
                'recommended_model': best_model.name,
                'task_type': task_type,
                'reason': reason
            }
        )

    def _detect_available_models(self):
        """Detect which models are available locally"""

        try:
            # Run ollama list
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Parse output
                lines = result.stdout.strip().split('\n')[1:]  # Skip header

                for line in lines:
                    parts = line.split()
                    if parts:
                        model_name = parts[0]

                        # Check if in registry
                        if model_name in MODEL_REGISTRY:
                            self.available_models.append(model_name)

        except Exception as e:
            print(f"Could not detect models: {e}")
            # Default to Gemma 3 1B
            self.available_models = ["gemma3:1b"]

    def _detect_task_type(self, question: str) -> str:
        """
        Detect task type from question content

        Returns: "math", "code", "creative", "multilingual", "general"
        """

        question_lower = question.lower()

        # Math patterns
        math_patterns = [
            r'\d+\s*[+\-*/×÷]\s*\d+',
            r'(calcola|calculate|quanto|how much)',
            r'(percentuale|percentage|frazione|fraction)',
            r'(equazione|equation|formula)',
        ]

        if any(re.search(p, question_lower) for p in math_patterns):
            return "math"

        # Code patterns
        code_patterns = [
            r'(python|javascript|java|c\+\+|rust|go)',
            r'(codice|code|programma|program|script)',
            r'(funzione|function|classe|class)',
            r'(debug|error|fix|bug)',
            r'def\s+\w+|function\s+\w+|class\s+\w+',
        ]

        if any(re.search(p, question_lower) for p in code_patterns):
            return "code"

        # Creative patterns
        creative_patterns = [
            r'(scrivi|write)\s+(una\s+)?(storia|story|poesia|poem)',
            r'(immagina|imagine|crea|create)',
            r'(creativo|creative|fantasioso|imaginative)',
        ]

        if any(re.search(p, question_lower) for p in creative_patterns):
            return "creative"

        # Multilingual (non-IT/EN)
        multilingual_keywords = [
            '中文', '日本', 'français', 'español', 'deutsch',
            'português', 'русский', 'العربية'
        ]

        if any(kw in question_lower for kw in multilingual_keywords):
            return "multilingual"

        # Default
        return "general"

    def _select_best_model(
        self,
        task_type: str,
        ram_available_gb: float,
        question: Optional[str] = None
    ) -> Tuple[Optional[ModelInfo], str]:
        """
        Select best model based on task and constraints

        Returns:
            (ModelInfo, reason) or (None, error_msg)
        """

        # Filter models by RAM availability
        viable_models = [
            MODEL_REGISTRY[name]
            for name in self.available_models
            if MODEL_REGISTRY[name].size_gb + 0.5 <= ram_available_gb  # +0.5 for overhead
        ]

        if not viable_models:
            return (None, "No models fit in available RAM")

        # Score each model for this task
        scored_models = []

        for model in viable_models:
            score = self._score_model_for_task(model, task_type, ram_available_gb)
            scored_models.append((model, score))

        # Sort by score
        scored_models.sort(key=lambda x: x[1], reverse=True)

        best_model, best_score = scored_models[0]

        # Generate reason
        reason = self._generate_selection_reason(best_model, task_type)

        return (best_model, reason)

    def _score_model_for_task(
        self,
        model: ModelInfo,
        task_type: str,
        ram_available_gb: float
    ) -> float:
        """
        Score a model for a specific task

        Returns score 0-100
        """

        score = 50.0  # Base score

        # Task-specific bonuses
        task_strength_map = {
            "math": ["math", "reasoning"],
            "code": ["code", "programming", "debug"],
            "creative": ["creative", "general"],
            "multilingual": ["multilingual"],
            "general": ["general", "fast"],
        }

        relevant_strengths = task_strength_map.get(task_type, [])

        for strength in model.strengths:
            if strength in relevant_strengths:
                score += 20.0
            elif strength in ["fast", "efficient"]:
                score += 5.0  # Always good

        # Speed bonus (important on Pi)
        score += model.speed_rating * 15.0

        # RAM efficiency bonus
        ram_usage_ratio = model.size_gb / ram_available_gb
        if ram_usage_ratio < 0.3:  # Using <30% of RAM
            score += 10.0
        elif ram_usage_ratio > 0.7:  # Using >70% of RAM
            score -= 10.0

        return score

    def _generate_selection_reason(self, model: ModelInfo, task_type: str) -> str:
        """Generate human-readable reason for model selection"""

        reasons = []

        if task_type in model.strengths:
            reasons.append(f"Optimized for {task_type}")

        if model.speed_rating > 0.8:
            reasons.append("Fast on Raspberry Pi")

        if model.size_gb < 1.0:
            reasons.append("Lightweight and efficient")

        if not reasons:
            reasons.append("Best available option")

        return " • ".join(reasons)

    def get_model_comparison(self) -> str:
        """Get formatted comparison of all available models"""

        if not self.available_models:
            return "⚠️ No models available"

        formatted = "🤖 **AVAILABLE MODELS**\n\n"

        for model_name in self.available_models:
            model = MODEL_REGISTRY[model_name]

            formatted += f"**{model.name}**\n"
            formatted += f"  Size: {model.size_gb:.1f} GB\n"
            formatted += f"  Speed: {model.speed_rating * 100:.0f}/100\n"
            formatted += f"  Best for: {', '.join(model.strengths)}\n"
            formatted += f"  Limitations: {', '.join(model.weaknesses)}\n\n"

        return formatted
