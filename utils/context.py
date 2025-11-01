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
    
    def is_channel_allowed(self, channel_id: str) -> bool:
        """Check if a channel is allowed based on configuration"""
        if not Config.ALLOWED_CHANNELS:
            return True  # If no channels specified, all channels are allowed
        
        try:
            channel_id_int = int(channel_id)
            return channel_id_int in Config.ALLOWED_CHANNELS
        except (ValueError, TypeError):
            logger.error(f"Invalid channel_id format: {channel_id}")
            return False
    
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
                        bot_responded BOOLEAN DEFAULT FALSE,
                        image_urls TEXT DEFAULT NULL
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
                
                # Add image_urls column to existing tables if it doesn't exist
                try:
                    conn.execute("ALTER TABLE messages ADD COLUMN image_urls TEXT DEFAULT NULL")
                    logger.info("Added image_urls column to existing messages table")
                except sqlite3.OperationalError:
                    # Column already exists
                    pass
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    async def add_message(self, channel_id: str, user_id: str, username: str, 
                         content: str, bot_responded: bool = False, image_urls: List[str] = None):
        """Add a message to the context history"""
        # Check if channel is allowed before storing
        if not self.is_channel_allowed(channel_id):
            logger.debug(f"Skipping message storage for non-allowed channel: {channel_id}")
            return
        
        async with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # Convert image URLs list to JSON string for storage
                    image_urls_json = None
                    if image_urls:
                        import json
                        image_urls_json = json.dumps(image_urls)
                    
                    conn.execute("""
                        INSERT INTO messages (channel_id, user_id, username, content, timestamp, bot_responded, image_urls)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (channel_id, user_id, username, content, datetime.utcnow(), bot_responded, image_urls_json))
                    
                    conn.commit()
                    
            except Exception as e:
                logger.error(f"Failed to add message to context: {e}")
    
    async def get_recent_messages(self, channel_id: str, limit: int = 20) -> List[Dict]:
        """Get recent messages from a channel for context"""
        # Check if channel is allowed before retrieving
        if not self.is_channel_allowed(channel_id):
            logger.debug(f"Skipping message retrieval for non-allowed channel: {channel_id}")
            return []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT user_id, username, content, timestamp, bot_responded, image_urls
                    FROM messages
                    WHERE channel_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (channel_id, limit))
                
                messages = []
                for row in cursor.fetchall():
                    # Parse image URLs from JSON
                    image_urls = []
                    if row['image_urls']:
                        import json
                        try:
                            image_urls = json.loads(row['image_urls'])
                        except json.JSONDecodeError:
                            image_urls = []
                    
                    messages.append({
                        'user_id': row['user_id'],
                        'username': row['username'],
                        'content': row['content'],
                        'timestamp': row['timestamp'],
                        'bot_responded': bool(row['bot_responded']),
                        'image_urls': image_urls
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
    
    async def wipe_all_messages(self) -> int:
        """
        Completely wipe all messages from the database.
        Used for admin memory reset functionality.
        
        Returns:
            int: Number of messages deleted
        """
        async with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # Get count before deletion for reporting
                    cursor = conn.execute("SELECT COUNT(*) FROM messages")
                    count = cursor.fetchone()[0]
                    
                    # Delete all messages
                    conn.execute("DELETE FROM messages")
                    conn.commit()
                    
                    logger.info(f"Wiped all {count} messages from database")
                    return count
                    
            except Exception as e:
                logger.error(f"Failed to wipe all messages: {e}")
                return 0
    
    def format_messages_for_llm(self, messages: List[Dict], bot_name: str = "Gooby", 
                               max_messages: int = 15, max_content_length: int = 150) -> str:
        """Format messages for LLM context with configurable limits"""
        if not messages:
            return "No recent conversation history."
        
        context_lines = ["Recent conversation:"]
        
        # Use the specified number of messages
        for msg in messages[-max_messages:]:
            username = msg['username']
            content = msg['content']
            
            # Truncate very long messages if limit specified
            if max_content_length and len(content) > max_content_length:
                content = content[:max_content_length-3] + "..."
            
            context_lines.append(f"{username}: {content}")
        
        return "\n".join(context_lines)
    
    def format_mixed_messages(self, messages, max_messages: int = 15, 
                            max_content_length: int = None, mode: str = "response") -> str:
        """
        Format messages for LLM context with clear structure and instructions
        
        Args:
            messages: List of messages (dict or Discord objects)
            max_messages: Maximum number of messages to include
            max_content_length: Max length per message (None for no limit)
            mode: "decision" or "response" - determines formatting and instructions
            
        Returns:
            Structured context string with instructions for the LLM
        """
        # Build the chat history section
        history_lines = []
        
        if messages:
            messages_to_use = messages[-max_messages:] if len(messages) > max_messages else messages
            
            for msg in messages_to_use:
                # Handle both dictionary format (from DB) and Discord message objects
                if isinstance(msg, dict):
                    username = msg.get('username', 'Unknown')
                    content = msg.get('content', '')
                else:
                    # Discord message object
                    username = getattr(msg.author, 'display_name', 'Unknown')
                    content = getattr(msg, 'content', '')
                
                # Truncate very long messages if limit specified
                if max_content_length and len(content) > max_content_length:
                    content = content[:max_content_length-3] + "..."
                
                history_lines.append(f"{username}: {content}")
        
        # Format based on mode
        if mode == "decision":
            # Decision mode: Should Gooby respond?
            if history_lines:
                context = (
                    "You are being shown recent Discord chat history for context. "
                    "Use this to understand the conversation flow and determine if Gooby should respond.\n\n"
                    "=== CHAT HISTORY (Most Recent Messages) ===\n"
                    f"{chr(10).join(history_lines)}\n"
                    "=== END CHAT HISTORY ==="
                )
            else:
                context = (
                    "You are in a Discord chat with no recent conversation history.\n\n"
                    "=== CHAT HISTORY ===\n"
                    "(No recent messages)\n"
                    "=== END CHAT HISTORY ==="
                )
        else:
            # Response mode: Generate Gooby's response
            if history_lines:
                context = (
                    "You are being shown recent Discord chat history for context. "
                    "Use this to understand the conversation and craft an appropriate response as Gooby.\n\n"
                    "=== CHAT HISTORY (Most Recent Messages) ===\n"
                    f"{chr(10).join(history_lines)}\n"
                    "=== END CHAT HISTORY ==="
                )
            else:
                context = (
                    "You are in a Discord chat with no recent conversation history.\n\n"
                    "=== CHAT HISTORY ===\n"
                    "(No recent messages)\n"
                    "=== END CHAT HISTORY ==="
                )
        
        return context