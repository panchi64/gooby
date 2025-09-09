import sqlite3
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class ContextManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        self._lock = asyncio.Lock()
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        username TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        bot_responded BOOLEAN DEFAULT FALSE
                    )
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_channel_time 
                    ON messages(channel_id, timestamp)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_time 
                    ON messages(user_id, timestamp)
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    async def add_message(self, channel_id: str, user_id: str, username: str, 
                         content: str, bot_responded: bool = False):
        """Add a message to the context history"""
        async with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO messages (channel_id, user_id, username, content, timestamp, bot_responded)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (channel_id, user_id, username, content, datetime.utcnow(), bot_responded))
                    
                    conn.commit()
                    
            except Exception as e:
                logger.error(f"Failed to add message to context: {e}")
    
    async def get_recent_messages(self, channel_id: str, limit: int = 20) -> List[Dict]:
        """Get recent messages from a channel for context"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT user_id, username, content, timestamp, bot_responded
                    FROM messages
                    WHERE channel_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (channel_id, limit))
                
                messages = []
                for row in cursor.fetchall():
                    messages.append({
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'content': row['content'],
                        'timestamp': row['timestamp'],
                        'bot_responded': bool(row['bot_responded'])
                    })
                
                # Return in chronological order (oldest first)
                return list(reversed(messages))
                
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            return []
    
    async def get_user_interaction_count(self, user_id: str, days: int = 7) -> int:
        """Get number of interactions with a user in the last N days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT COUNT(*) as count
                    FROM messages
                    WHERE user_id = ? AND timestamp > ?
                """, (user_id, cutoff_date))
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Failed to get user interaction count: {e}")
            return 0
    
    async def cleanup_old_messages(self, days: int = 7):
        """Clean up messages older than specified days"""
        async with self._lock:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        DELETE FROM messages
                        WHERE timestamp < ?
                    """, (cutoff_date,))
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    if deleted_count > 0:
                        logger.info(f"Cleaned up {deleted_count} old messages")
                        
            except Exception as e:
                logger.error(f"Failed to cleanup old messages: {e}")
    
    def format_messages_for_llm(self, messages: List[Dict], bot_name: str = "Gooby") -> str:
        """Format messages for LLM context"""
        if not messages:
            return "No recent conversation history."
        
        context_lines = ["Recent conversation:"]
        
        for msg in messages[-15:]:  # Only use last 15 messages to avoid token limit
            username = msg['username']
            content = msg['content']
            
            # Truncate very long messages
            if len(content) > 150:
                content = content[:147] + "..."
            
            context_lines.append(f"{username}: {content}")
        
        return "\n".join(context_lines)
    
    async def should_respond_based_on_history(self, channel_id: str, user_id: str) -> float:
        """Calculate response probability based on interaction history"""
        try:
            # Get recent messages
            recent_messages = await self.get_recent_messages(channel_id, 10)
            
            if not recent_messages:
                return 0.5  # Default probability
            
            # Count bot responses in recent messages
            bot_responses = sum(1 for msg in recent_messages if msg['bot_responded'])
            total_messages = len(recent_messages)
            
            # Lower probability if bot has been very active
            if bot_responses / total_messages > 0.5:
                return 0.2
            
            # Higher probability if user hasn't interacted much
            user_interactions = await self.get_user_interaction_count(user_id, 1)
            if user_interactions < 3:
                return 0.7
            
            return Config.RESPONSE_CHANCE
            
        except Exception as e:
            logger.error(f"Failed to calculate response probability: {e}")
            return Config.RESPONSE_CHANCE