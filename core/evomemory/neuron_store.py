"""
Neuron Store - CRUD operations per neuroni
Gestisce creazione, lettura, aggiornamento e cancellazione neuroni
"""

import hashlib
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from .schema import EvoMemoryDB


class Neuron:
    """Rappresenta un singolo neurone"""

    def __init__(
        self,
        input_text: str,
        output_text: str,
        idea: Optional[str] = None,
        mood: str = "neutral",
        confidence: float = 0.5,
        skill_id: Optional[str] = None,
        neuron_id: Optional[int] = None,
    ):
        self.id = neuron_id
        self.input_text = input_text
        self.idea = idea
        self.output_text = output_text
        self.mood = mood
        self.confidence = confidence
        self.skill_id = skill_id
        self.context_hash = self._compute_hash(input_text)
        self.timestamp = datetime.now()
        self.user_feedback = 0

    def _compute_hash(self, text: str) -> str:
        """Hash per retrieval simile"""
        # Normalizza e hash
        normalized = text.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:8]

    def to_dict(self) -> dict:
        """Serializza a dict"""
        return {
            "id": self.id,
            "input_text": self.input_text,
            "idea": self.idea,
            "output_text": self.output_text,
            "mood": self.mood,
            "confidence": self.confidence,
            "skill_id": self.skill_id,
            "context_hash": self.context_hash,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            "user_feedback": self.user_feedback,
        }


class NeuronStore:
    """Gestisce lo storage dei neuroni"""

    def __init__(self, db: EvoMemoryDB):
        self.db = db

    def save_neuron(self, neuron: Neuron) -> int:
        """Salva un neurone e ritorna l'ID"""
        cursor = self.db.conn.cursor()

        cursor.execute("""
            INSERT INTO neurons (
                input_text, idea, output_text, mood, confidence,
                context_hash, skill_id, user_feedback
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            neuron.input_text,
            neuron.idea,
            neuron.output_text,
            neuron.mood,
            neuron.confidence,
            neuron.context_hash,
            neuron.skill_id,
            neuron.user_feedback,
        ))

        self.db.conn.commit()
        return cursor.lastrowid

    def get_neuron(self, neuron_id: int) -> Optional[Neuron]:
        """Recupera un neurone per ID"""
        cursor = self.db.conn.cursor()
        row = cursor.execute("SELECT * FROM neurons WHERE id = ?", (neuron_id,)).fetchone()

        if not row:
            return None

        return self._row_to_neuron(row)

    def get_recent_neurons(self, limit: int = 10, skill_id: Optional[str] = None) -> List[Neuron]:
        """Recupera gli ultimi N neuroni"""
        cursor = self.db.conn.cursor()

        if skill_id:
            rows = cursor.execute(
                "SELECT * FROM neurons WHERE skill_id = ? ORDER BY timestamp DESC LIMIT ?",
                (skill_id, limit)
            ).fetchall()
        else:
            rows = cursor.execute(
                "SELECT * FROM neurons ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()

        return [self._row_to_neuron(row) for row in rows]

    def get_similar_neurons(self, context_hash: str, limit: int = 5) -> List[Neuron]:
        """Trova neuroni con contesto simile"""
        cursor = self.db.conn.cursor()

        rows = cursor.execute("""
            SELECT * FROM neurons
            WHERE context_hash = ?
            ORDER BY confidence DESC, timestamp DESC
            LIMIT ?
        """, (context_hash, limit)).fetchall()

        return [self._row_to_neuron(row) for row in rows]

    def search_neurons(self, query: str, limit: int = 10) -> List[Neuron]:
        """Ricerca full-text nei neuroni"""
        cursor = self.db.conn.cursor()

        search_pattern = f"%{query}%"
        rows = cursor.execute("""
            SELECT * FROM neurons
            WHERE input_text LIKE ? OR output_text LIKE ?
            ORDER BY confidence DESC, timestamp DESC
            LIMIT ?
        """, (search_pattern, search_pattern, limit)).fetchall()

        return [self._row_to_neuron(row) for row in rows]

    def update_feedback(self, neuron_id: int, feedback: int):
        """Aggiorna il feedback dell'utente (-1, 0, +1)"""
        cursor = self.db.conn.cursor()

        # Aggiorna feedback e mood
        mood = "positive" if feedback > 0 else ("negative" if feedback < 0 else "neutral")

        cursor.execute("""
            UPDATE neurons
            SET user_feedback = ?, mood = ?, last_accessed = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (feedback, mood, neuron_id))

        self.db.conn.commit()

    def prune_old_neurons(self, keep_days: int = 30, min_confidence: float = 0.3):
        """Elimina neuroni vecchi con bassa confidenza"""
        cursor = self.db.conn.cursor()

        cursor.execute("""
            DELETE FROM neurons
            WHERE timestamp < datetime('now', ? || ' days')
            AND confidence < ?
            AND user_feedback <= 0
        """, (f"-{keep_days}", min_confidence))

        deleted = cursor.rowcount
        self.db.conn.commit()

        return deleted

    def _row_to_neuron(self, row) -> Neuron:
        """Converte una row SQL in Neuron object"""
        neuron = Neuron(
            input_text=row["input_text"],
            output_text=row["output_text"],
            idea=row["idea"],
            mood=row["mood"],
            confidence=row["confidence"],
            skill_id=row["skill_id"],
            neuron_id=row["id"],
        )
        neuron.user_feedback = row["user_feedback"]
        neuron.timestamp = row["timestamp"]
        neuron.context_hash = row["context_hash"]

        return neuron


if __name__ == "__main__":
    # Test
    db = EvoMemoryDB("../../data/evomemory/neurons.db")
    store = NeuronStore(db)

    # Crea neurone di test
    test_neuron = Neuron(
        input_text="Accendi il LED sul pin 17",
        output_text="OK, attivo GPIO 17 su HIGH",
        idea="L'utente vuole controllare un LED via GPIO",
        mood="positive",
        confidence=0.85,
        skill_id="gpio_control"
    )

    neuron_id = store.save_neuron(test_neuron)
    print(f"✓ Neuron saved with ID: {neuron_id}")

    # Recupera
    retrieved = store.get_neuron(neuron_id)
    print(f"✓ Retrieved: {retrieved.to_dict()}")

    db.close()
