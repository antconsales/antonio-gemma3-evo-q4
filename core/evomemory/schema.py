"""
EvoMemory™ - SQLite Schema
Database schema per neuroni auto-evolutivi
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

class EvoMemoryDB:
    """Gestisce il database SQLite per EvoMemory™"""

    def __init__(self, db_path: str = "data/evomemory/neurons.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self.init_db()

    def init_db(self):
        """Inizializza il database con lo schema"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()

        # Tabella neuroni
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS neurons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_text TEXT NOT NULL,
                idea TEXT,
                output_text TEXT NOT NULL,
                mood TEXT DEFAULT 'neutral',  -- positive, neutral, negative
                confidence REAL DEFAULT 0.5,
                user_feedback INTEGER DEFAULT 0,  -- -1, 0, +1
                context_hash TEXT,  -- Per retrieval simile
                skill_id TEXT,  -- Quale skill ha generato questo
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0
            )
        """)

        # Tabella meta-neuroni (compressi)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meta_neurons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT NOT NULL,
                template TEXT NOT NULL,
                occurrences INTEGER DEFAULT 1,
                avg_confidence REAL DEFAULT 0.5,
                skill_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabella regole (instinct)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_text TEXT NOT NULL,
                trigger_pattern TEXT,
                confidence_threshold REAL DEFAULT 0.5,
                priority INTEGER DEFAULT 1,
                enabled INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                applied_count INTEGER DEFAULT 0
            )
        """)

        # Tabella skills
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                neuron_count INTEGER DEFAULT 0,
                avg_confidence REAL DEFAULT 0.5,
                enabled INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indici per performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_neurons_timestamp
            ON neurons(timestamp DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_neurons_confidence
            ON neurons(confidence DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_neurons_context
            ON neurons(context_hash)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_neurons_skill
            ON neurons(skill_id)
        """)

        self.conn.commit()
        print(f"✓ EvoMemory™ database initialized at {self.db_path}")

    def close(self):
        """Chiude la connessione"""
        if self.conn:
            self.conn.close()

    def get_stats(self) -> dict:
        """Statistiche del database"""
        cursor = self.conn.cursor()

        stats = {
            "neurons": cursor.execute("SELECT COUNT(*) FROM neurons").fetchone()[0],
            "meta_neurons": cursor.execute("SELECT COUNT(*) FROM meta_neurons").fetchone()[0],
            "rules": cursor.execute("SELECT COUNT(*) FROM rules WHERE enabled = 1").fetchone()[0],
            "skills": cursor.execute("SELECT COUNT(*) FROM skills WHERE enabled = 1").fetchone()[0],
            "avg_confidence": cursor.execute(
                "SELECT AVG(confidence) FROM neurons WHERE timestamp > datetime('now', '-7 days')"
            ).fetchone()[0] or 0.0,
        }

        return stats


if __name__ == "__main__":
    # Test
    db = EvoMemoryDB("../../data/evomemory/neurons.db")
    print("Stats:", db.get_stats())
    db.close()
