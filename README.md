<div align="center">

# 🧌 Gooby Discord Bot

**A competent goblin assistant who learned everything from the internet's weird corners.**

*Gooby provides genuinely helpful responses with a quirky goblin perspective - think "IT support raised by Wikipedia and Reddit."*

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Discord.py](https://img.shields.io/badge/Discord.py-2.3+-blue.svg)](https://discordpy.readthedocs.io/)
[![LM Studio](https://img.shields.io/badge/AI-LM%20Studio-orange.svg)](https://lmstudio.ai/)

[Features](#-features) • [Quick Start](#-quick-start) • [Commands](#-commands) • [Configuration](#️-configuration) • [Development](#-development)

</div>

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🚀 Quick Start](#-quick-start)
- [🎮 Commands](#-commands)
- [⚙️ Configuration](#️-configuration)
- [📁 Project Structure](#-project-structure)
- [🎭 Gooby's Personality](#-goobys-personality)
- [💻 Development](#-development)
- [🐛 Troubleshooting](#-troubleshooting)

---

## ✨ Features

### 🤖 **AI-Powered Chat**
- Local LM Studio integration for privacy
- Context-aware conversations with memory
- Intelligent response decision making
- Supports image analysis (multimodal)
- Rate limiting and server restrictions


### 🎲 **Dice Rolling**
- Advanced dice expressions (`3d20 + 5`, `2d6 - 1d4`)
- Individual roll breakdowns
- Safety limits and error handling
- Special highlighting for critical rolls

### 🖼️ **Image Search**
- DuckDuckGo image search
- Paginated results with navigation
- Random image discovery
- Search result caching

### 🛡️ **Administration**
- Memory wipe functionality
- Personality reload without restart
- Server and channel restrictions
- Comprehensive logging

**Tech Stack:** Python 3.9+, discord.py 2.3+, LM Studio, SQLite

---

## 🚀 Quick Start

**Prerequisites:**
- Python 3.9+
- [LM Studio](https://lmstudio.ai) with a loaded model
- Discord bot token and server ID

**Setup:**

```bash
# Clone and setup
git clone https://github.com/yourusername/gooby.git
cd gooby

# Option 1: Use setup script
python setup.py

# Option 2: Manual setup
python3 -m venv gooby-env
source gooby-env/bin/activate  # Windows: gooby-env\Scripts\activate
pip install -r requirements.txt
```

**Configure:**

1. Create `.env` file (copy from `.env.example` if available)
2. Add your Discord bot token and server ID
3. Start LM Studio with a loaded model on `localhost:1234`
4. Run: `python bot.py`

**Required Environment Variables:**
```bash
DISCORD_TOKEN=your_bot_token_here
ALLOWED_SERVER_ID=your_server_id_here
```

---

## ⚙️ Configuration

### 🔑 Discord Setup

<details>
<summary><b>🤖 Creating Your Discord Bot</b></summary>

1. **Create Application**
   - Visit [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application"
   - Name your bot (e.g., "Gooby")

2. **Configure Bot**
   - Go to "Bot" section
   - Click "Add Bot"
   - **Important**: Enable "Message Content Intent"
   - Copy the bot token (keep this secret!)

3. **Set Permissions**
   - Go to "OAuth2" > "URL Generator"
   - Select scopes: `bot`, `applications.commands`
   - Select permissions: `Send Messages`, `Use Slash Commands`, `Attach Files`, `Read Message History`

4. **Invite to Server**
   - Use the generated URL to invite bot to your server
   - Make sure you have "Manage Server" permission

</details>

<details>
<summary><b>🆔 Finding Your Server ID</b></summary>

1. Enable Developer Mode in Discord:
   - User Settings → Advanced → Developer Mode (ON)
2. Right-click your server name
3. Select "Copy Server ID"
4. Paste this ID in your `.env` file

</details>

### 🧠 LM Studio Setup

<details>
<summary><b>🛠️ LM Studio Configuration</b></summary>

1. **Download & Install**
   - Get LM Studio from [lmstudio.ai](https://lmstudio.ai)
   - Install and launch the application

2. **Download a Model**
   - Recommended models for Gooby:
     - `microsoft/DialoGPT-medium` (lightweight, good for chat)
     - `TheBloke/Llama-2-7B-Chat-GGML` (better quality, needs more RAM)
     - `microsoft/DialoGPT-large` (balanced option)

3. **Configure Server**
   - Load your chosen model
   - Go to "Server" tab
   - Start server on `localhost:1234`
   - Recommended settings:
     ```
     Temperature: 0.7
     Max Tokens: 200
     Top P: 0.9
     ```

4. **Test Connection**
   ```bash
   curl http://localhost:1234/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"messages":[{"role":"user","content":"Hello"}]}'
   ```

</details>

### 📝 Environment Variables

**Create/Edit `.env` file:**

```env
# ===== REQUIRED SETTINGS =====
# Your Discord bot token (keep this secret!)
DISCORD_TOKEN=your_bot_token_here

# Server ID where Gooby should respond (for security)
ALLOWED_SERVER_ID=your_server_id_here

# ===== OPTIONAL SETTINGS =====
# Bot command prefix for legacy commands (default: !)
BOT_PREFIX=!

# LM Studio API endpoint (default: local)
LM_STUDIO_URL=http://localhost:1234/v1/chat/completions

# Maximum conversation history to remember (default: 50)
MAX_CONTEXT_LENGTH=50

# AI response timeout in seconds (default: 30)
AI_TIMEOUT=30

# Enable debug logging (true/false, default: false)
DEBUG_MODE=false

# Custom personality file path (optional)
# PERSONALITY_FILE=custom_personality.md
```

---

## 🎮 Commands

### ⚡ Slash Commands

| Command | Parameters | Description | Example |
|---------|-----------|-------------|--------|
| `/image` | `query` | Search for images | `/image cute puppies` |
| `/randomimage` | - | Get a random image | `/randomimage` |
| `/roll` | `expression` | Roll dice with expressions | `/roll 3d20`, `/roll 1d4 + 2d6 + 5` |
| `/reload_personality` | - | Reload personality file (owner only) | `/reload_personality` |
| `/wipememory` | - | Wipe bot's memory (admin only) | `/wipememory` |

### 📝 Prefix Commands

| Command | Format | Description |
|---------|--------|------------|
| `!goob` | `!goob [message]` | Chat with Gooby |
| `!image` | `!image [search query]` | Search images |
| `!roll` | `!roll [expression]` | Roll dice (aliases: `!dice`, `!r`) |
| `!reload` | `!reload` | Reload personality (owner only) |

### 🤖 Auto-Responses

Gooby uses a two-stage AI decision system:

1. **AI Decision Stage**: LLM analyzes conversation context to decide if Gooby should respond
2. **Response Generation**: If decided to respond, generates an appropriate reply

**Always responds to:**
- Direct mentions (`@Gooby`)
- Replies to Gooby's messages
- Slash commands and prefix commands

**Intelligently decides whether to respond to:**
- General conversation (based on context and relevance)
- Questions and help requests
- Natural conversation flow

**Features:**
- Context-aware conversation memory
- Rate limiting (3 seconds between responses per channel)
- Server and channel restrictions
- Multimodal support (can analyze images)

---

## 📁 Project Structure

```
gooby/
├── 📄 bot.py                    # Main bot entry point & event handlers
├── ⚙️ config.py                 # Configuration management & validation
├── 📋 requirements.txt          # Python dependencies
├── 🔐 .env                     # Environment variables (create from .env.example)
├── 🎭 gooby_personality.md     # Personality configuration
├── 🧠 gooby_decision.md        # Decision-making logic
├── 📖 CLAUDE.md                # Development guidance for Claude Code
├── 🛠️ setup.py                 # Setup script
├── 🔍 show_llm_context.py      # Context debugging utility
│
├── 🧩 cogs/                    # Bot feature modules (Discord.py cogs)
│   ├── 💬 chat.py              # AI chat, personality & auto-responses
│   ├── 🖼️ images.py            # Image search & random images
│   ├── 🎲 dice.py              # Dice rolling with natural language parsing
│   └── 🛡️ admin.py             # Administrative commands
│
├── 🛠️ utils/                   # Helper modules & utilities
│   ├── 🤖 llm_client.py        # LM Studio API integration
│   ├── 🔍 image_search.py      # DuckDuckGo image search
│   └── 💾 context.py           # Conversation memory & database
│
└── 💾 data/                    # Runtime data (created automatically)
    ├── 🗄️ gooby.db             # SQLite conversation history
    └── 📊 logs/                # Application logs
```

**Key Files Explained:**

- **`bot.py`**: Main application entry point, Discord client setup, event handlers
- **`config.py`**: Configuration management with personality and decision prompt loading
- **`gooby_personality.md`**: Goblin assistant personality definition and response rules
- **`gooby_decision.md`**: LLM prompt for intelligent response decision making
- **`cogs/`**: Modular bot features using Discord.py's cog system
- **`utils/`**: Reusable utility classes for AI, images, and data management
- **`data/gooby.db`**: SQLite database storing conversation context and user interactions

---

## 🎭 Gooby's Personality

**A competent goblin assistant who learned everything from the internet's weird corners.**

### 🌟 Core Identity

- **🧌 IT Goblin**: Surprisingly competent but explains things oddly
- **🤝 Helpful First**: Actually solves problems, entertainment second
- **🧠 Internet-Raised**: Sees world through internet lens
- **⚡ Brief & Direct**: Keeps responses short and to the point
- **🎯 Contextual**: Remembers conversations and stays on topic

### 💬 Speech Patterns

**Golden Rule:** Be actually helpful first, entertainingly weird second.

```
✅ "Clear your cache and cookies. browsers hoard memories like elephants"
✅ "Check semicolons, code gets dramatic about punctuation"
✅ "Restart it, computers need naps sometimes"
✅ "doors are just walls that gave up"

❌ "Goob-tastic vibes, goober!" (overly cutesy)
❌ "That's very suspicious..." (overused phrase)
❌ Long explanations with random observations
```

### 🎯 Response Examples

**User**: "My computer is slow"
**Gooby**: "Restart it, computers need naps sometimes"

**User**: "Can you help with Python?"
**Gooby**: "Code problems usually mean missing semicolons or angry brackets"

**User**: "I'm stressed about work"
**Gooby**: "Makes sense, world demanding lately"

**User**: "React to this with 🎉"
**Gooby**: `[REACT:last:🎉]`

---

## ⚙️ Configuration

Create a `.env` file with your bot configuration:

```env
# Required
DISCORD_TOKEN=your_bot_token_here
ALLOWED_SERVER_ID=your_server_id_here

# Optional
BOT_PREFIX=!
LM_STUDIO_URL=http://localhost:1234/v1/chat/completions
CONTEXT_MESSAGE_LIMIT=20
LM_STUDIO_TIMEOUT=30
MAX_TOKENS=2000
```

### Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and bot
3. Enable "Message Content Intent" under Bot settings
4. Copy the bot token to your `.env` file
5. Invite bot to your server with necessary permissions

### LM Studio Setup

1. Download and install [LM Studio](https://lmstudio.ai)
2. Load a compatible model (any chat model works)
3. Start the local server on `localhost:1234`
4. Ensure it's running before starting the bot

---

## 🐛 Troubleshooting

**Bot not responding:**
- Check LM Studio is running with a model loaded
- Verify "Message Content Intent" is enabled
- Ensure bot has proper permissions in Discord


**Connection issues:**
- Verify `.env` file has correct tokens
- Test LM Studio API: `curl http://localhost:1234/v1/models`

---

## 💻 Development

**Adding new commands:**
1. Create new methods in relevant cog files
2. Use `@app_commands.command()` for slash commands
3. Use `@commands.command()` for prefix commands

**Customizing personality:**
1. Edit `gooby_personality.md`
2. Reload with `/reload_personality` command (owner only)

**Project structure:**
- `bot.py` - Main bot entry point
- `cogs/` - Feature modules (chat, images, dice, admin)
- `utils/` - Helper utilities (LLM client, image search, etc.)
- `config.py` - Configuration and personality loading

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

---

<div align="center">

**🧌 A competent goblin assistant for Discord**

Made with ❤️ by developers who believe in local AI and privacy

</div>
