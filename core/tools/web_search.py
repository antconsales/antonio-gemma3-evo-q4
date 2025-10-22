"""
Web Search Tool
Searches the web for factual information
Uses DuckDuckGo (no API key required, privacy-friendly)
"""

import re
import asyncio
from typing import List, Dict
from .base import Tool, ToolResult


class WebSearchTool(Tool):
    """
    Web search for factual queries
    Uses DuckDuckGo instant answers + web scraping
    """

    def __init__(self):
        super().__init__(
            name="WebSearch",
            description="Search the web for facts, current events, definitions"
        )
        self.cache = {}  # Simple cache for repeated queries

    def can_handle(self, question: str) -> float:
        """
        Detect if question requires web search
        Returns confidence 0-1
        """
        question_lower = question.lower()

        # Strong indicators - factual questions
        strong_patterns = [
            r'(chi è|who is|what is|cos\'è)',
            r'(capitale|capital)\s+(di|of)',
            r'(quando|when)\s+(è nato|was born|happened)',
            r'(dove|where)\s+(si trova|is located)',
            r'(attuale|current|latest|ultimo)',
            r'(notizie|news|today)',
        ]

        for pattern in strong_patterns:
            if re.search(pattern, question_lower):
                return 0.8  # High confidence

        # Medium indicators
        factual_keywords = [
            'wikipedia', 'definizione', 'definition', 'significa',
            'anno', 'year', 'data', 'date', 'informazioni', 'information'
        ]

        if any(kw in question_lower for kw in factual_keywords):
            return 0.6  # Medium confidence

        # Low indicators - simple factual structure
        if question.endswith('?') and len(question.split()) <= 10:
            # Short factual-looking question
            if re.search(r'(qual|what|which|quando|when|dove|where|chi|who)', question_lower):
                return 0.4  # Low-medium confidence

        return 0.0  # Cannot handle

    async def execute(self, query: str = None, **kwargs) -> ToolResult:
        """
        Search the web for information

        Args:
            query: Search query string
        """
        if not query:
            query = kwargs.get('question', '')

        if not query:
            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error="No search query provided"
            )

        # Check cache
        cache_key = query.lower().strip()
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            return ToolResult(
                success=True,
                output=cached['answer'],
                confidence=cached['confidence'],
                metadata={"source": "cache", "url": cached.get('url')}
            )

        try:
            # Use DuckDuckGo instant answer API (no key required)
            result = await self._duckduckgo_search(query)

            if result['success']:
                # Cache result
                self.cache[cache_key] = result

                self.update_stats(success=True)

                return ToolResult(
                    success=True,
                    output=result['answer'],
                    confidence=result['confidence'],
                    metadata={"source": "duckduckgo", "url": result.get('url')}
                )
            else:
                self.update_stats(success=False)

                return ToolResult(
                    success=False,
                    output=None,
                    confidence=0.0,
                    error="No results found"
                )

        except Exception as e:
            self.update_stats(success=False)

            return ToolResult(
                success=False,
                output=None,
                confidence=0.0,
                error=f"Search error: {str(e)}"
            )

    async def _duckduckgo_search(self, query: str) -> Dict:
        """
        Search using DuckDuckGo Instant Answer API
        Free, no API key, privacy-friendly
        """
        try:
            import urllib.parse
            import urllib.request
            import json

            # DuckDuckGo Instant Answer API
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"

            # Async HTTP request
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: urllib.request.urlopen(url, timeout=5).read()
            )

            data = json.loads(response)

            # Extract answer
            answer = None
            confidence = 0.0
            source_url = None

            # Try different result types
            if data.get('AbstractText'):
                answer = data['AbstractText']
                source_url = data.get('AbstractURL')
                confidence = 0.9  # High confidence for abstracts

            elif data.get('Answer'):
                answer = data['Answer']
                confidence = 0.95  # Very high for direct answers

            elif data.get('Definition'):
                answer = data['Definition']
                source_url = data.get('DefinitionURL')
                confidence = 0.85

            elif data.get('RelatedTopics'):
                # First related topic
                topics = data['RelatedTopics']
                if topics and isinstance(topics[0], dict):
                    answer = topics[0].get('Text', '')
                    source_url = topics[0].get('FirstURL')
                    confidence = 0.7  # Lower confidence for related topics

            if answer:
                return {
                    'success': True,
                    'answer': answer,
                    'confidence': confidence,
                    'url': source_url
                }
            else:
                return {'success': False}

        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return {'success': False}

    def clear_cache(self):
        """Clear search cache"""
        self.cache = {}
