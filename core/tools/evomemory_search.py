"""
EvoMemory Search Tool
Search past conversation neurons for similar questions/experiences
Enables Antonio to learn from past interactions
"""

import re
from typing import List, Dict, Optional
from .base import Tool, ToolResult, ToolType


class EvoMemorySearchTool(Tool):
    """
    Search Antonio's episodic memory (EvoMemory neurons)

    Use cases:
    - Find similar past questions
    - Retrieve successful strategies
    - Learn from past mistakes
    - Detect recurring patterns
    """

    def __init__(self, evomemory_instance=None):
        """
        Initialize with EvoMemory instance

        Args:
            evomemory_instance: Instance of EvoMemory class
                               (will be injected by server)
        """
        super().__init__(
            name="EvoMemorySearch",
            description="Search past conversations and learned patterns",
            tool_type=ToolType.ASSISTANT
        )

        self.evomemory = evomemory_instance

    def can_handle(self, question: str) -> float:
        """
        Detect if searching memory would be helpful

        Returns confidence 0-1
        """

        if not self.evomemory:
            return 0.0  # Cannot handle without EvoMemory

        question_lower = question.lower()

        # Strong indicators - explicit memory requests
        memory_patterns = [
            r'(ricordi|remember|recall)\s+(quando|when|if|se)',
            r'(abbiamo|we)\s+(già|already|previously)\s+(parlato|discussed|talked)',
            r'(hai|have you)\s+(già|already)\s+(risposto|answered)',
            r'(l\'altra volta|last time|before)',
            r'(come|what)\s+(ho|did I)\s+(detto|said)',
        ]

        for pattern in memory_patterns:
            if re.search(pattern, question_lower):
                return 0.9  # High confidence

        # Medium indicators - questions that could benefit from past context
        contextual_keywords = [
            'sempre', 'always', 'usually', 'normalmente', 'typically',
            'come al solito', 'as usual', 'again', 'ancora',
        ]

        if any(kw in question_lower for kw in contextual_keywords):
            return 0.6

        # Check if question is similar to recent questions
        # (This would benefit from past answers)
        if self._has_similar_recent_questions(question):
            return 0.5

        return 0.0

    async def execute(
        self,
        query: str = None,
        search_type: str = "similar",
        min_confidence: float = 0.5,
        limit: int = 5,
        **kwargs
    ) -> ToolResult:
        """
        Search EvoMemory for relevant neurons

        Args:
            query: Search query (defaults to question from kwargs)
            search_type: "similar", "exact", "pattern", "recent"
            min_confidence: Minimum confidence for results (0-1)
            limit: Maximum number of results
            **kwargs: Additional parameters (question)

        Returns:
            ToolResult with search results
        """

        if not self.evomemory:
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error="EvoMemory not initialized"
            )

        # Use question as query if not provided
        if not query:
            query = kwargs.get('question', '')

        if not query:
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error="No search query provided"
            )

        try:
            # Execute search based on type
            if search_type == "similar":
                results = self._search_similar(query, min_confidence, limit)
            elif search_type == "exact":
                results = self._search_exact(query, limit)
            elif search_type == "pattern":
                results = self._search_pattern(query, limit)
            elif search_type == "recent":
                results = self._search_recent(limit)
            else:
                return ToolResult(
                    success=False,
                    output=None,
                    confidence=0.0,
                    error=f"Unknown search type: {search_type}"
                )

            if not results:
                self.update_stats(success=True)
                return ToolResult(
                    success=True,
                    output="No relevant memories found",
                    confidence=0.3,
                    metadata={"search_type": search_type, "query": query}
                )

            # Format results
            formatted_output = self._format_results(results, search_type)

            self.update_stats(success=True)

            return ToolResult(
                success=True,
                output=formatted_output,
                confidence=self._calculate_result_confidence(results),
                metadata={
                    "search_type": search_type,
                    "query": query,
                    "result_count": len(results),
                    "neurons": results
                }
            )

        except Exception as e:
            self.update_stats(success=False)
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error=f"Memory search error: {str(e)}"
            )

    def _search_similar(self, query: str, min_confidence: float, limit: int) -> List[Dict]:
        """
        Search for similar past questions using BM25

        Returns list of neuron dicts
        """

        # Use EvoMemory's RAG-Lite system
        similar = self.evomemory.retrieve_similar(query, top_k=limit)

        # Filter by confidence
        filtered = [
            neuron for neuron in similar
            if neuron.get('confidence', 0.0) >= min_confidence
        ]

        return filtered[:limit]

    def _search_exact(self, query: str, limit: int) -> List[Dict]:
        """
        Search for exact question matches

        Returns list of neuron dicts
        """

        # Get all neurons
        all_neurons = self.evomemory.get_all_neurons()

        # Find exact matches (case-insensitive)
        query_lower = query.lower().strip()

        exact_matches = [
            neuron for neuron in all_neurons
            if neuron.get('question', '').lower().strip() == query_lower
        ]

        return exact_matches[:limit]

    def _search_pattern(self, pattern: str, limit: int) -> List[Dict]:
        """
        Search for questions matching a regex pattern

        Returns list of neuron dicts
        """

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            return []

        # Get all neurons
        all_neurons = self.evomemory.get_all_neurons()

        # Find pattern matches
        pattern_matches = [
            neuron for neuron in all_neurons
            if regex.search(neuron.get('question', ''))
        ]

        return pattern_matches[:limit]

    def _search_recent(self, limit: int) -> List[Dict]:
        """
        Get most recent neurons

        Returns list of neuron dicts
        """

        # Get all neurons (already sorted by ID, which is chronological)
        all_neurons = self.evomemory.get_all_neurons()

        # Return last N neurons
        return all_neurons[-limit:] if all_neurons else []

    def _has_similar_recent_questions(self, question: str) -> bool:
        """
        Check if similar questions exist in recent history

        Used for can_handle() decision
        """

        if not self.evomemory:
            return False

        try:
            similar = self.evomemory.retrieve_similar(question, top_k=3)
            return len(similar) > 0
        except:
            return False

    def _format_results(self, results: List[Dict], search_type: str) -> str:
        """
        Format search results for display

        Returns formatted string
        """

        if not results:
            return "No memories found"

        output = f"🧠 **EvoMemory Results** ({len(results)} found)\n\n"

        for i, neuron in enumerate(results, 1):
            neuron_id = neuron.get('id', '?')
            question = neuron.get('question', 'N/A')
            response = neuron.get('response', 'N/A')
            confidence = neuron.get('confidence', 0.0)
            timestamp = neuron.get('timestamp', 'unknown')

            # Truncate long responses
            if len(response) > 200:
                response = response[:200] + "..."

            output += f"**{i}. Neuron #{neuron_id}** (confidence: {confidence:.2f})\n"
            output += f"   📅 {timestamp}\n"
            output += f"   ❓ Q: {question}\n"
            output += f"   💬 A: {response}\n\n"

        return output.strip()

    def _calculate_result_confidence(self, results: List[Dict]) -> float:
        """
        Calculate overall confidence of search results

        Based on:
        - Number of results
        - Average confidence of neurons
        - Recency of results
        """

        if not results:
            return 0.0

        # Average neuron confidence
        avg_confidence = sum(n.get('confidence', 0.0) for n in results) / len(results)

        # Bonus for multiple results (more evidence)
        multiplicity_bonus = min(len(results) / 10.0, 0.2)

        # Combined confidence
        total_confidence = min(avg_confidence + multiplicity_bonus, 1.0)

        return total_confidence

    def get_learning_patterns(self) -> Optional[Dict]:
        """
        Analyze neurons to detect learning patterns

        Returns:
            Dict with pattern analysis or None
        """

        if not self.evomemory:
            return None

        all_neurons = self.evomemory.get_all_neurons()

        if not all_neurons:
            return None

        # Analyze patterns
        patterns = {
            'total_neurons': len(all_neurons),
            'avg_confidence': sum(n.get('confidence', 0.0) for n in all_neurons) / len(all_neurons),
            'high_confidence_count': sum(1 for n in all_neurons if n.get('confidence', 0.0) >= 0.7),
            'low_confidence_count': sum(1 for n in all_neurons if n.get('confidence', 0.0) < 0.4),
        }

        # Detect most common question types
        question_keywords = {}

        for neuron in all_neurons:
            question = neuron.get('question', '').lower()
            words = re.findall(r'\w+', question)

            for word in words:
                if len(word) > 3:  # Skip short words
                    question_keywords[word] = question_keywords.get(word, 0) + 1

        # Top keywords
        top_keywords = sorted(
            question_keywords.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        patterns['common_topics'] = dict(top_keywords)

        return patterns
