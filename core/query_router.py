"""
Query Router - Automatic model selection based on query complexity
Routes simple queries to fast model, complex queries to tool-aware model
"""

import re
from enum import Enum
from typing import Tuple


class QueryType(Enum):
    """Type of query detected"""
    SIMPLE = "simple"       # Greetings, basic questions - use fast model
    TOOL_REQUIRED = "tool"  # Requires tools (calc, search, etc) - use tool model


class QueryRouter:
    """Routes queries to appropriate model based on complexity"""

    def __init__(self):
        # Keywords that indicate tool usage needed
        self.tool_keywords = {
            # Calculation
            'calcola', 'calculate', 'quanto fa', 'how much', 'moltiplicazione',
            'divisione', 'somma', 'sottrazione', 'multiply', 'divide', 'add', 'subtract',

            # Web Search
            'cerca', 'search', 'trova', 'find', 'informazioni su', 'information about',
            'cosa dice', 'what does', 'notizie', 'news', 'quando è nato', 'when was',
            'chi è', 'who is', 'dove si trova', 'where is',

            # Date/Time
            'che giorno', 'what day', 'che ora', 'what time', 'data', 'date',

            # Weather
            'meteo', 'weather', 'temperatura', 'temperature', 'previsioni', 'forecast',

            # File/System operations
            'leggi il file', 'read file', 'scrivi file', 'write file', 'apri', 'open',
            'salva', 'save', 'cancella', 'delete',
        }

        # Simple conversation patterns
        self.simple_patterns = [
            r'^(ciao|hello|hi|hey|salve|buongiorno|buonasera)',  # Greetings
            r'^(come stai|how are you|come va)',                  # How are you
            r'^(grazie|thanks|thank you)',                        # Thanks
            r'^(chi sei|what are you|cosa sei)',                  # Who/what are you
            r'^(come ti chiami|what\'s your name)',               # Name question
            r'^(si|sì|no|yes|ok|okay)',                          # Confirmations
        ]

        # Math operators that indicate calculation
        self.math_operators = [
            r'\d+\s*[\+\-\*\/×÷]\s*\d+',  # Numbers with operators
            r'\d+\s*\^\s*\d+',             # Powers
            r'\d+\s*%\s*\d+',              # Modulo
        ]

    def classify(self, query: str) -> Tuple[QueryType, str]:
        """
        Classify query and return model to use

        Returns:
            (QueryType, reason)
        """
        query_lower = query.lower().strip()

        # Check for simple conversation patterns first
        for pattern in self.simple_patterns:
            if re.search(pattern, query_lower):
                return QueryType.SIMPLE, f"matched simple pattern: {pattern}"

        # Check for math operators
        for pattern in self.math_operators:
            if re.search(pattern, query):
                return QueryType.TOOL_REQUIRED, "math operation detected"

        # Check for tool keywords
        for keyword in self.tool_keywords:
            if keyword in query_lower:
                return QueryType.TOOL_REQUIRED, f"tool keyword: {keyword}"

        # Check query length and complexity
        words = query_lower.split()

        # Very short queries are usually simple
        if len(words) <= 3:
            return QueryType.SIMPLE, "short query"

        # Long queries with question words might need tools
        question_words = ['quando', 'where', 'dove', 'perché', 'why', 'quanto', 'how much']
        if any(qw in query_lower for qw in question_words) and len(words) > 5:
            return QueryType.TOOL_REQUIRED, "complex question detected"

        # Default to simple for general conversation
        return QueryType.SIMPLE, "default to simple conversation"

    def get_model_for_query(self, query: str) -> Tuple[str, str]:
        """
        Get the appropriate model name for the query

        Returns:
            (model_name, reason)
        """
        query_type, reason = self.classify(query)

        if query_type == QueryType.SIMPLE:
            return "antconsales/antonio-gemma3-evo-q4", f"Simple query: {reason}"
        else:
            return "antonio-tools", f"Tool required: {reason}"


if __name__ == "__main__":
    # Test router
    router = QueryRouter()

    test_queries = [
        "ciao bro",
        "come stai?",
        "calcola 1847 × 2935",
        "cerca informazioni sul PIL italiano 2024",
        "quanto fa 2+2?",
        "chi è il presidente degli Stati Uniti?",
        "grazie mille",
        "come funziona la memoria evolutiva?",
    ]

    print("Query Router - Test Results")
    print("=" * 60)

    for query in test_queries:
        model, reason = router.get_model_for_query(query)
        model_short = "FAST" if "evo-q4" in model else "TOOL"
        print(f"\nQuery: {query}")
        print(f"  → Model: {model_short} ({model})")
        print(f"  → Reason: {reason}")
