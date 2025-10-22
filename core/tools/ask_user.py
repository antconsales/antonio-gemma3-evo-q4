"""
Ask User Tool
Prompts user for clarification when question is ambiguous
Part of Antonio's self-aware reasoning system
"""

import re
from typing import Optional, List
from .base import Tool, ToolResult, ToolType


class AskUserTool(Tool):
    """
    Ask clarification questions when input is ambiguous

    Philosophy:
    - Better to ask than to assume
    - Self-aware of knowledge limitations
    - Provides context for why clarification is needed
    """

    def __init__(self):
        super().__init__(
            name="AskUser",
            description="Request clarification when question is ambiguous",
            tool_type=ToolType.ASSISTANT
        )

    def can_handle(self, question: str) -> float:
        """
        Detect ambiguous or unclear questions

        Returns confidence 0-1
        """
        question_lower = question.lower()

        # Strong indicators of ambiguity
        ambiguous_patterns = [
            r'\b(questo|questo qui|that|it)\b',  # Pronoun without antecedent
            r'\b(cosa|what)\s*\?$',  # Just "what?"
            r'\b(come|how)\s*\?$',   # Just "how?"
            r'\b(perché|why)\s*\?$', # Just "why?"
            r'^(e\s+)?poi\?$',       # Just "and then?"
        ]

        for pattern in ambiguous_patterns:
            if re.search(pattern, question_lower):
                return 0.7

        # Detect very short questions (likely missing context)
        words = question.split()
        if len(words) <= 2 and question.endswith('?'):
            return 0.6

        # Detect multiple interpretations
        multi_interpretation_keywords = [
            'oppure', 'or', 'either', 'quale', 'which'
        ]

        if any(kw in question_lower for kw in multi_interpretation_keywords):
            # Check if there are multiple options without clear preference
            if '?' in question and not any(pref in question_lower for pref in ['preferisco', 'prefer', 'meglio', 'better']):
                return 0.5

        # Detect contradictions
        if any(contr in question_lower for contr in ['ma anche', 'but also', 'però', 'however']):
            return 0.4

        return 0.0

    async def execute(
        self,
        clarification_type: str = "ambiguous",
        context: str = None,
        options: List[str] = None,
        **kwargs
    ) -> ToolResult:
        """
        Generate clarification question for user

        Args:
            clarification_type: Type of clarification needed
                - "ambiguous": Question unclear
                - "missing_info": Need more information
                - "multiple_options": Multiple interpretations
                - "confirmation": Confirm understanding
            context: Why clarification is needed
            options: Possible interpretations (for multiple_options type)
            **kwargs: Additional parameters (original question)

        Returns:
            ToolResult with clarification question
        """

        original_question = kwargs.get('question', '')

        # Generate appropriate clarification based on type
        if clarification_type == "ambiguous":
            clarification = self._generate_ambiguous_clarification(original_question, context)

        elif clarification_type == "missing_info":
            clarification = self._generate_missing_info_clarification(original_question, context)

        elif clarification_type == "multiple_options":
            clarification = self._generate_options_clarification(original_question, options)

        elif clarification_type == "confirmation":
            clarification = self._generate_confirmation(original_question, context)

        else:
            clarification = f"Puoi chiarire meglio la tua domanda?\n\nDomanda originale: \"{original_question}\""

        self.update_stats(success=True)

        return ToolResult(
            success=True,
            output=clarification,
            confidence=0.9,  # High confidence in needing clarification
            metadata={
                "type": clarification_type,
                "original_question": original_question,
                "requires_user_response": True
            }
        )

    def _generate_ambiguous_clarification(self, question: str, context: Optional[str]) -> str:
        """Generate clarification for ambiguous question"""

        clarification = "🤔 La tua domanda non è del tutto chiara.\n\n"

        if context:
            clarification += f"**Motivo**: {context}\n\n"

        clarification += f"**Domanda originale**: \"{question}\"\n\n"
        clarification += "Puoi riformularla con più dettagli? Ad esempio:\n"
        clarification += "- Cosa vuoi sapere esattamente?\n"
        clarification += "- C'è un contesto specifico?\n"
        clarification += "- Hai bisogno di un esempio pratico?"

        return clarification

    def _generate_missing_info_clarification(self, question: str, context: Optional[str]) -> str:
        """Generate clarification when information is missing"""

        clarification = "ℹ️  Mi mancano alcune informazioni per rispondere correttamente.\n\n"

        if context:
            clarification += f"**Cosa mi serve**: {context}\n\n"

        clarification += "Puoi fornire:\n"

        # Detect what type of information might be missing
        question_lower = question.lower()

        if any(kw in question_lower for kw in ['calcola', 'calculate', 'quanto', 'how much']):
            clarification += "- I numeri/valori specifici\n"
            clarification += "- L'unità di misura\n"

        if any(kw in question_lower for kw in ['codice', 'code', 'programma', 'program']):
            clarification += "- Il linguaggio di programmazione\n"
            clarification += "- Cosa deve fare il codice\n"

        if any(kw in question_lower for kw in ['quando', 'when', 'dove', 'where']):
            clarification += "- Il contesto temporale/spaziale\n"

        clarification += "\n**Domanda originale**: \"" + question + "\""

        return clarification

    def _generate_options_clarification(self, question: str, options: Optional[List[str]]) -> str:
        """Generate clarification when multiple interpretations exist"""

        clarification = "🔀 La tua domanda potrebbe avere più interpretazioni.\n\n"
        clarification += f"**Domanda**: \"{question}\"\n\n"

        if options:
            clarification += "**Intendevi**:\n\n"
            for i, option in enumerate(options, 1):
                clarification += f"{i}. {option}\n"

            clarification += "\nIndicami il numero dell'opzione corretta o riformula la domanda."
        else:
            clarification += "Puoi essere più specifico su cosa intendi?"

        return clarification

    def _generate_confirmation(self, question: str, context: Optional[str]) -> str:
        """Generate confirmation question to verify understanding"""

        clarification = "✓ Fammi confermare di aver capito bene:\n\n"

        if context:
            clarification += f"{context}\n\n"

        clarification += "È corretto? Se no, correggimi pure!"

        return clarification

    def detect_clarification_needed(self, question: str) -> Optional[dict]:
        """
        Analyze question and suggest what clarification is needed

        Returns:
            Dict with clarification_type and suggested_response
            or None if no clarification needed
        """

        question_lower = question.lower()

        # Check for pronouns without clear antecedent
        pronouns = ['questo', 'quello', 'it', 'that', 'these', 'those']
        if any(p in question_lower for p in pronouns):
            # Check if there's context (previous conversation)
            # For now, simplified check
            if len(question.split()) < 5:
                return {
                    'type': 'ambiguous',
                    'context': 'Hai usato un pronome ma non ho il contesto della conversazione precedente'
                }

        # Check for very short questions
        if len(question.split()) <= 2 and question.endswith('?'):
            return {
                'type': 'missing_info',
                'context': 'Domanda troppo breve - aggiungi più dettagli'
            }

        # Check for contradictory keywords
        if 'ma' in question_lower and 'anche' in question_lower:
            return {
                'type': 'ambiguous',
                'context': 'La domanda sembra contenere elementi contraddittori'
            }

        # Check for choice questions without clear preference
        if ('oppure' in question_lower or 'or' in question_lower):
            # Extract options
            parts = re.split(r'\s+o(ppure)?\s+', question, flags=re.IGNORECASE)
            if len(parts) >= 2:
                return {
                    'type': 'multiple_options',
                    'options': [p.strip(' ?') for p in parts]
                }

        return None


class ClarificationContext:
    """
    Manages clarification conversation flow

    Tracks:
    - Original question
    - Clarification asked
    - User's clarification response
    - Resolved question
    """

    def __init__(self):
        self.history = []

    def add_clarification(
        self,
        original_question: str,
        clarification_asked: str,
        user_response: Optional[str] = None
    ):
        """Record a clarification interaction"""

        self.history.append({
            'original': original_question,
            'clarification': clarification_asked,
            'response': user_response,
            'resolved': user_response is not None
        })

    def get_resolved_question(self, original_question: str) -> Optional[str]:
        """
        Get the resolved version of a question after clarification

        Returns:
            Resolved question or None if not found/resolved
        """
        for item in reversed(self.history):
            if item['original'] == original_question and item['resolved']:
                return item['response']

        return None

    def needs_clarification(self, question: str) -> bool:
        """Check if this question already has a pending clarification"""

        for item in self.history:
            if item['original'] == question and not item['resolved']:
                return False  # Already asked, waiting for response

        return True
