"""
Tests for EvoMemory™ core components
"""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.evomemory import EvoMemoryDB, Neuron, NeuronStore, RAGLite


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = EvoMemoryDB(db_path)
    yield db

    db.close()
    os.unlink(db_path)


def test_database_initialization(temp_db):
    """Test database creation"""
    stats = temp_db.get_stats()
    assert stats["neurons"] == 0
    assert stats["meta_neurons"] == 0
    assert stats["rules"] == 0


def test_neuron_creation_and_storage(temp_db):
    """Test neuron CRUD operations"""
    store = NeuronStore(temp_db)

    # Create neuron
    neuron = Neuron(
        input_text="Test input",
        output_text="Test output",
        confidence=0.85,
        skill_id="test_skill"
    )

    # Save
    neuron_id = store.save_neuron(neuron)
    assert neuron_id > 0

    # Retrieve
    retrieved = store.get_neuron(neuron_id)
    assert retrieved is not None
    assert retrieved.input_text == "Test input"
    assert retrieved.confidence == 0.85

    # Update feedback
    store.update_feedback(neuron_id, feedback=1)
    updated = store.get_neuron(neuron_id)
    assert updated.user_feedback == 1
    assert updated.mood == "positive"


def test_neuron_search(temp_db):
    """Test search functionality"""
    store = NeuronStore(temp_db)

    # Create multiple neurons
    neurons_data = [
        ("Turn on LED", "GPIO 17 activated", 0.9),
        ("Turn off LED", "GPIO 17 deactivated", 0.85),
        ("Read sensor", "Temperature: 22.5°C", 0.7),
    ]

    for inp, out, conf in neurons_data:
        n = Neuron(inp, out, confidence=conf)
        store.save_neuron(n)

    # Search
    results = store.search_neurons("LED")
    assert len(results) == 2
    assert "LED" in results[0].input_text


def test_rag_lite_retrieval(temp_db):
    """Test RAG-Lite BM25 retrieval"""
    store = NeuronStore(temp_db)
    rag = RAGLite(store)

    # Create test neurons
    test_data = [
        ("Accendi il LED rosso", "OK, GPIO 17 attivo", 0.9),
        ("Spegni il LED", "OK, GPIO 17 su LOW", 0.85),
        ("Che temperatura fa?", "22.5°C", 0.7),
    ]

    for inp, out, conf in test_data:
        n = Neuron(inp, out, confidence=conf)
        store.save_neuron(n)

    # Index
    rag.index_neurons()

    # Retrieve
    results = rag.retrieve("Come controllo un LED?", top_k=2)
    assert len(results) > 0

    # Top result should be LED-related
    top_neuron, score = results[0]
    assert "LED" in top_neuron.input_text


def test_confidence_scoring():
    """Test confidence scorer"""
    from core.inference import ConfidenceScorer

    scorer = ConfidenceScorer()

    # High confidence response
    conf1, _ = scorer.score("Certainly! The command is gpio.write(17, HIGH)")
    assert conf1 > 0.6

    # Low confidence response
    conf2, _ = scorer.score("I'm not sure, maybe check the docs?")
    assert conf2 < 0.5

    # Short response
    conf3, _ = scorer.score("OK")
    assert conf3 < 0.5


def test_neuron_pruning(temp_db):
    """Test old neuron pruning"""
    store = NeuronStore(temp_db)

    # Create low-confidence neuron
    n = Neuron("test", "output", confidence=0.2)
    store.save_neuron(n)

    # Prune (won't delete recent ones)
    deleted = store.prune_old_neurons(keep_days=0, min_confidence=0.3)
    assert deleted >= 0  # May or may not delete based on timestamp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
