import sqlite3
import os
import json
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "sentra.db")

def initialize_database():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Agents Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                name TEXT,
                framework TEXT,
                node_count INTEGER,
                graph_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Execution Traces Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS execution_traces (
                id TEXT PRIMARY KEY,
                agent_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                node_name TEXT,
                event_type TEXT,
                prompt TEXT,
                response TEXT,
                tool_name TEXT,
                latency REAL,
                token_usage INTEGER,
                error TEXT,
                FOREIGN KEY(agent_id) REFERENCES agents(agent_id)
            )
        ''')

        # Vulnerabilities Table
        try:
            cursor.execute("SELECT trace_id FROM vulnerabilities LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("DROP TABLE IF EXISTS vulnerabilities")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id TEXT PRIMARY KEY,
                trace_id TEXT,
                vulnerability_type TEXT,
                severity TEXT,
                description TEXT,
                FOREIGN KEY(trace_id) REFERENCES execution_traces(id)
            )
        ''')

        # Prompt Tests Table (Redteaming)
        try:
            cursor.execute("SELECT attack_prompt FROM prompt_tests LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("DROP TABLE IF EXISTS prompt_tests")
            
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT,
                attack_prompt TEXT,
                response TEXT,
                success INTEGER,
                severity TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Ensure graph_data column exists
        try:
             cursor.execute("ALTER TABLE agents ADD COLUMN graph_data TEXT")
        except sqlite3.OperationalError:
            pass # column already exists
            
        conn.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized at {DB_PATH}")
