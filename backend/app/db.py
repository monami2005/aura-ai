import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).parent / 'aura_history.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS action_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            original_command TEXT NOT NULL,
            action TEXT NOT NULL,
            result TEXT NOT NULL,
            success INTEGER NOT NULL,
            detected_intent TEXT,
            planned_action TEXT,
            confirmation_status TEXT,
            execution_status TEXT,
            error TEXT,
            language TEXT DEFAULT 'en'
        )
    ''')
    conn.commit()

    # Migration for existing databases
    existing_cols = [row[1] for row in c.execute("PRAGMA table_info(action_history)").fetchall()]
    new_cols = [
        ("detected_intent", "TEXT"),
        ("planned_action", "TEXT"),
        ("confirmation_status", "TEXT"),
        ("execution_status", "TEXT"),
        ("error", "TEXT"),
        ("language", "TEXT DEFAULT 'en'")
    ]
    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            try:
                c.execute(f"ALTER TABLE action_history ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                pass
    conn.commit()
    conn.close()

def add_action_history(
    original_command: str,
    action: str,
    result: str,
    success: bool,
    detected_intent: Optional[str] = None,
    planned_action: Optional[str] = None,
    confirmation_status: Optional[str] = None,
    execution_status: Optional[str] = None,
    error: Optional[str] = None,
    language: Optional[str] = "en"
):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    ts = datetime.utcnow().isoformat() + "Z"
    c.execute(
        '''
        INSERT INTO action_history (
            timestamp, original_command, action, result, success,
            detected_intent, planned_action, confirmation_status, execution_status, error, language
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            ts, original_command, action, result, 1 if success else 0,
            detected_intent or action,
            planned_action or action,
            confirmation_status or ("allowed" if success else "failed"),
            execution_status or ("completed" if success else "failed"),
            error,
            language or "en"
        )
    )
    conn.commit()
    conn.close()

def get_action_history(limit: int = 50) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        '''
        SELECT id, timestamp, original_command, action, result, success,
               detected_intent, planned_action, confirmation_status, execution_status, error, language
        FROM action_history
        ORDER BY id DESC
        LIMIT ?
        ''',
        (limit,)
    )
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "timestamp": row["timestamp"],
            "original_command": row["original_command"],
            "action": row["action"],
            "result": row["result"],
            "success": bool(row["success"]),
            "detected_intent": row["detected_intent"] if "detected_intent" in row.keys() else row["action"],
            "planned_action": row["planned_action"] if "planned_action" in row.keys() else row["action"],
            "confirmation_status": row["confirmation_status"] if "confirmation_status" in row.keys() else None,
            "execution_status": row["execution_status"] if "execution_status" in row.keys() else None,
            "error": row["error"] if "error" in row.keys() else None,
            "language": row["language"] if "language" in row.keys() else "en",
        }
        for row in rows
    ]

# Initialize on module import
init_db()
