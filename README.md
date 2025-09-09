# 🫘 Gooby Discord Bot

A delightfully goofy Discord bot with personality inspired by Morph from Treasure Planet! Gooby loves making "goob" puns, calling everyone "goobers", and spreading goobly good vibes.

## ✨ Features

- **🤖 AI Chat**: Context-aware conversations powered by your local LM Studio
- **🎭 Meme Generator**: Create memes with popular templates and custom text
- **🖼️ Image Search**: Search the internet for images using DuckDuckGo
- **🫘 Gooby Personality**: Playful, punny, and full of goob vibes
- **🎯 Server Restricted**: Only responds in your specified Discord server
- **💾 Memory**: Remembers conversation context for better interactions

## 🚀 Quick Start

### Prerequisites

- Python 3.9+ 
- LM Studio running locally (with a model loaded)
- Discord Bot Token
- Your Discord Server ID

### Installation

1. **Clone and setup**:
   ```bash
   cd gooby
   python3 -m venv gooby-env
   source gooby-env/bin/activate  # On Windows: gooby-env\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Discord token and server ID
   ```

3. **Setup meme templates**:
   ```bash
   python create_templates.py
   ```

4. **Start LM Studio** and load a model (ensure it's running on localhost:1234)

5. **Run Gooby**:
   ```bash
   python bot.py
   ```

## ⚙️ Configuration

Edit `.env` file:

```env
# Required
DISCORD_TOKEN=your_bot_token_here
ALLOWED_SERVER_ID=your_server_id_here

# Optional (defaults shown)
BOT_PREFIX=!
LM_STUDIO_URL=http://localhost:1234/v1/chat/completions
RESPONSE_CHANCE=0.3
```

### Getting Your Discord Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section
4. Create bot and copy token
5. Invite bot to your server with necessary permissions

### Finding Your Server ID

1. Enable Developer Mode in Discord settings
2. Right-click your server name
3. Click "Copy Server ID"

## 🎮 Commands

### Slash Commands (Recommended)
- `/chat [message]` - Direct chat with Gooby
- `/goobify [text]` - Transform text with goob puns
- `/meme [template] [top_text] [bottom_text]` - Create memes
- `/templates` - List available meme templates
- `/image [query]` - Search for images
- `/randomimage` - Get a random image
- `/randommeme [text]` - Create meme with random template

### Prefix Commands (Alternative)
- `!goob [message]` - Chat with Gooby
- `!meme [template] [top text] | [bottom text]` - Create memes
- `!templates` - List templates
- `!image [query]` - Search images

### Auto-Responses
Gooby automatically responds when:
- Directly mentioned (@Gooby)
- Replied to
- Name "Gooby" is mentioned in conversation
- Certain keywords trigger responses
- Sometimes randomly (based on RESPONSE_CHANCE)

## 📁 Project Structure

```
gooby/
├── bot.py              # Main bot entry point
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── .env               # Your configuration (create from .env.example)
│
├── cogs/              # Bot features
│   ├── chat.py        # LLM chat & personality
│   ├── memes.py       # Meme generation
│   └── images.py      # Image search
│
├── utils/             # Helper functions
│   ├── llm_client.py  # LM Studio integration
│   ├── image_maker.py # Meme creation
│   ├── image_search.py# Image searching
│   └── context.py     # Conversation memory
│
├── assets/            # Bot assets
│   ├── fonts/         # Meme fonts
│   └── templates/     # Meme templates
│
└── data/              # Runtime data
    └── gooby.db       # Conversation history (SQLite)
```

## 🎭 Gooby's Personality

Gooby is inspired by Morph from Treasure Planet with these traits:
- **Playful & Mischievous**: Loves jokes and friendly teasing
- **Goob Obsessed**: Makes puns with "goob" and calls everyone "goobers"
- **Optimistic**: Always cheerful and positive
- **Helpful**: Wants to help but in a fun way
- **Expressive**: Uses emojis and reactions appropriately

### Example Interactions
- "Goob morning, goobers! ☀️"
- "That's absolutely goob-tastic!"
- "Don't be such a silly goober!"
- "Goob vibes only! ✨"

## 🔧 Customization

### Adding Meme Templates
1. Add image files to `assets/templates/`
2. Name them descriptively (e.g., `drake.jpg`, `distracted_boyfriend.png`)
3. Restart bot to load new templates

### 🎭 Customizing Gooby's Personality

**The Easy Way** - Edit the personality file:
1. Open `gooby_personality.md` in any text editor
2. Modify Gooby's behavior, speech patterns, and personality traits
3. Save the file
4. Either restart the bot OR use `/reload_personality` command (owner only)

**Examples of personality changes:**
```markdown
# Make Gooby more formal
## Personality Traits
- Professional but friendly
- Use "goob" puns sparingly  
- Address users as "esteemed goober"

# Make Gooby a pirate
## Speech Patterns
- Start with "Ahoy" or "Arr"
- Call users "ye goobly landlubbers"
- End with "Yo ho, goob vibes!"

# Make Gooby super excited
## Personality Traits
- EXTREMELY ENTHUSIASTIC!!!
- Everything is GOOB-TASTIC!!!
- Use lots of exclamation marks!!!
```

**Advanced Settings:**
- Modify response triggers in `cogs/chat.py`
- Adjust `RESPONSE_CHANCE` in `.env`

### LM Studio Settings
- Temperature: Controls creativity (0.1-1.0)
- Max Tokens: Response length limit
- Model: Choose based on your hardware

## 🐛 Troubleshooting

### Common Issues

**Bot doesn't respond**:
- Check LM Studio is running with a model loaded
- Verify Discord token and server ID are correct
- Check bot has message permissions in your server

**Memes don't work**:
- Run `python create_templates.py` to create templates
- Check `assets/templates/` has image files

**Image search fails**:
- Check internet connection
- DuckDuckGo search is sometimes rate-limited

**LM Studio connection fails**:
- Ensure LM Studio is running on localhost:1234
- Try loading a different model
- Check firewall settings

### Logs
Check console output for detailed error messages and debugging info.

## 🎨 Advanced Features

### Custom Commands
Add new commands by creating functions in the cogs with `@app_commands.command()` decorator.

### Database Queries
Use `ContextManager` class to query conversation history and user interactions.

### Image Processing
Extend `MemeGenerator` class for custom image manipulations.

## 📜 License

This project is open source. Feel free to modify and distribute!

## 🤝 Contributing

Found a bug or want to add features? Feel free to contribute!

---

Made with goobly love! 🫘✨

*Gooby says: "Thanks for using me, you wonderful goober!"*