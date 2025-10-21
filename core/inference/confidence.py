"""
Confidence Scorer - Auto-valutazione delle risposte
Calcola un punteggio di confidenza (0-1) per ogni output
"""

import re
from typing import Tuple


class ConfidenceScorer:
    """Valuta la confidenza di una risposta"""

    # Patterns che indicano bassa confidenza
    UNCERTAINTY_PATTERNS = [
        r"\bnon sono sicuro\b",
        r"\bnon so\b",
        r"\bforse\b",
        r"\bprobabilmente\b",
        r"\bpotrebbe essere\b",
        r"\bpossibilmente\b",
        r"\bI'm not sure\b",
        r"\bI don't know\b",
        r"\bmaybe\b",
        r"\bprobably\b",
        r"\bmight be\b",
        r"\bcould be\b",
    ]

    # Patterns che indicano alta confidenza
    CERTAINTY_PATTERNS = [
        r"\bsicuramente\b",
        r"\bconferma\b",
        r"\bessenzialmente\b",
        r"\bdefinitivamente\b",
        r"\bcertainly\b",
        r"\bdefinitely\b",
        r"\bclearly\b",
        r"\bobviously\b",
    ]

    def __init__(self):
        self.uncertainty_regex = re.compile(
            "|".join(self.UNCERTAINTY_PATTERNS),
            re.IGNORECASE
        )
        self.certainty_regex = re.compile(
            "|".join(self.CERTAINTY_PATTERNS),
            re.IGNORECASE
        )

    def score(self, output_text: str, context: dict = None) -> Tuple[float, str]:
        """
        Calcola confidenza (0-1) e reasoning

        Args:
            output_text: Il testo generato dal modello
            context: Contesto opzionale (es. prompt length, tokens generati)

        Returns:
            (confidence_score, reasoning)
        """
        confidence = 0.5  # Baseline
        reasons = []

        # 1. Analisi lunghezza
        output_len = len(output_text.strip())
        if output_len < 10:
            confidence -= 0.2
            reasons.append("output troppo breve")
        elif output_len > 50:
            confidence += 0.1
            reasons.append("risposta dettagliata")

        # 2. Patterns di incertezza
        uncertainty_matches = len(self.uncertainty_regex.findall(output_text))
        if uncertainty_matches > 0:
            confidence -= 0.15 * uncertainty_matches
            reasons.append(f"trovate {uncertainty_matches} espressioni di dubbio")

        # 3. Patterns di certezza
        certainty_matches = len(self.certainty_regex.findall(output_text))
        if certainty_matches > 0:
            confidence += 0.1 * certainty_matches
            reasons.append(f"trovate {certainty_matches} espressioni di certezza")

        # 4. Domande nella risposta (sintomo di confusione)
        question_marks = output_text.count("?")
        if question_marks > 1:
            confidence -= 0.1
            reasons.append("risposta contiene domande")

        # 5. Ripetizioni (sintomo di allucinazione)
        words = output_text.lower().split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.6:
                confidence -= 0.15
                reasons.append("troppe ripetizioni")

        # 6. Context-based adjustments
        if context:
            # Se il prompt era molto lungo ma l'output corto → bassa confidenza
            if context.get("prompt_tokens", 0) > 500 and output_len < 50:
                confidence -= 0.1
                reasons.append("risposta troppo breve rispetto al prompt")

            # Se generazione veloce → alta confidenza
            if context.get("tokens_per_second", 0) > 5:
                confidence += 0.05
                reasons.append("generazione fluida")

        # Clamp tra 0 e 1
        confidence = max(0.0, min(1.0, confidence))

        reasoning = "; ".join(reasons) if reasons else "valutazione standard"

        return confidence, reasoning

    def should_ask_clarification(self, confidence: float, threshold: float = 0.4) -> bool:
        """Determina se chiedere chiarimenti all'utente"""
        return confidence < threshold

    def get_confidence_label(self, confidence: float) -> str:
        """Etichetta human-readable"""
        if confidence >= 0.8:
            return "molto alta"
        elif confidence >= 0.6:
            return "alta"
        elif confidence >= 0.4:
            return "media"
        elif confidence >= 0.2:
            return "bassa"
        else:
            return "molto bassa"


if __name__ == "__main__":
    # Test
    scorer = ConfidenceScorer()

    test_cases = [
        "Accendo il pin GPIO 17 su HIGH. Fatto!",
        "Non sono sicuro, forse dovresti controllare la documentazione?",
        "Probabilmente il LED è sul pin 17, ma potrebbe essere anche il 18...",
        "Certamente! Il comando corretto è gpio.write(17, HIGH).",
    ]

    for text in test_cases:
        conf, reason = scorer.score(text)
        label = scorer.get_confidence_label(conf)
        print(f"\nText: {text[:50]}...")
        print(f"Confidence: {conf:.2f} ({label})")
        print(f"Reasoning: {reason}")
        print(f"Ask clarification: {scorer.should_ask_clarification(conf)}")
