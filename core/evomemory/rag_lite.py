"""
RAG-Lite - Retrieval Augmented Generation semplificato
Usa BM25 puro Python senza dipendenze pesanti
"""

import math
from collections import Counter
from typing import List, Tuple, Dict
from .neuron_store import Neuron, NeuronStore


class BM25:
    """BM25 algorithm per ranking documenti"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_count = 0
        self.avg_doc_len = 0
        self.doc_freqs = {}
        self.idf_cache = {}

    def fit(self, documents: List[str]):
        """Calcola IDF per il corpus"""
        self.doc_count = len(documents)

        # Calcola lunghezza media
        total_len = sum(len(doc.split()) for doc in documents)
        self.avg_doc_len = total_len / self.doc_count if self.doc_count > 0 else 0

        # Calcola document frequency per ogni term
        for doc in documents:
            terms = set(doc.lower().split())
            for term in terms:
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        # Pre-calcola IDF
        for term, freq in self.doc_freqs.items():
            idf = math.log((self.doc_count - freq + 0.5) / (freq + 0.5) + 1)
            self.idf_cache[term] = idf

    def score(self, query: str, document: str) -> float:
        """Calcola BM25 score per un documento"""
        query_terms = query.lower().split()
        doc_terms = document.lower().split()
        doc_len = len(doc_terms)

        doc_term_counts = Counter(doc_terms)
        score = 0.0

        for term in query_terms:
            if term not in self.idf_cache:
                continue

            idf = self.idf_cache[term]
            tf = doc_term_counts.get(term, 0)

            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_len))

            score += idf * (numerator / denominator)

        return score


class RAGLite:
    """Retrieval system leggero per neuroni"""

    def __init__(self, neuron_store: NeuronStore):
        self.store = neuron_store
        self.bm25 = BM25()
        self.indexed_neurons: List[Neuron] = []

    def index_neurons(self, max_neurons: int = 1000):
        """Indicizza gli ultimi N neuroni per retrieval veloce"""
        # Recupera neuroni recenti con alta confidenza
        self.indexed_neurons = self.store.get_recent_neurons(limit=max_neurons)

        # Crea corpus per BM25
        documents = [
            f"{n.input_text} {n.output_text}" for n in self.indexed_neurons
        ]

        self.bm25.fit(documents)
        print(f"✓ RAG-Lite indexed {len(self.indexed_neurons)} neurons")

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[Neuron, float]]:
        """
        Retrieval dei neuroni più rilevanti

        Returns:
            Lista di (neuron, score) ordinata per score
        """
        if not self.indexed_neurons:
            self.index_neurons()

        results = []

        for neuron in self.indexed_neurons:
            doc_text = f"{neuron.input_text} {neuron.output_text}"
            score = self.bm25.score(query, doc_text)

            # Boost per alta confidenza e feedback positivo
            if neuron.confidence > 0.7:
                score *= 1.2
            if neuron.user_feedback > 0:
                score *= 1.3

            results.append((neuron, score))

        # Ordina per score
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def get_context_for_prompt(self, query: str, max_context_tokens: int = 300) -> str:
        """
        Genera contesto RAG da aggiungere al prompt

        Returns:
            Stringa di contesto formattata
        """
        relevant = self.retrieve(query, top_k=3)

        if not relevant or relevant[0][1] < 0.5:
            return ""  # Nessun match rilevante

        context_parts = ["### Esperienze passate rilevanti:"]

        current_tokens = 0

        for neuron, score in relevant:
            # Stima token (~4 chars = 1 token)
            estimated_tokens = len(neuron.output_text) / 4

            if current_tokens + estimated_tokens > max_context_tokens:
                break

            context_parts.append(
                f"- Input: {neuron.input_text[:100]}\n"
                f"  Output: {neuron.output_text[:150]}\n"
                f"  (confidenza: {neuron.confidence:.2f})"
            )

            current_tokens += estimated_tokens

        if len(context_parts) == 1:
            return ""  # Solo header, niente context

        return "\n".join(context_parts) + "\n\n"

    def hybrid_search(self, query: str) -> Dict:
        """
        Combina BM25 con context hash matching

        Returns:
            {
                "bm25_results": [...],
                "context_matches": [...],
                "combined": [...]
            }
        """
        from .neuron_store import Neuron as NeuronClass

        # 1. BM25 search
        bm25_results = self.retrieve(query, top_k=5)

        # 2. Context hash matching
        temp_neuron = NeuronClass(input_text=query, output_text="")
        context_matches = self.store.get_similar_neurons(
            temp_neuron.context_hash,
            limit=5
        )

        # 3. Combina e de-duplica
        seen_ids = set()
        combined = []

        # Priorità a BM25
        for neuron, score in bm25_results:
            if neuron.id not in seen_ids:
                combined.append((neuron, score, "bm25"))
                seen_ids.add(neuron.id)

        # Aggiungi context matches
        for neuron in context_matches:
            if neuron.id not in seen_ids:
                combined.append((neuron, 0.5, "context_hash"))
                seen_ids.add(neuron.id)

        return {
            "bm25_results": bm25_results,
            "context_matches": context_matches,
            "combined": combined[:5]
        }


if __name__ == "__main__":
    # Test
    from .schema import EvoMemoryDB
    from .neuron_store import NeuronStore, Neuron

    db = EvoMemoryDB("../../data/evomemory/neurons.db")
    store = NeuronStore(db)

    # Crea alcuni neuroni di test
    test_data = [
        ("Accendi il LED rosso", "OK, attivo GPIO 17", "gpio_control", 0.9),
        ("Spegni il LED", "OK, GPIO 17 su LOW", "gpio_control", 0.85),
        ("Che temperatura fa?", "Leggo il sensore... 22.5°C", "sensors", 0.7),
        ("Registra un video", "Avvio registrazione video dalla camera", "media", 0.6),
    ]

    for inp, out, skill, conf in test_data:
        n = Neuron(inp, out, skill_id=skill, confidence=conf)
        store.save_neuron(n)

    # Test RAG
    rag = RAGLite(store)
    rag.index_neurons()

    query = "Come controllo un LED?"
    results = rag.retrieve(query, top_k=3)

    print(f"\nQuery: {query}\n")
    for neuron, score in results:
        print(f"Score: {score:.3f}")
        print(f"  Input: {neuron.input_text}")
        print(f"  Output: {neuron.output_text}")
        print()

    # Test context generation
    context = rag.get_context_for_prompt(query)
    print("Context generato:")
    print(context)

    db.close()
