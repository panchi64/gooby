# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Setup & Installation:**
```bash
# Initial setup
./setup.py  # or python setup.py

# Manual setup
python3 -m venv gooby-env
source gooby-env/bin/activate  # On Windows: gooby-env\Scripts\activate
pip install -r requirements.txt
```

**Running the Bot:**
```bash
# Activate virtual environment first
source gooby-env/bin/activate

# Run the bot
python bot.py
```

**Testing and Development:**
- No specific test framework configured - verify functionality by running the bot and testing Discord interactions
- Bot requires LM Studio running locally on port 1234 with a loaded model
- Configuration is managed through `.env` file (copy from `.env.example`)

## Architecture Overview

**Core Structure:**
- `bot.py` - Main Discord bot entry point with GoobyBot class
- `config.py` - Configuration management and personality loading
- `cogs/` - Discord.py cog modules for features (chat, images, dice, admin)
- `utils/` - Utility modules for LLM, context, image search
- `data/` - Runtime data (SQLite database, logs)

**Key Components:**
1. **Chat System** (`cogs/chat.py`):
   - Handles AI conversations via LM Studio
   - Uses context management for conversation memory
   - Implements personality-based decision making for when to respond
   - Rate limiting per channel

2. **LLM Integration** (`utils/llm_client.py`):
   - Interfaces with local LM Studio API
   - Fallback responses when AI unavailable
   - Configurable temperature, max tokens, timeout

3. **Context Management** (`utils/context.py`):
   - SQLite database for conversation history
   - Message tracking and retrieval
   - User interaction memory

4. **Personality System**:
   - Personality loaded from `gooby_personality.md`
   - Decision making logic in `gooby_decision.md`
   - Runtime personality reloading capability

**Dependencies:**
- discord.py >= 2.3.0 for Discord API
- python-dotenv for environment management
- aiohttp for HTTP requests
- duckduckgo-search for image search

**Configuration:**
- Environment variables loaded from `.env` file
- Key settings: DISCORD_TOKEN, ALLOWED_SERVER_ID, LM_STUDIO_URL
- Bot restricted to specific server by default for security
- Personality and response behavior configurable

**Important Notes:**
- Bot requires "Message Content Intent" enabled in Discord Developer Portal
- LM Studio must be running locally with a loaded model before starting bot
- Database automatically created on first run in `data/` directory