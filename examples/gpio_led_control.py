"""
Example: LED Control via Antonio Gemma3 Evo Q4

Demonstrates:
- Connecting to the API
- Sending GPIO commands
- Receiving neuron feedback
"""

import requests
import json

# API endpoint
API_URL = "http://localhost:8000"


def chat(message: str, use_rag: bool = True):
    """Send message to Antonio API"""
    response = requests.post(
        f"{API_URL}/chat",
        json={"message": message, "use_rag": use_rag},
    )
    return response.json()


def give_feedback(neuron_id: int, feedback: int):
    """Give feedback on a response (1=good, -1=bad, 0=neutral)"""
    response = requests.post(
        f"{API_URL}/feedback",
        json={"neuron_id": neuron_id, "feedback": feedback},
    )
    return response.json()


def main():
    print("=" * 60)
    print("  Antonio Gemma3 Evo Q4 - GPIO LED Control Example")
    print("=" * 60)

    # Example 1: Chiedi informazioni su GPIO
    print("\n1. Asking about GPIO...")
    result = chat("Come posso accendere un LED sul pin 17?")
    print(f"Response: {result['response']}")
    print(f"Confidence: {result['confidence']:.2f} ({result['confidence_label']})")
    print(f"Neuron ID: {result['neuron_id']}")

    # Give positive feedback
    print("\n2. Giving positive feedback...")
    feedback_result = give_feedback(result["neuron_id"], feedback=1)
    print(f"Feedback submitted: {feedback_result}")

    # Example 2: Actual GPIO command (if using Action Broker)
    print("\n3. Requesting GPIO action...")
    result = chat("Accendi il LED sul pin 17")
    print(f"Response: {result['response']}")

    # Example 3: Complex query
    print("\n4. Complex GPIO query...")
    result = chat(
        "Voglio far lampeggiare il LED rosso 5 volte, come faccio?"
    )
    print(f"Response: {result['response']}")

    # Example 4: With RAG (should retrieve past GPIO conversations)
    print("\n5. Query with RAG memory...")
    result = chat("Ricordi come si accende un LED?", use_rag=True)
    print(f"Response: {result['response']}")
    print(f"RAG used: {result['rag_used']}")

    # Check stats
    print("\n6. System stats...")
    stats = requests.get(f"{API_URL}/stats").json()
    print(f"Total neurons: {stats['neurons_total']}")
    print(f"Avg confidence: {stats['avg_confidence']:.2f}")
    print(f"Uptime: {stats['uptime']}")


if __name__ == "__main__":
    # Verify API is running
    try:
        requests.get(API_URL, timeout=2)
    except requests.exceptions.ConnectionError:
        print("❌ Error: API server not running!")
        print("Start it with: python3 api/server.py")
        exit(1)

    main()

    print("\n" + "=" * 60)
    print("  Example completed! Check data/evomemory/neurons.db")
    print("  to see saved neurons.")
    print("=" * 60)
