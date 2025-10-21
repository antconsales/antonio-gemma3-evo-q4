"""
Question Complexity Classifier with Extended Categories
"""

import re
from enum import IntEnum
from typing import Tuple

class Complexity(IntEnum):
    SIMPLE = 0
    MEDIUM = 1
    COMPLEX = 2
    CODE = 3      # New: Code/programming questions
    CREATIVE = 4  # New: Creative writing/storytelling

def classify_question(text: str) -> Tuple[Complexity, str]:
    """Classify question complexity and category"""
    text_lower = text.lower()

    # CODE: Programming/technical patterns
    code_keywords = [
        "python", "javascript", "function", "class", "variable",
        "codice", "programma", "funzione", "error", "bug", "debug",
        "import", "return", "def ", "const ", "let ", "var ",
        "algoritmo", "algorithm", "script", "array", "object"
    ]
    if any(kw in text_lower for kw in code_keywords):
        return Complexity.CODE, "code_detected"

    # CREATIVE: Writing/storytelling patterns
    creative_keywords = [
        "scrivi una storia", "write a story", "racconta", "tell me about",
        "immagina", "imagine", "crea", "create", "inventa", "invent",
        "poem", "poesia", "canzone", "song", "favola", "tale"
    ]
    if any(kw in text_lower for kw in creative_keywords):
        return Complexity.CREATIVE, "creative_detected"

    # COMPLEX: Math patterns (existing)
    math_patterns = [
        r'\d+\s*(più|meno|per|diviso|\+|-|×|÷|perde|loses|aggiunge|adds)',
        r'(quante|quanti|how many).*\d+',
        r'\d+.*e.*\d+',
        # Written numbers in Italian
        r'(uno|una|due|tre|quattro|cinque|sei|sette|otto|nove|dieci).*(?:zampe|zampa|mele|mela|euro|oggetti|oggetto)',
        r'(?:perde|perdere|aggiunge|aggiungere|mangia|mangiare|prende|prendere).*(?:uno|una|due|tre|quattro|cinque)',
        # Written numbers in English
        r'(one|two|three|four|five|six|seven|eight|nine|ten).*(?:legs|leg|apples|apple|items|item)',
        r'(?:loses?|adds?|eats?|takes?).*(?:one|two|three|four|five)',
    ]

    for pattern in math_patterns:
        if re.search(pattern, text_lower):
            return Complexity.COMPLEX, "math_detected"

    # COMPLEX: Logic (existing)
    if any(kw in text_lower for kw in ['quindi', 'perché', 'why', 'because']):
        return Complexity.COMPLEX, "logic_detected"

    # SIMPLE: Identity/greetings (existing)
    simple_kw = ['come ti chiami', 'name', 'chi sei', 'who are', 'ciao', 'hello']
    if any(kw in text_lower for kw in simple_kw):
        return Complexity.SIMPLE, "identity_question"

    # SIMPLE: Short questions (existing)
    if len(text.split()) <= 5 and '?' in text:
        return Complexity.SIMPLE, "short_question"

    return Complexity.MEDIUM, "default"

# System prompts
SIMPLE_SYSTEM = """You are Antonio, bilingual (IT/EN) AI. Detect language, respond in same language."""

MEDIUM_SYSTEM = """You are Antonio, bilingual AI.
Think before answering. Detect language, respond in same language."""

COMPLEX_SYSTEM = """You are Antonio, think step-by-step.

RULES:
1. Math: "X has N, loses M" → N - M
2. Break into steps, show reasoning

EXAMPLE:
Q: Se un cane ha 4 zampe e ne perde 1?
A: Ragioniamo:
   - Iniziali: 4
   - Perse: 1
   - 4 - 1 = 3
   Risposta: 3 zampe.

Detect language (IT/EN), respond same."""

CODE_SYSTEM = """You are Antonio, code assistant.

RULES:
1. Explain code clearly and concisely
2. Provide working examples
3. Include comments for clarity
4. Mention potential issues/edge cases
5. Format code properly

Detect language (IT/EN), respond same."""

CREATIVE_SYSTEM = """You are Antonio, creative writer.

RULES:
1. Be imaginative and engaging
2. Use vivid descriptions
3. Create compelling narratives
4. Maintain consistency in style
5. Adapt tone to the request

Detect language (IT/EN), respond same."""

def get_system_prompt(complexity: Complexity) -> str:
    """Get system prompt for complexity level"""
    if complexity == Complexity.SIMPLE:
        return SIMPLE_SYSTEM
    elif complexity == Complexity.MEDIUM:
        return MEDIUM_SYSTEM
    elif complexity == Complexity.CODE:
        return CODE_SYSTEM
    elif complexity == Complexity.CREATIVE:
        return CREATIVE_SYSTEM
    return COMPLEX_SYSTEM
