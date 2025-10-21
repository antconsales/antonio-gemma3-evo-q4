"""
Example: Rule Evolution Demo

Demonstrates:
- Creating neurons with different patterns
- Triggering auto-evolution
- Inspecting generated rules
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.evomemory import EvoMemoryDB, Neuron, NeuronStore
from core.growth import RuleGenerator


def create_sample_neurons(store: NeuronStore):
    """Create sample neurons with patterns"""
    print("Creating sample neurons with patterns...\n")

    # Pattern 1: GPIO control (high confidence)
    gpio_data = [
        ("Accendi LED rosso", "GPIO 17 → HIGH", 0.92, 1),
        ("Spegni LED rosso", "GPIO 17 → LOW", 0.90, 1),
        ("LED verde on", "GPIO 18 → HIGH", 0.88, 1),
        ("LED verde off", "GPIO 18 → LOW", 0.91, 0),
        ("Blink LED", "GPIO 17: blink 3x", 0.85, 1),
    ]

    for inp, out, conf, feedback in gpio_data:
        n = Neuron(inp, out, confidence=conf, skill_id="gpio_control")
        n.user_feedback = feedback
        nid = store.save_neuron(n)
        print(f"  ✓ Neuron {nid}: {inp} (conf={conf}, feedback={feedback})")

    # Pattern 2: Sensor reading (medium confidence)
    sensor_data = [
        ("Temperatura?", "22.5°C", 0.75, 0),
        ("Umidità?", "65%", 0.70, 0),
        ("Pressione?", "1013 hPa", 0.68, 0),
    ]

    for inp, out, conf, feedback in sensor_data:
        n = Neuron(inp, out, confidence=conf, skill_id="sensors")
        n.user_feedback = feedback
        nid = store.save_neuron(n)
        print(f"  ✓ Neuron {nid}: {inp} (conf={conf})")

    # Pattern 3: Low confidence queries (need clarification)
    low_conf_data = [
        ("Sistema meteo?", "Non sono sicuro...", 0.30, -1),
        ("Previsioni domani?", "Forse controlla online?", 0.25, -1),
        ("Quanto pioverà?", "Non ho dati meteo", 0.20, -1),
    ]

    for inp, out, conf, feedback in low_conf_data:
        n = Neuron(inp, out, confidence=conf, skill_id="weather")
        n.user_feedback = feedback
        nid = store.save_neuron(n)
        print(f"  ✓ Neuron {nid}: {inp} (conf={conf}, feedback={feedback})")

    print(f"\n✓ Created {len(gpio_data) + len(sensor_data) + len(low_conf_data)} neurons")


def main():
    print("=" * 70)
    print("  Antonio Gemma3 Evo Q4 - Rule Evolution Demo")
    print("=" * 70)
    print()

    # Initialize
    db = EvoMemoryDB("data/evomemory/neurons.db")
    store = NeuronStore(db)
    generator = RuleGenerator(store, db)

    # Create neurons
    create_sample_neurons(store)

    # Trigger auto-evolution
    print("\n" + "=" * 70)
    print("  Triggering Auto-Evolution...")
    print("=" * 70)
    print()

    result = generator.auto_evolve(min_neurons=10)

    print(f"Neurons analyzed: {result['neurons_analyzed']}")
    print(f"Rules generated: {result['rules_generated']}")
    print(f"Rules saved to DB: {result['rules_saved']}")
    print(f"\n{result['message']}")

    # Inspect rules
    if result['rules_generated'] > 0:
        print("\n" + "=" * 70)
        print("  Generated Rules:")
        print("=" * 70)

        import json
        instinct_path = Path("data/evomemory/instinct.json")
        if instinct_path.exists():
            with open(instinct_path) as f:
                instinct = json.load(f)

            for i, rule in enumerate(instinct["rules"], 1):
                print(f"\nRule {i}:")
                print(f"  Text: {rule['rule_text']}")
                print(f"  Trigger: {rule['trigger_pattern']}")
                print(f"  Confidence threshold: {rule['confidence_threshold']:.2f}")
                print(f"  Priority: {rule['priority']}")

    # Database stats
    print("\n" + "=" * 70)
    print("  Final Database Stats:")
    print("=" * 70)
    stats = db.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    db.close()

    print("\n" + "=" * 70)
    print("  Evolution complete! Check:")
    print("    - data/evomemory/neurons.db (SQLite)")
    print("    - data/evomemory/instinct.json (Generated rules)")
    print("=" * 70)


if __name__ == "__main__":
    main()
