import asyncio
import discord
from discord.ext import commands
import logging
from config import Config, GOOBY_SYSTEM_PROMPT

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GoobyBot(commands.Bot):
    def __init__(self):
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True
        intents.reactions = True
        
        super().__init__(
            command_prefix=Config.BOT_PREFIX,
            intents=intents,
            case_insensitive=True
        )
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Setting up Gooby...")
        
        # Load cogs
        await self.load_extension('cogs.chat')
        await self.load_extension('cogs.memes')
        await self.load_extension('cogs.images')
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f'{self.user} has awakened! Goob vibes activated! 🫘')
        logger.info(f'Connected to {len(self.guilds)} server(s)')
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for goobers to chat with! 🫘"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_join(self, guild):
        """Check if bot is allowed in this server"""
        if Config.ALLOWED_SERVER_ID and guild.id != Config.ALLOWED_SERVER_ID:
            logger.warning(f"Attempted to join unauthorized server: {guild.name} ({guild.id})")
            await guild.leave()
        else:
            logger.info(f"Joined authorized server: {guild.name} ({guild.id})")
    
    async def on_message(self, message):
        """Check server restriction before processing messages"""
        if message.author.bot:
            return
            
        if Config.ALLOWED_SERVER_ID and message.guild and message.guild.id != Config.ALLOWED_SERVER_ID:
            return
            
        await self.process_commands(message)
    
    async def on_command_error(self, ctx, error):
        """Handle command errors with goobly personality"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Oops, looks like you're missing something there, goober! Try using the help command 🤔")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Whoa there, speedy goober! Try again in {error.retry_after:.1f} seconds ⏰")
        else:
            logger.error(f"Command error: {error}")
            await ctx.send("Uh oh, something went goobly wrong! 😅")

async def main():
    """Main function to run the bot"""
    try:
        # Validate configuration
        Config.validate()
        
        # Create and run bot
        bot = GoobyBot()
        
        # Run the bot
        logger.info("Starting Gooby bot...")
        await bot.start(Config.DISCORD_TOKEN)
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Gooby is signing off... goob night! 🌙")

if __name__ == '__main__':
    asyncio.run(main())