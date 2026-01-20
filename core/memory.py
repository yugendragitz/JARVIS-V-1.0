"""
JARVIS Persistent Memory System
SQLite-backed memory with context awareness
"""

import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
from pathlib import Path
import threading
import logging

logger = logging.getLogger(__name__)


class Memory:
    """
    Persistent memory system with:
    - Key-value storage
    - Context/conversation history
    - Temporal awareness
    - Thread-safe operations
    """
    
    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
        
    def initialize(self) -> bool:
        """Initialize memory database"""
        try:
            self._connection = sqlite3.connect(
                str(self._db_path),
                check_same_thread=False
            )
            self._connection.row_factory = sqlite3.Row
            self._create_tables()
            logger.info(f"Memory initialized: {self._db_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize memory: {e}")
            return False
    
    def _create_tables(self):
        """Create required database tables"""
        with self._lock:
            cursor = self._connection.cursor()
            
            # Key-value store for general memory
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    type TEXT DEFAULT 'string',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NULL
                )
            """)
            
            # Conversation history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    intent TEXT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User preferences
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Facts Jarvis learns about the user
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    fact TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    source TEXT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self._connection.commit()
    
    # ══════════════════════════════════════════════════════════════════════════
    # KEY-VALUE OPERATIONS
    # ══════════════════════════════════════════════════════════════════════════
    
    def set(self, key: str, value: Any, ttl_seconds: int = None):
        """
        Store a value in memory
        
        Args:
            key: Storage key
            value: Value to store (will be JSON serialized)
            ttl_seconds: Optional time-to-live in seconds
        """
        with self._lock:
            try:
                cursor = self._connection.cursor()
                
                # Determine type and serialize
                if isinstance(value, dict):
                    type_str = 'dict'
                    value_str = json.dumps(value)
                elif isinstance(value, list):
                    type_str = 'list'
                    value_str = json.dumps(value)
                elif isinstance(value, bool):
                    type_str = 'bool'
                    value_str = str(value)
                elif isinstance(value, (int, float)):
                    type_str = 'number'
                    value_str = str(value)
                else:
                    type_str = 'string'
                    value_str = str(value)
                
                expires_at = None
                if ttl_seconds:
                    expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO memory (key, value, type, updated_at, expires_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
                """, (key, value_str, type_str, expires_at))
                
                self._connection.commit()
                logger.debug(f"Memory set: {key}")
                
            except Exception as e:
                logger.error(f"Memory set error: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from memory"""
        with self._lock:
            try:
                cursor = self._connection.cursor()
                cursor.execute("""
                    SELECT value, type, expires_at FROM memory WHERE key = ?
                """, (key,))
                
                row = cursor.fetchone()
                if not row:
                    return default
                
                # Check expiration
                if row['expires_at']:
                    expires = datetime.fromisoformat(row['expires_at'])
                    if datetime.now() > expires:
                        self.delete(key)
                        return default
                
                # Deserialize based on type
                value_str = row['value']
                type_str = row['type']
                
                if type_str == 'dict' or type_str == 'list':
                    return json.loads(value_str)
                elif type_str == 'bool':
                    return value_str.lower() == 'true'
                elif type_str == 'number':
                    return float(value_str) if '.' in value_str else int(value_str)
                else:
                    return value_str
                    
            except Exception as e:
                logger.error(f"Memory get error: {e}")
                return default
    
    def delete(self, key: str):
        """Delete a key from memory"""
        with self._lock:
            try:
                cursor = self._connection.cursor()
                cursor.execute("DELETE FROM memory WHERE key = ?", (key,))
                self._connection.commit()
            except Exception as e:
                logger.error(f"Memory delete error: {e}")
    
    def exists(self, key: str) -> bool:
        """Check if key exists in memory"""
        return self.get(key) is not None
    
    # ══════════════════════════════════════════════════════════════════════════
    # CONVERSATION HISTORY
    # ══════════════════════════════════════════════════════════════════════════
    
    def add_conversation(self, role: str, content: str, intent: str = None):
        """Add a conversation entry"""
        with self._lock:
            try:
                cursor = self._connection.cursor()
                cursor.execute("""
                    INSERT INTO conversations (role, content, intent)
                    VALUES (?, ?, ?)
                """, (role, content, intent))
                self._connection.commit()
            except Exception as e:
                logger.error(f"Add conversation error: {e}")
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""
        with self._lock:
            try:
                cursor = self._connection.cursor()
                cursor.execute("""
                    SELECT role, content, intent, timestamp 
                    FROM conversations 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in reversed(rows)]
                
            except Exception as e:
                logger.error(f"Get conversations error: {e}")
                return []
    
    def clear_old_conversations(self, days: int = 7):
        """Clear conversations older than specified days"""
        with self._lock:
            try:
                cursor = self._connection.cursor()
                cutoff = datetime.now() - timedelta(days=days)
                cursor.execute("""
                    DELETE FROM conversations WHERE timestamp < ?
                """, (cutoff,))
                self._connection.commit()
                logger.info(f"Cleared conversations older than {days} days")
            except Exception as e:
                logger.error(f"Clear conversations error: {e}")
    
    # ══════════════════════════════════════════════════════════════════════════
    # PREFERENCES
    # ══════════════════════════════════════════════════════════════════════════
    
    def set_preference(self, key: str, value: str):
        """Set a user preference"""
        with self._lock:
            try:
                cursor = self._connection.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO preferences (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (key, value))
                self._connection.commit()
            except Exception as e:
                logger.error(f"Set preference error: {e}")
    
    def get_preference(self, key: str, default: str = None) -> Optional[str]:
        """Get a user preference"""
        with self._lock:
            try:
                cursor = self._connection.cursor()
                cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
                row = cursor.fetchone()
                return row['value'] if row else default
            except Exception as e:
                logger.error(f"Get preference error: {e}")
                return default
    
    # ══════════════════════════════════════════════════════════════════════════
    # FACTS (Learning about user)
    # ══════════════════════════════════════════════════════════════════════════
    
    def learn_fact(self, category: str, fact: str, confidence: float = 1.0, source: str = None):
        """Store a fact about the user"""
        with self._lock:
            try:
                cursor = self._connection.cursor()
                cursor.execute("""
                    INSERT INTO facts (category, fact, confidence, source)
                    VALUES (?, ?, ?, ?)
                """, (category, fact, confidence, source))
                self._connection.commit()
                logger.info(f"Learned fact [{category}]: {fact}")
            except Exception as e:
                logger.error(f"Learn fact error: {e}")
    
    def get_facts(self, category: str = None) -> List[Dict]:
        """Get stored facts, optionally filtered by category"""
        with self._lock:
            try:
                cursor = self._connection.cursor()
                
                if category:
                    cursor.execute("""
                        SELECT category, fact, confidence, source, created_at
                        FROM facts WHERE category = ?
                        ORDER BY confidence DESC, created_at DESC
                    """, (category,))
                else:
                    cursor.execute("""
                        SELECT category, fact, confidence, source, created_at
                        FROM facts
                        ORDER BY confidence DESC, created_at DESC
                    """)
                
                return [dict(row) for row in cursor.fetchall()]
                
            except Exception as e:
                logger.error(f"Get facts error: {e}")
                return []
    
    def recall(self, query: str) -> Optional[str]:
        """
        Try to recall information related to a query
        Searches through facts and memory
        """
        # Search facts
        facts = self.get_facts()
        query_lower = query.lower()
        
        for fact in facts:
            if query_lower in fact['fact'].lower() or query_lower in fact['category'].lower():
                return fact['fact']
        
        # Search memory keys
        with self._lock:
            try:
                cursor = self._connection.cursor()
                cursor.execute("""
                    SELECT key, value FROM memory 
                    WHERE key LIKE ? OR value LIKE ?
                """, (f"%{query}%", f"%{query}%"))
                
                row = cursor.fetchone()
                if row:
                    return f"{row['key']}: {row['value']}"
                    
            except Exception as e:
                logger.error(f"Recall error: {e}")
        
        return None
    
    # ══════════════════════════════════════════════════════════════════════════
    # MAINTENANCE
    # ══════════════════════════════════════════════════════════════════════════
    
    def cleanup(self):
        """Run maintenance tasks"""
        self._cleanup_expired()
        self.clear_old_conversations(days=30)
    
    def _cleanup_expired(self):
        """Remove expired memory entries"""
        with self._lock:
            try:
                cursor = self._connection.cursor()
                cursor.execute("""
                    DELETE FROM memory WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
                """)
                self._connection.commit()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        with self._lock:
            try:
                cursor = self._connection.cursor()
                
                cursor.execute("SELECT COUNT(*) as count FROM memory")
                memory_count = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM conversations")
                conv_count = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM facts")
                facts_count = cursor.fetchone()['count']
                
                return {
                    'memory_entries': memory_count,
                    'conversations': conv_count,
                    'facts': facts_count
                }
                
            except Exception as e:
                logger.error(f"Get stats error: {e}")
                return {}
    
    def shutdown(self):
        """Gracefully shutdown memory system"""
        logger.info("Shutting down memory system...")
        self.cleanup()
        
        if self._connection:
            self._connection.close()
            self._connection = None
        
        logger.info("Memory system shutdown complete")


# Global memory instance
_memory_instance: Optional[Memory] = None


def get_memory() -> Memory:
    """Get or create global memory instance"""
    global _memory_instance
    if _memory_instance is None:
        from config import MEMORY_DB
        _memory_instance = Memory(MEMORY_DB)
        _memory_instance.initialize()
    return _memory_instance
