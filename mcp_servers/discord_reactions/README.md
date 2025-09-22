# Discord Reactions MCP Server

This MCP (Model Context Protocol) server enables Gooby to add reactions to Discord messages through LM Studio tool calls.

## Overview

The MCP server provides tools that allow the LLM (via LM Studio) to request Discord reactions. The server communicates with the Discord bot through a SQLite queue system for reliable message processing.

## Architecture

```
LM Studio (with loaded model)
    ↓ (tool call)
MCP Server (this server)
    ↓ (SQLite queue)
Discord Bot (MCP Handler)
    ↓ (Discord API)
Discord Message (reaction applied)
```

## Tools Provided

### `add_discord_reaction`
Adds a reaction to a Discord message.

**Parameters:**
- `channel_id` (string): Discord channel ID where the message is located
- `message_target` (string): Target message specification:
  - `"last"` - Most recent user message in the channel
  - `"2"`, `"3"`, etc. - Nth message back from most recent
  - `"123456789012345678"` - Specific Discord message ID
- `emoji` (string): Emoji to react with (e.g., "👍", "❤️", "🎉")

**Returns:**
- Success confirmation with queue ID
- Error message if parameters are invalid

### `get_reaction_status`
Checks the status of a reaction request.

**Parameters:**
- `reaction_id` (int): ID of the reaction request to check

**Returns:**
- Status information (pending, completed, failed)

### `list_pending_reactions`
Lists all pending reaction requests in the queue.

**Returns:**
- List of up to 10 pending reactions

## Database Schema

The server uses SQLite for the IPC queue:

```sql
CREATE TABLE reaction_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    message_target TEXT NOT NULL,
    emoji TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    error_message TEXT NULL
);
```

## Usage Examples

When LM Studio calls the tools, they work like this:

```json
{
  "tool": "add_discord_reaction",
  "parameters": {
    "channel_id": "123456789012345678",
    "message_target": "last",
    "emoji": "👍"
  }
}
```

This will add a thumbs up reaction to the most recent user message in the specified channel.

## Error Handling

The server validates all inputs and provides descriptive error messages:
- Invalid channel IDs
- Malformed message targets
- Empty emoji fields
- Database connection issues

## Logging

All operations are logged to stderr (stdout is reserved for MCP protocol). Log levels:
- INFO: Normal operations, queue additions
- WARNING: Validation failures, recoverable errors
- ERROR: Database errors, critical failures

## Integration

This MCP server is automatically configured by the launcher script (`launch.py`) and integrates with:
- LM Studio's MCP configuration (`~/.lmstudio/mcp.json`)
- Discord bot's MCP handler (`utils/mcp_handler.py`)
- Shared SQLite queue database

## Dependencies

See `requirements.txt` for the specific dependencies:
- `fastmcp>=2.0.0` - MCP server framework
- `aiosqlite>=0.20.0` - Async SQLite support
- `aiohttp>=3.9.0` - HTTP client capabilities
- `pydantic>=2.0.0` - Data validation
- `structlog>=24.0.0` - Structured logging