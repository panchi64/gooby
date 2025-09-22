#!/usr/bin/env python3
"""
Discord Reactions MCP Server

This MCP server provides tools for Gooby to add reactions to Discord messages.
It communicates with the Discord bot through a SQLite queue system.
"""

import asyncio
import logging
import os
import sys
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime

# Import MCP framework
try:
    from fastmcp import FastMCP
except ImportError:
    print("FastMCP not installed. Install with: pip install fastmcp", file=sys.stderr)
    sys.exit(1)

# Configure logging to stderr (stdout is reserved for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("discord_reactions_mcp")

# Initialize FastMCP server
mcp = FastMCP("discord-reactions")

# Database path for IPC queue (relative to bot's root directory)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "mcp_queue.db")

def init_database():
    """Initialize the SQLite database for reaction queue."""
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create reaction queue table
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
        logger.info(f"Initialized MCP queue database at {DB_PATH}")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def add_reaction_to_queue(channel_id: str, message_target: str, emoji: str) -> int:
    """Add a reaction request to the queue."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO reaction_queue (channel_id, message_target, emoji)
            VALUES (?, ?, ?)
        ''', (channel_id, message_target, emoji))

        reaction_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"Added reaction to queue: {reaction_id} - {emoji} on {message_target} in {channel_id}")
        return reaction_id

    except Exception as e:
        logger.error(f"Failed to add reaction to queue: {e}")
        raise

@mcp.tool()
async def add_discord_reaction(
    channel_id: str,
    message_target: str,
    emoji: str
) -> str:
    """
    Add a reaction to a Discord message.

    Args:
        channel_id: The Discord channel ID where the message is located
        message_target: Target message - either "last" for the most recent message,
                       or a number (e.g., "2") for the Nth message back,
                       or a specific message ID
        emoji: The emoji to react with (e.g., "👍", "❤️", "🎉")

    Returns:
        Success message or error description
    """
    try:
        # Validate inputs
        if not channel_id or not channel_id.isdigit():
            return "Error: channel_id must be a valid Discord channel ID (numeric string)"

        if not message_target:
            return "Error: message_target cannot be empty"

        if not emoji:
            return "Error: emoji cannot be empty"

        # Validate message_target format
        if message_target not in ["last", "none"] and not message_target.isdigit():
            # Check if it's a message ID (Discord message IDs are typically 17-19 digits)
            if not (len(message_target) >= 17 and message_target.isdigit()):
                return "Error: message_target must be 'last', a number, or a valid message ID"

        # Add reaction request to queue
        reaction_id = await add_reaction_to_queue(channel_id, message_target, emoji)

        return f"✅ Reaction request added to queue (ID: {reaction_id}). The bot will process it shortly."

    except Exception as e:
        logger.error(f"Error in add_discord_reaction: {e}")
        return f"Error: Failed to add reaction - {str(e)}"

@mcp.tool()
async def get_reaction_status(reaction_id: int) -> str:
    """
    Check the status of a reaction request.

    Args:
        reaction_id: The ID of the reaction request to check

    Returns:
        Status information about the reaction request
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT channel_id, message_target, emoji, status, created_at, processed_at, error_message
            FROM reaction_queue
            WHERE id = ?
        ''', (reaction_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return f"❌ Reaction request {reaction_id} not found"

        channel_id, message_target, emoji, status, created_at, processed_at, error_message = row

        status_info = {
            "id": reaction_id,
            "channel_id": channel_id,
            "message_target": message_target,
            "emoji": emoji,
            "status": status,
            "created_at": created_at,
            "processed_at": processed_at
        }

        if error_message:
            status_info["error"] = error_message

        if status == "pending":
            return f"⏳ Reaction {reaction_id} is pending processing"
        elif status == "completed":
            return f"✅ Reaction {reaction_id} completed successfully at {processed_at}"
        elif status == "failed":
            return f"❌ Reaction {reaction_id} failed: {error_message}"
        else:
            return f"ℹ️ Reaction {reaction_id}: {json.dumps(status_info, indent=2)}"

    except Exception as e:
        logger.error(f"Error checking reaction status: {e}")
        return f"Error: Failed to check status - {str(e)}"

@mcp.tool()
async def list_pending_reactions() -> str:
    """
    List all pending reaction requests.

    Returns:
        List of pending reactions or empty message if none
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, channel_id, message_target, emoji, created_at
            FROM reaction_queue
            WHERE status = 'pending'
            ORDER BY created_at DESC
            LIMIT 10
        ''')

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return "📭 No pending reactions in queue"

        reactions = []
        for row in rows:
            reaction_id, channel_id, message_target, emoji, created_at = row
            reactions.append(f"  {reaction_id}: {emoji} → {message_target} in channel {channel_id} ({created_at})")

        return f"📋 Pending reactions ({len(rows)}):\n" + "\n".join(reactions)

    except Exception as e:
        logger.error(f"Error listing pending reactions: {e}")
        return f"Error: Failed to list reactions - {str(e)}"

def main():
    """Run the MCP server."""
    try:
        # Initialize database
        init_database()

        logger.info("Starting Discord Reactions MCP Server...")
        logger.info(f"Database path: {DB_PATH}")

        # Run the MCP server using stdio transport
        mcp.run(transport="stdio")

    except KeyboardInterrupt:
        logger.info("MCP server stopped by user")
    except Exception as e:
        logger.error(f"MCP server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()