#!/usr/bin/env python3
"""
Script to show the last 20 messages that Gooby's LLM sees, 
in the exact format it receives them for response generation.
"""
import sys
import sqlite3
from pathlib import Path

def get_recent_messages_from_db(db_path: str, limit: int = 20):
    """Get recent messages from the database"""
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT user_id, username, content, timestamp, bot_responded, image_urls
                FROM messages
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
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
        print(f"Failed to get recent messages: {e}")
        return []

def format_messages_for_llm(messages, max_messages: int = 20, max_content_length=None):
    """Format messages exactly like the LLM sees them - using the same logic from context.py"""
    if not messages:
        return "No recent conversation history."
    
    context_lines = ["Recent conversation:"]
    
    # Use the specified number of messages
    messages_to_use = messages[-max_messages:] if len(messages) > max_messages else messages
    
    for msg in messages_to_use:
        username = msg.get('username', 'Unknown')
        content = msg.get('content', '')
        
        # Truncate very long messages if limit specified
        if max_content_length and len(content) > max_content_length:
            content = content[:max_content_length-3] + "..."
        
        context_lines.append(f"{username}: {content}")
    
    return "\n".join(context_lines)

def main():
    # Database path
    db_path = "./data/gooby.db"
    
    if not Path(db_path).exists():
        print(f"Database not found at {db_path}")
        print("Make sure Gooby has been running and has processed some messages.")
        sys.exit(1)
    
    print("=" * 60)
    print("LAST 20 MESSAGES AS SEEN BY GOOBY'S LLM")
    print("=" * 60)
    print()
    
    # Get recent messages
    messages = get_recent_messages_from_db(db_path, limit=20)
    
    if not messages:
        print("No messages found in database.")
        sys.exit(1)
    
    # Format them exactly like the LLM sees them for response generation
    # (This uses the same logic as build_unified_context in "response" mode)
    formatted_context = format_messages_for_llm(
        messages,
        max_messages=20,
        max_content_length=None  # No truncation for response mode
    )
    
    print(formatted_context)
    print()
    print("This would be followed by something like:")
    print("Respond to [USERNAME]: [their current message]")
    print()
    print("=" * 60)
    print(f"Total messages shown: {len(messages)}")
    
    # Show some stats
    bot_messages = [msg for msg in messages if msg['bot_responded']]
    user_messages = [msg for msg in messages if not msg['bot_responded']]
    
    print(f"User messages: {len(user_messages)}")
    print(f"Bot messages: {len(bot_messages)}")
    print("=" * 60)

if __name__ == "__main__":
    main()