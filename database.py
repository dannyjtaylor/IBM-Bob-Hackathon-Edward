"""
Edward Database Module
Manages session history and conversation logs
"""

import logging
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from config import DB_PATH

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EdwardDatabase:
    """
    Database manager for Edward's session history and conversation logs.
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database.
        
        Args:
            db_path: Path to database file (defaults to config)
        """
        self.db_path = db_path or DB_PATH
        self._init_database()
        
        logger.info(f"Edward database initialized: {self.db_path}")
    
    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    total_interactions INTEGER DEFAULT 0
                )
            """)
            
            # Create interactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    question TEXT NOT NULL,
                    response TEXT NOT NULL,
                    screenshot_path TEXT,
                    duration_ms INTEGER,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                )
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_session 
                ON interactions(session_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_timestamp 
                ON interactions(timestamp)
            """)
            
            conn.commit()
            logger.info("Database schema initialized")
    
    def create_session(self) -> int:
        """
        Create a new session.
        
        Returns:
            Session ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO sessions DEFAULT VALUES")
                session_id = cursor.lastrowid
                conn.commit()
            
            logger.info(f"New session created: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return -1
    
    def end_session(self, session_id: int):
        """
        Mark a session as ended.
        
        Args:
            session_id: Session ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update session end time
                cursor.execute("""
                    UPDATE sessions 
                    SET ended_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (session_id,))
                
                # Update total interactions count
                cursor.execute("""
                    UPDATE sessions 
                    SET total_interactions = (
                        SELECT COUNT(*) FROM interactions WHERE session_id = ?
                    )
                    WHERE id = ?
                """, (session_id, session_id))
                
                conn.commit()
            
            logger.info(f"Session ended: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
    
    def add_interaction(
        self,
        session_id: int,
        question: str,
        response: str,
        screenshot_path: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> int:
        """
        Add an interaction to the database.
        
        Args:
            session_id: Session ID
            question: User's question
            response: Edward's response
            screenshot_path: Path to screenshot (optional)
            duration_ms: Response duration in milliseconds (optional)
            
        Returns:
            Interaction ID
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO interactions 
                    (session_id, question, response, screenshot_path, duration_ms)
                    VALUES (?, ?, ?, ?, ?)
                """, (session_id, question, response, screenshot_path, duration_ms))
                
                interaction_id = cursor.lastrowid
                conn.commit()
            
            logger.info(f"Interaction added: {interaction_id}")
            return interaction_id
            
        except Exception as e:
            logger.error(f"Failed to add interaction: {e}")
            return -1
    
    def get_session_history(self, session_id: int) -> List[Dict]:
        """
        Get all interactions for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of interaction dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, timestamp, question, response, screenshot_path, duration_ms
                    FROM interactions
                    WHERE session_id = ?
                    ORDER BY timestamp
                """, (session_id,))
                
                interactions = []
                for row in cursor.fetchall():
                    interactions.append({
                        "id": row[0],
                        "timestamp": row[1],
                        "question": row[2],
                        "response": row[3],
                        "screenshot_path": row[4],
                        "duration_ms": row[5]
                    })
                
                return interactions
                
        except Exception as e:
            logger.error(f"Failed to get session history: {e}")
            return []
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict]:
        """
        Get recent sessions.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, started_at, ended_at, total_interactions
                    FROM sessions
                    ORDER BY started_at DESC
                    LIMIT ?
                """, (limit,))
                
                sessions = []
                for row in cursor.fetchall():
                    sessions.append({
                        "id": row[0],
                        "started_at": row[1],
                        "ended_at": row[2],
                        "total_interactions": row[3]
                    })
                
                return sessions
                
        except Exception as e:
            logger.error(f"Failed to get recent sessions: {e}")
            return []
    
    def search_interactions(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search interactions by question or response content.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching interaction dictionaries
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                search_pattern = f"%{query}%"
                cursor.execute("""
                    SELECT id, session_id, timestamp, question, response
                    FROM interactions
                    WHERE question LIKE ? OR response LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (search_pattern, search_pattern, limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "id": row[0],
                        "session_id": row[1],
                        "timestamp": row[2],
                        "question": row[3],
                        "response": row[4]
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to search interactions: {e}")
            return []


# Singleton instance
_db_instance: Optional[EdwardDatabase] = None


def get_database() -> EdwardDatabase:
    """
    Get or create singleton database instance.
    
    Returns:
        EdwardDatabase instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = EdwardDatabase()
    return _db_instance


# Example usage
if __name__ == "__main__":
    db = EdwardDatabase()
    
    # Create session
    session_id = db.create_session()
    
    # Add interactions
    db.add_interaction(
        session_id,
        "What's the weather?",
        "I don't have access to weather data yet.",
        duration_ms=1500
    )
    
    # Get history
    history = db.get_session_history(session_id)
    print(f"Session {session_id} has {len(history)} interactions")
    
    # End session
    db.end_session(session_id)

# Made with Bob
