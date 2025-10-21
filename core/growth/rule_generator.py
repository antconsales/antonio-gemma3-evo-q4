"""
Rule Regeneration System - Auto-evoluzione
Analizza i neuroni e genera nuove regole di ragionamento
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.evomemory import EvoMemoryDB, NeuronStore, Neuron


class Rule:
    """Rappresenta una regola di ragionamento"""

    def __init__(
        self,
        rule_text: str,
        trigger_pattern: str,
        confidence_threshold: float = 0.5,
        priority: int = 1,
        enabled: bool = True,
    ):
        self.rule_text = rule_text
        self.trigger_pattern = trigger_pattern
        self.confidence_threshold = confidence_threshold
        self.priority = priority
        self.enabled = enabled

    def to_dict(self) -> dict:
        return {
            "rule_text": self.rule_text,
            "trigger_pattern": self.trigger_pattern,
            "confidence_threshold": self.confidence_threshold,
            "priority": self.priority,
            "enabled": self.enabled,
        }


class RuleGenerator:
    """Genera nuove regole analizzando i neuroni"""

    def __init__(self, neuron_store: NeuronStore, db: EvoMemoryDB):
        self.store = neuron_store
        self.db = db

    def analyze_patterns(self, limit: int = 100) -> Dict[str, List[Neuron]]:
        """Raggruppa neuroni per pattern simili"""
        neurons = self.store.get_recent_neurons(limit=limit)

        # Raggruppa per skill_id
        by_skill = defaultdict(list)
        for n in neurons:
            if n.skill_id:
                by_skill[n.skill_id].append(n)

        # Raggruppa per mood
        by_mood = defaultdict(list)
        for n in neurons:
            by_mood[n.mood].append(n)

        # Raggruppa per parole chiave comuni
        by_keywords = defaultdict(list)
        for n in neurons:
            words = n.input_text.lower().split()
            # Estrai parole significative (>3 caratteri)
            keywords = [w for w in words if len(w) > 3]
            for kw in keywords[:3]:  # Prime 3 parole significative
                by_keywords[kw].append(n)

        return {
            "by_skill": dict(by_skill),
            "by_mood": dict(by_mood),
            "by_keywords": dict(by_keywords),
        }

    def generate_rules(self, min_occurrences: int = 3) -> List[Rule]:
        """
        Genera regole basate sui pattern identificati

        Args:
            min_occurrences: Numero minimo di neuroni per generare una regola

        Returns:
            Lista di nuove regole
        """
        patterns = self.analyze_patterns(limit=200)
        rules = []

        # 1. Regole da skill patterns
        for skill_id, neurons in patterns["by_skill"].items():
            if len(neurons) >= min_occurrences:
                avg_confidence = sum(n.confidence for n in neurons) / len(neurons)

                if avg_confidence > 0.7:
                    rule = Rule(
                        rule_text=f"Use high confidence for {skill_id} tasks",
                        trigger_pattern=f"skill_id:{skill_id}",
                        confidence_threshold=avg_confidence,
                        priority=2,
                    )
                    rules.append(rule)

        # 2. Regole da feedback negativo
        negative_neurons = [
            n for n in self.store.get_recent_neurons(limit=100)
            if n.user_feedback < 0
        ]

        if len(negative_neurons) >= 3:
            # Trova pattern comuni in risposte negative
            common_words = Counter()
            for n in negative_neurons:
                words = n.output_text.lower().split()
                common_words.update(words)

            # Se una parola appare spesso in risposte negative → evitala
            for word, count in common_words.most_common(5):
                if count >= 3 and len(word) > 3:
                    rule = Rule(
                        rule_text=f"Avoid using '{word}' in responses (negative feedback pattern)",
                        trigger_pattern=f"avoid_word:{word}",
                        confidence_threshold=0.3,
                        priority=3,
                    )
                    rules.append(rule)

        # 3. Regole da alta confidenza
        high_conf_neurons = [
            n for n in self.store.get_recent_neurons(limit=100)
            if n.confidence > 0.8
        ]

        if len(high_conf_neurons) >= 5:
            # Trova pattern comuni in risposte ad alta confidenza
            keywords = Counter()
            for n in high_conf_neurons:
                words = n.input_text.lower().split()
                keywords.update(w for w in words if len(w) > 3)

            # Pattern che portano ad alta confidenza
            for keyword, count in keywords.most_common(3):
                if count >= 3:
                    rule = Rule(
                        rule_text=f"High confidence pattern detected for '{keyword}' queries",
                        trigger_pattern=f"keyword:{keyword}",
                        confidence_threshold=0.8,
                        priority=1,
                    )
                    rules.append(rule)

        # 4. Regole da bassa confidenza ripetuta
        low_conf_neurons = [
            n for n in self.store.get_recent_neurons(limit=50)
            if n.confidence < 0.4
        ]

        if len(low_conf_neurons) >= 5:
            # Pattern che causano bassa confidenza
            topics = Counter()
            for n in low_conf_neurons:
                words = n.input_text.lower().split()[:5]  # Prime 5 parole
                topics.update(w for w in words if len(w) > 3)

            for topic, count in topics.most_common(2):
                if count >= 3:
                    rule = Rule(
                        rule_text=f"Ask clarification for '{topic}' topics (low confidence pattern)",
                        trigger_pattern=f"clarify:{topic}",
                        confidence_threshold=0.4,
                        priority=2,
                    )
                    rules.append(rule)

        return rules

    def save_rules_to_db(self, rules: List[Rule]) -> int:
        """Salva le regole nel database"""
        cursor = self.db.conn.cursor()
        saved = 0

        for rule in rules:
            # Evita duplicati
            existing = cursor.execute(
                "SELECT id FROM rules WHERE rule_text = ?",
                (rule.rule_text,)
            ).fetchone()

            if not existing:
                cursor.execute("""
                    INSERT INTO rules (
                        rule_text, trigger_pattern, confidence_threshold,
                        priority, enabled
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    rule.rule_text,
                    rule.trigger_pattern,
                    rule.confidence_threshold,
                    rule.priority,
                    1 if rule.enabled else 0,
                ))
                saved += 1

        self.db.conn.commit()
        return saved

    def save_rules_to_json(self, rules: List[Rule], path: str = "data/evomemory/instinct.json"):
        """Esporta regole in JSON per ispezione umana"""
        rules_data = {
            "generated_at": datetime.now().isoformat(),
            "rules_count": len(rules),
            "rules": [r.to_dict() for r in rules],
        }

        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(path_obj, "w") as f:
            json.dump(rules_data, f, indent=2)

        print(f"✓ Rules exported to {path}")

    def auto_evolve(self, min_neurons: int = 50) -> Dict:
        """
        Ciclo di auto-evoluzione completo

        Returns:
            {
                "neurons_analyzed": int,
                "rules_generated": int,
                "rules_saved": int,
            }
        """
        stats = self.db.get_stats()

        if stats["neurons"] < min_neurons:
            return {
                "neurons_analyzed": stats["neurons"],
                "rules_generated": 0,
                "rules_saved": 0,
                "message": f"Not enough neurons ({stats['neurons']} < {min_neurons})",
            }

        # Genera regole
        new_rules = self.generate_rules(min_occurrences=3)

        # Salva in DB
        saved = self.save_rules_to_db(new_rules)

        # Salva in JSON
        self.save_rules_to_json(new_rules)

        return {
            "neurons_analyzed": stats["neurons"],
            "rules_generated": len(new_rules),
            "rules_saved": saved,
            "message": f"✓ Generated {len(new_rules)} rules, saved {saved} new ones",
        }


if __name__ == "__main__":
    # Test
    db = EvoMemoryDB("../../data/evomemory/neurons.db")
    store = NeuronStore(db)

    # Crea neuroni di test
    test_data = [
        ("Accendi LED rosso", "GPIO 17 attivato", "gpio_control", 0.9, 1),
        ("Spegni LED", "GPIO 17 disattivato", "gpio_control", 0.85, 1),
        ("LED verde on", "GPIO 18 attivato", "gpio_control", 0.88, 0),
        ("Temperatura?", "22.5°C", "sensors", 0.7, 0),
        ("Umidità?", "Non sono sicuro", "sensors", 0.3, -1),
        ("Pressione?", "Forse 1013 hPa", "sensors", 0.4, -1),
    ]

    for inp, out, skill, conf, feedback in test_data:
        n = Neuron(inp, out, skill_id=skill, confidence=conf)
        n.user_feedback = feedback
        store.save_neuron(n)

    # Generate rules
    generator = RuleGenerator(store, db)
    result = generator.auto_evolve(min_neurons=3)

    print("\n" + "="*50)
    print("Auto-Evolution Results:")
    print("="*50)
    print(f"Neurons analyzed: {result['neurons_analyzed']}")
    print(f"Rules generated: {result['rules_generated']}")
    print(f"Rules saved: {result['rules_saved']}")
    print(f"Message: {result['message']}")

    db.close()
