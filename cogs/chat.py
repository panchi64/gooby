import discord
from discord.ext import commands
from discord import app_commands
import random
import re
import logging
from typing import List, Dict
from utils.llm_client import LMStudioClient, get_fallback_response
from utils.context import ContextManager
from config import Config, GOOBY_SYSTEM_PROMPT, load_personality

logger = logging.getLogger(__name__)

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.context_manager = ContextManager()
        self.goob_reactions = ['🫘', '👀', '🙄']
        
        # Keywords that increase response probability
        self.trigger_keywords = [
            'gooby', 'goob', 'help', 'what', 'how', 'why', 'funny', 'joke'
        ]
        
        # Random bean reactions
        self.last_bean_reaction = 0
    
    async def should_respond(self, message: discord.Message) -> tuple[bool, float]:
        """Determine if Gooby should respond to a message"""
        content_lower = message.content.lower()
        
        # Always respond to direct mentions or replies
        if self.bot.user in message.mentions or (
            message.reference and message.reference.resolved and 
            message.reference.resolved.author == self.bot.user
        ):
            return True, 1.0
        
        # High probability if name mentioned
        if 'gooby' in content_lower:
            return True, 0.8
        
        # Medium probability for trigger keywords
        keyword_count = sum(1 for keyword in self.trigger_keywords if keyword in content_lower)
        if keyword_count > 0:
            probability = min(0.6, keyword_count * 0.2)
            return random.random() < probability, probability
        
        # Check interaction history
        history_probability = await self.context_manager.should_respond_based_on_history(
            str(message.channel.id), str(message.author.id)
        )
        
        return random.random() < history_probability, history_probability
    
    def contains_question(self, content: str) -> bool:
        """Check if message contains a question"""
        return ('?' in content or 
                content.lower().startswith(('what', 'how', 'why', 'when', 'where', 'who', 'can', 'do', 'is', 'are')))
    
    async def generate_response(self, message: discord.Message) -> str:
        """Generate a response using LM Studio"""
        try:
            # Get conversation context
            recent_messages = await self.context_manager.get_recent_messages(
                str(message.channel.id), limit=15
            )
            
            # Format context for LLM
            context = self.context_manager.format_messages_for_llm(recent_messages, "Gooby")
            
            # Build the conversation
            messages = []
            
            # Add context if available
            if recent_messages:
                messages.append({
                    "role": "user", 
                    "content": f"Here's our recent conversation for context:\n{context}\n\nNow respond to: {message.content}"
                })
            else:
                messages.append({
                    "role": "user",
                    "content": message.content
                })
            
            # Generate response using LM Studio
            async with LMStudioClient() as llm:
                response = await llm.chat_completion(messages, GOOBY_SYSTEM_PROMPT)
                
                if response:
                    return response
                else:
                    return await get_fallback_response()
                    
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return await get_fallback_response()
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for messages and respond when appropriate"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Check server restriction
        if Config.ALLOWED_SERVER_ID and message.guild and message.guild.id != Config.ALLOWED_SERVER_ID:
            return
        
        # Store message in context
        await self.context_manager.add_message(
            str(message.channel.id),
            str(message.author.id),
            message.author.display_name,
            message.content
        )
        
        # Random bean reactions (very occasionally)
        if random.random() < 0.02:  # 2% chance
            try:
                await message.add_reaction('🫘')
            except:
                pass  # Ignore reaction failures
        
        # Check if should respond
        should_respond, probability = await self.should_respond(message)
        
        if should_respond:
            try:
                # Show typing indicator
                async with message.channel.typing():
                    # Generate response
                    response = await self.generate_response(message)
                    
                    # Send response
                    sent_message = await message.channel.send(response)
                    
                    # Record that bot responded
                    await self.context_manager.add_message(
                        str(message.channel.id),
                        str(self.bot.user.id),
                        self.bot.user.display_name,
                        response,
                        bot_responded=True
                    )
                    
                    # Occasionally add a reaction to our own message
                    if random.random() < 0.3:
                        reaction = random.choice(self.goob_reactions)
                        try:
                            await sent_message.add_reaction(reaction)
                        except:
                            pass
                    
            except Exception as e:
                logger.error(f"Failed to send response: {e}")
    
    @app_commands.command(name="chat", description="Have a direct chat with Gooby!")
    async def chat_slash(self, interaction: discord.Interaction, message: str):
        """Direct chat command"""
        await interaction.response.defer()
        
        try:
            # Create a mock message object for context
            class MockMessage:
                def __init__(self, content, author, channel):
                    self.content = content
                    self.author = author
                    self.channel = channel
                    self.mentions = []
                    self.reference = None
            
            mock_msg = MockMessage(message, interaction.user, interaction.channel)
            response = await self.generate_response(mock_msg)
            
            await interaction.followup.send(response)
            
            # Store both user message and bot response
            await self.context_manager.add_message(
                str(interaction.channel.id),
                str(interaction.user.id),
                interaction.user.display_name,
                message
            )
            
            await self.context_manager.add_message(
                str(interaction.channel.id),
                str(self.bot.user.id),
                self.bot.user.display_name,
                response,
                bot_responded=True
            )
            
        except Exception as e:
            logger.error(f"Chat slash command error: {e}")
            await interaction.followup.send("Yeah, that didn't work out so well. Try again, chief.")
    
    @app_commands.command(name="goobify", description="Transform text with goobly magic!")
    async def goobify_slash(self, interaction: discord.Interaction, text: str):
        """Transform text with goob puns"""
        await interaction.response.defer()
        
        try:
            # Ask LM Studio to goobify the text
            goobify_prompt = f"""Add some wit and maybe a subtle goob pun to this text. Keep it clever, not overwhelming.
            
            Original text: "{text}"
            
            Make it more interesting but don't go overboard."""
            
            messages = [{"role": "user", "content": goobify_prompt}]
            
            async with LMStudioClient() as llm:
                response = await llm.chat_completion(messages, GOOBY_SYSTEM_PROMPT)
                
                if response:
                    await interaction.followup.send(f"✨ Goobified: {response}")
                else:
                    # Fallback goobification
                    goobified = text.replace('good', 'goob').replace('cool', 'goobly cool')
                    if goobified == text:
                        goobified = f"That's goob-tastic! {text}"
                    await interaction.followup.send(f"✨ Goobified: {goobified}")
                    
        except Exception as e:
            logger.error(f"Goobify command error: {e}")
            await interaction.followup.send("Well, that was a spectacular failure. Maybe try again later.")
    
    @commands.command(name="goob")
    async def goob_prefix(self, ctx, *, message: str = None):
        """Prefix version of chat command"""
        if not message:
            await ctx.send("You gonna say something or just stand there, chief?")
            return
        
        try:
            async with ctx.typing():
                class MockMessage:
                    def __init__(self, content, author, channel):
                        self.content = content
                        self.author = author
                        self.channel = channel
                        self.mentions = []
                        self.reference = None
                
                mock_msg = MockMessage(message, ctx.author, ctx.channel)
                response = await self.generate_response(mock_msg)
                
                await ctx.send(response)
                
        except Exception as e:
            logger.error(f"Goob prefix command error: {e}")
            await ctx.send("Something went sideways there, pal. Give it another shot.")
    
    @app_commands.command(name="reload_personality", description="Reload Gooby's personality from file (Owner only)")
    async def reload_personality_slash(self, interaction: discord.Interaction):
        """Reload personality from gooby_personality.md file"""
        # Check if user is bot owner
        app_info = await self.bot.application_info()
        if interaction.user != app_info.owner:
            await interaction.response.send_message(
                "Sorry goober, only my creator can reload my personality! 🤖", 
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        try:
            # Reload the personality
            global GOOBY_SYSTEM_PROMPT
            new_personality = load_personality()
            
            # Update the global variable (this is a bit hacky but works)
            import config
            config.GOOBY_SYSTEM_PROMPT = new_personality
            
            # Also update the local reference
            global GOOBY_SYSTEM_PROMPT
            GOOBY_SYSTEM_PROMPT = new_personality
            
            await interaction.followup.send(
                "Personality reloaded. New me, same attitude."
            )
            logger.info("Personality reloaded via slash command")
            
        except Exception as e:
            logger.error(f"Failed to reload personality: {e}")
            await interaction.followup.send(
                "Well that didn't work. Personality reload failed, chief."
            )
    
    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_personality_prefix(self, ctx):
        """Reload Gooby's personality from file (Owner only)"""
        try:
            # Reload the personality
            global GOOBY_SYSTEM_PROMPT
            new_personality = load_personality()
            
            # Update the global variable
            import config
            config.GOOBY_SYSTEM_PROMPT = new_personality
            
            # Also update the local reference
            global GOOBY_SYSTEM_PROMPT
            GOOBY_SYSTEM_PROMPT = new_personality
            
            await ctx.send("Personality reloaded. Ready to be slightly less insufferable.")
            logger.info("Personality reloaded via prefix command")
            
        except Exception as e:
            logger.error(f"Failed to reload personality: {e}")
            await ctx.send("Personality reload failed. How embarrassing.")

async def setup(bot):
    await bot.add_cog(ChatCog(bot))