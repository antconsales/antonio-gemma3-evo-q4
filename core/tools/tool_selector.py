"""
Tool Selector - Core Decision Engine
Evaluates all available tools and routes questions to the best one
Part of Antonio's adaptive agent architecture
"""

import asyncio
from typing import List, Optional, Dict, Tuple
from .base import Tool, ToolResult, ToolType


class ToolSelector:
    """
    Decision engine for Antonio's adaptive agent system

    Responsibilities:
    - Evaluate all tools for a given question
    - Select the best tool based on confidence scores
    - Fall back to LLM if no tool is confident enough
    - Log tool selection decisions for learning
    """

    def __init__(self, tools: List[Tool], min_confidence: float = 0.6):
        """
        Initialize tool selector

        Args:
            tools: List of available tools
            min_confidence: Minimum confidence (0-1) required to use a tool
        """
        self.tools = tools
        self.min_confidence = min_confidence
        self.selection_history = []  # For analytics

    async def select_tool(self, question: str) -> Tuple[Optional[Tool], float, Dict]:
        """
        Select the best tool for a question

        Args:
            question: User's question

        Returns:
            Tuple of (selected_tool, confidence, metadata)
            - selected_tool: Tool instance or None (use LLM)
            - confidence: Confidence score of selection
            - metadata: Decision details for logging
        """

        # Evaluate all tools in parallel
        evaluations = await asyncio.gather(
            *[self._evaluate_tool(tool, question) for tool in self.tools]
        )

        # Sort by confidence
        evaluations.sort(key=lambda x: x[1], reverse=True)

        # Get best match
        best_tool, best_confidence = evaluations[0]

        # Prepare metadata
        metadata = {
            "question": question,
            "evaluations": [
                {"tool": tool.name, "confidence": conf}
                for tool, conf in evaluations
            ],
            "selected_tool": best_tool.name if best_tool else "LLM",
            "confidence": best_confidence,
            "threshold": self.min_confidence
        }

        # Decision logic
        if best_confidence >= self.min_confidence:
            # Use tool
            decision = (best_tool, best_confidence, metadata)
            metadata["decision"] = "USE_TOOL"
        else:
            # Fall back to LLM
            decision = (None, 0.0, metadata)
            metadata["decision"] = "USE_LLM"
            metadata["reason"] = "No tool confident enough"

        # Log decision
        self.selection_history.append(metadata)

        return decision

    async def _evaluate_tool(self, tool: Tool, question: str) -> Tuple[Tool, float]:
        """
        Evaluate a single tool's confidence for handling a question

        Returns:
            Tuple of (tool, confidence_score)
        """
        try:
            confidence = tool.can_handle(question)
            return (tool, confidence)
        except Exception as e:
            print(f"Error evaluating {tool.name}: {e}")
            return (tool, 0.0)

    async def execute_with_tool(
        self,
        question: str,
        **kwargs
    ) -> Tuple[ToolResult, Dict]:
        """
        Full pipeline: select tool → execute → return result

        Args:
            question: User's question
            **kwargs: Additional parameters for tool execution

        Returns:
            Tuple of (tool_result, selection_metadata)
        """

        # Select best tool
        selected_tool, confidence, metadata = await self.select_tool(question)

        if selected_tool:
            # Execute tool
            try:
                result = await selected_tool.execute(question=question, **kwargs)
                metadata["execution_success"] = result.success
                metadata["execution_error"] = result.error

                return (result, metadata)

            except Exception as e:
                # Tool failed - return error result
                metadata["execution_success"] = False
                metadata["execution_error"] = str(e)

                return (
                    ToolResult(
                        success=False,
                        output=None,
                        confidence=0.0,
                        error=f"Tool execution failed: {str(e)}"
                    ),
                    metadata
                )
        else:
            # No tool selected - signal to use LLM
            return (
                ToolResult(
                    success=False,
                    output=None,
                    confidence=0.0,
                    error="No suitable tool found - use LLM"
                ),
                metadata
            )

    def get_tool_by_name(self, name: str) -> Optional[Tool]:
        """Get a specific tool by name"""
        for tool in self.tools:
            if tool.name.lower() == name.lower():
                return tool
        return None

    def get_tools_by_type(self, tool_type: ToolType) -> List[Tool]:
        """Get all tools of a specific type"""
        return [tool for tool in self.tools if tool.tool_type == tool_type]

    def get_selection_stats(self) -> Dict:
        """
        Get statistics about tool selection patterns
        Useful for fine-tuning and optimization
        """
        if not self.selection_history:
            return {"total_selections": 0}

        total = len(self.selection_history)
        tool_used = sum(1 for s in self.selection_history if s["decision"] == "USE_TOOL")
        llm_used = total - tool_used

        # Count by tool
        tool_counts = {}
        for selection in self.selection_history:
            tool_name = selection["selected_tool"]
            tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

        # Average confidence when tools are used
        tool_confidences = [
            s["confidence"]
            for s in self.selection_history
            if s["decision"] == "USE_TOOL"
        ]
        avg_tool_confidence = sum(tool_confidences) / len(tool_confidences) if tool_confidences else 0.0

        return {
            "total_selections": total,
            "tools_used": tool_used,
            "llm_used": llm_used,
            "tool_usage_rate": tool_used / total if total > 0 else 0.0,
            "tool_counts": tool_counts,
            "avg_tool_confidence": avg_tool_confidence,
            "min_confidence_threshold": self.min_confidence
        }

    def clear_history(self):
        """Clear selection history"""
        self.selection_history = []


class ToolOrchestrator:
    """
    Higher-level orchestrator for complex multi-tool workflows

    Example:
    - Question requires both web search AND calculation
    - Chain tools together based on dependencies
    """

    def __init__(self, selector: ToolSelector):
        self.selector = selector

    async def execute_workflow(
        self,
        question: str,
        max_tools: int = 3
    ) -> List[ToolResult]:
        """
        Execute a workflow that may use multiple tools

        Args:
            question: User's question
            max_tools: Maximum number of tools to chain

        Returns:
            List of ToolResults from executed tools
        """
        results = []
        current_question = question

        for i in range(max_tools):
            # Try to find a tool for current question
            result, metadata = await self.selector.execute_with_tool(current_question)

            if not result.success:
                # No tool found or tool failed - stop workflow
                break

            results.append(result)

            # Check if we need another tool
            # (This is simplified - real implementation would parse tool output)
            if not self._needs_another_tool(result):
                break

            # Prepare next question based on result
            current_question = self._prepare_next_question(result)

        return results

    def _needs_another_tool(self, result: ToolResult) -> bool:
        """
        Determine if workflow needs another tool

        Real implementation would use LLM to analyze result
        For now, simplified heuristic
        """
        # If result mentions "need to search" or "calculate", continue
        if result.output and isinstance(result.output, str):
            needs_more = any(
                keyword in result.output.lower()
                for keyword in ["need to", "should search", "calculate", "verify"]
            )
            return needs_more

        return False

    def _prepare_next_question(self, result: ToolResult) -> str:
        """
        Extract next question from previous result

        Real implementation would use LLM
        """
        # Simplified: use metadata if available
        if result.metadata and "next_query" in result.metadata:
            return result.metadata["next_query"]

        return str(result.output)


# Utility function for quick tool selection
async def quick_select(question: str, tools: List[Tool]) -> Optional[Tool]:
    """
    Quick tool selection without creating a ToolSelector instance

    Args:
        question: User's question
        tools: Available tools

    Returns:
        Best tool or None
    """
    selector = ToolSelector(tools)
    tool, confidence, _ = await selector.select_tool(question)
    return tool
