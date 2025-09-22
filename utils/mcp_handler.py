"""
MCP Handler for Discord Bot

Handles Inter-Process Communication between the Discord bot and MCP servers.
Processes reaction requests from the MCP queue and applies them to Discord messages.
"""

import asyncio
import logging
import sqlite3
import os
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from collections import deque
import discord

logger = logging.getLogger(__name__)

class MCPHandler:
    """Handles MCP communication and reaction queue processing."""

    def __init__(self, bot, db_path: str = "./data/mcp_queue.db"):
        """
        Initialize the MCP handler.

        Args:
            bot: The Discord bot instance
            db_path: Path to the SQLite database for the MCP queue
        """
        self.bot = bot
        self.db_path = db_path
        self.is_running = False
        self.poll_interval = 2.0  # seconds between queue checks
        self._task = None

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize the SQLite database for the MCP queue."""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create reaction queue table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reaction_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL,
                    message_target TEXT NOT NULL,
                    emoji TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP NULL,
                    error_message TEXT NULL
                )
            ''')

            conn.commit()
            conn.close()
            logger.info(f"MCP queue database initialized at {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize MCP database: {e}")
            raise

    async def start(self):
        """Start the MCP handler background task."""
        if self.is_running:
            logger.warning("MCP handler is already running")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._process_queue_loop())
        logger.info("MCP handler started")

    async def stop(self):
        """Stop the MCP handler background task."""
        if not self.is_running:
            return

        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("MCP handler stopped")

    async def _process_queue_loop(self):
        """Main loop for processing the MCP reaction queue."""
        logger.info("MCP queue processing loop started")

        while self.is_running:
            try:
                await self._process_pending_reactions()
                await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                logger.info("MCP queue processing cancelled")
                break
            except Exception as e:
                logger.error(f"Error in MCP queue processing loop: {e}")
                await asyncio.sleep(self.poll_interval)

    async def _process_pending_reactions(self):
        """Process all pending reactions in the queue."""
        try:
            pending_reactions = await self._get_pending_reactions()

            for reaction in pending_reactions:
                await self._process_single_reaction(reaction)

        except Exception as e:
            logger.error(f"Error processing pending reactions: {e}")

    async def _get_pending_reactions(self) -> List[Dict[str, Any]]:
        """Get all pending reaction requests from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, channel_id, message_target, emoji, created_at
                FROM reaction_queue
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT 10
            ''')

            rows = cursor.fetchall()
            conn.close()

            reactions = []
            for row in rows:
                reactions.append({
                    'id': row[0],
                    'channel_id': row[1],
                    'message_target': row[2],
                    'emoji': row[3],
                    'created_at': row[4]
                })

            return reactions

        except Exception as e:
            logger.error(f"Error getting pending reactions: {e}")
            return []

    async def _process_single_reaction(self, reaction: Dict[str, Any]):
        """Process a single reaction request."""
        reaction_id = reaction['id']
        channel_id = reaction['channel_id']
        message_target = reaction['message_target']
        emoji = reaction['emoji']

        try:
            logger.debug(f"Processing reaction {reaction_id}: {emoji} on {message_target} in {channel_id}")

            # Get the Discord channel
            try:
                channel = self.bot.get_channel(int(channel_id))
                if not channel:
                    # Try fetching if not in cache
                    channel = await self.bot.fetch_channel(int(channel_id))
            except (ValueError, discord.NotFound, discord.Forbidden) as e:
                await self._mark_reaction_failed(reaction_id, f"Channel not found or no access: {e}")
                return

            # Determine the target message
            target_message = await self._resolve_target_message(channel, message_target)
            if not target_message:
                await self._mark_reaction_failed(reaction_id, f"Could not resolve target message: {message_target}")
                return

            # Apply the reaction
            try:
                await target_message.add_reaction(emoji)
                await self._mark_reaction_completed(reaction_id)
                logger.info(f"Successfully applied reaction {reaction_id}: {emoji} to message {target_message.id}")

            except discord.Forbidden:
                await self._mark_reaction_failed(reaction_id, "Missing permissions to add reactions")
            except discord.HTTPException as e:
                await self._mark_reaction_failed(reaction_id, f"Failed to add reaction: {e}")

        except Exception as e:
            logger.error(f"Error processing reaction {reaction_id}: {e}")
            await self._mark_reaction_failed(reaction_id, f"Unexpected error: {e}")

    async def _resolve_target_message(self, channel, message_target: str) -> Optional[discord.Message]:
        """
        Resolve a message target to an actual Discord message.

        Args:
            channel: Discord channel object
            message_target: Target specification ("last", number, or message ID)

        Returns:
            Discord message object or None if not found
        """
        try:
            if message_target == "last":
                # Get the last message in the channel (excluding bot messages)
                async for message in channel.history(limit=50):
                    if not message.author.bot:
                        return message
                return None

            elif message_target.isdigit():
                if len(message_target) >= 17:
                    # Looks like a message ID
                    try:
                        return await channel.fetch_message(int(message_target))
                    except (discord.NotFound, discord.Forbidden):
                        return None
                else:
                    # Position-based targeting (e.g., "2" means 2nd message back)
                    position = int(message_target)
                    if position <= 0:
                        return None

                    count = 0
                    async for message in channel.history(limit=50):
                        if not message.author.bot:
                            count += 1
                            if count == position:
                                return message
                    return None

            else:
                logger.warning(f"Invalid message target format: {message_target}")
                return None

        except Exception as e:
            logger.error(f"Error resolving target message {message_target}: {e}")
            return None

    async def _mark_reaction_completed(self, reaction_id: int):
        """Mark a reaction as completed in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE reaction_queue
                SET status = 'completed', processed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (reaction_id,))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error marking reaction {reaction_id} as completed: {e}")

    async def _mark_reaction_failed(self, reaction_id: int, error_message: str):
        """Mark a reaction as failed in the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE reaction_queue
                SET status = 'failed', processed_at = CURRENT_TIMESTAMP, error_message = ?
                WHERE id = ?
            ''', (error_message, reaction_id))

            conn.commit()
            conn.close()

            logger.warning(f"Reaction {reaction_id} failed: {error_message}")

        except Exception as e:
            logger.error(f"Error marking reaction {reaction_id} as failed: {e}")

    async def get_queue_stats(self) -> Dict[str, int]:
        """Get statistics about the reaction queue."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM reaction_queue
                GROUP BY status
            ''')

            stats = dict(cursor.fetchall())
            conn.close()

            return {
                'pending': stats.get('pending', 0),
                'completed': stats.get('completed', 0),
                'failed': stats.get('failed', 0),
                'total': sum(stats.values())
            }

        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {'pending': 0, 'completed': 0, 'failed': 0, 'total': 0}

    async def clear_old_entries(self, days: int = 7):
        """Clear old queue entries older than specified days."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM reaction_queue
                WHERE created_at < datetime('now', '-{} days')
                AND status IN ('completed', 'failed')
            '''.format(days))

            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old reaction queue entries")

        except Exception as e:
            logger.error(f"Error cleaning up old queue entries: {e}")