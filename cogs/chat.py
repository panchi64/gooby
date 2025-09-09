import discord
from discord.ext import commands
from discord import app_commands
import random
import re
import logging
import time
from typing import List, Dict, Optional, Tuple
from collections import deque
from utils.llm_client import LMStudioClient, get_fallback_response
from utils.context import ContextManager
from config import Config, GOOBY_SYSTEM_PROMPT, GOOBY_DECISION_PROMPT, load_personality, load_decision_prompt

logger = logging.getLogger(__name__)

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.context_manager = ContextManager()
        
        # Message history for reaction targeting and context
        self.message_history = deque(maxlen=10)
        
        # Rate limiting
        self.last_response_time = {}  # channel_id -> timestamp
        self.min_response_gap = 3  # seconds between responses per channel
        
        # Decision tracking
        self.decision_cache = {}  # message_id -> decision (for debugging)
    
    async def should_evaluate(self, message: discord.Message) -> bool:
        """Quick pre-filter before sending to LLM for decision"""
        # Always evaluate direct mentions
        if self.bot.user in message.mentions:
            return True
        
        # Always evaluate replies to bot
        if message.reference and message.reference.resolved:
            if message.reference.resolved.author == self.bot.user:
                return True
        
        # Check rate limiting per channel
        channel_id = message.channel.id
        if channel_id in self.last_response_time:
            time_since_last = time.time() - self.last_response_time[channel_id]
            if time_since_last < self.min_response_gap:
                return False  # Too soon since last response
        
        # Otherwise, let the LLM decide
        return True
    
    async def build_unified_context(self, message: discord.Message, mode: str = "response") -> str:
        """
        Unified context builder for both decision and response stages
        Uses database as primary source with in-memory fallback for consistency
        
        Args:
            message: The Discord message to build context for
            mode: "decision" or "response" - determines context configuration
        
        Returns:
            Formatted context string ready for LLM consumption
        """
        # Configuration based on mode
        config = {
            "decision": {
                "limit": 8, 
                "truncate": 120, 
                "include_new_msg": True,
                "context_ending": f"\n\nNew message from {message.author.display_name}: {message.content}\nShould Gooby respond? Reply with [SKIP] or [RESPOND]."
            },
            "response": {
                "limit": 15, 
                "truncate": None, 
                "include_new_msg": False,
                "context_ending": f"\n\nRespond to {message.author.display_name}: {message.content}"
            }
        }
        
        mode_config = config.get(mode, config["response"])
        
        try:
            # Primary: Try to get context from database (persistent across restarts)
            db_messages = await self.context_manager.get_recent_messages(
                str(message.channel.id), 
                mode_config["limit"]
            )
            
            if db_messages:
                context = self.context_manager.format_mixed_messages(
                    db_messages,
                    max_messages=mode_config["limit"],
                    max_content_length=mode_config["truncate"]
                )
            else:
                # Fallback: Use in-memory deque if database is empty/unavailable
                memory_messages = list(self.message_history)[-mode_config["limit"]:]
                context = self.context_manager.format_mixed_messages(
                    memory_messages,
                    max_messages=mode_config["limit"],
                    max_content_length=mode_config["truncate"]
                )
                
        except Exception as e:
            logger.error(f"Failed to get database context, using memory fallback: {e}")
            # Emergency fallback to in-memory deque
            memory_messages = list(self.message_history)[-mode_config["limit"]:]
            context = self.context_manager.format_mixed_messages(
                memory_messages,
                max_messages=mode_config["limit"],
                max_content_length=mode_config["truncate"]
            )
        
        # Add the appropriate ending based on mode
        context += mode_config["context_ending"]
        
        return context
    
    async def get_llm_decision(self, message: discord.Message) -> str:
        """First stage: Ask LLM if Gooby should respond"""
        try:
            context = await self.build_unified_context(message, mode="decision")
            messages = [{"role": "user", "content": context}]
            
            async with LMStudioClient() as llm:
                # TODO: Would be nice to use lower temperature for decisions
                decision = await llm.chat_completion(
                    messages,
                    GOOBY_DECISION_PROMPT
                )
                
                if decision:
                    # Cache the decision for debugging
                    self.decision_cache[message.id] = decision.strip()
                    return decision.strip()
                
            return "[SKIP]"  # Default to skip if LLM fails
            
        except Exception as e:
            logger.error(f"Failed to get LLM decision: {e}")
            # On error, only respond to direct mentions
            if self.bot.user in message.mentions:
                return "[RESPOND]"
            return "[SKIP]"
    
    
    def parse_reaction_command(self, response: str) -> Tuple[str, Optional[str], Optional[str]]:
        """Parse reaction commands from response
        
        Returns:
            (clean_response, target, emoji) where target is 'last', '2', etc.
        """
        # Look for [REACT:target:emoji] pattern at the end
        pattern = r'\[REACT:(\w+):(.+?)\]\s*$'
        match = re.search(pattern, response)
        
        if match:
            target = match.group(1)
            emoji = match.group(2).strip()
            clean_response = response[:match.start()].strip()
            return clean_response, target, emoji
        
        return response, None, None
    
    async def apply_reaction(self, target: str, emoji: str, channel):
        """Apply reaction to the specified message"""
        try:
            if target == 'none':
                return
            
            if target == 'last' and len(self.message_history) > 0:
                # React to the most recent user message
                await self.message_history[-1].add_reaction(emoji)
            elif target.isdigit():
                # React to a message N positions back
                position = int(target)
                if position <= len(self.message_history):
                    await self.message_history[-position].add_reaction(emoji)
        except Exception as e:
            logger.debug(f"Failed to apply reaction: {e}")
    
    async def generate_response(self, message: discord.Message) -> str:
        """Second stage: Generate Gooby's actual response"""
        try:
            context = await self.build_unified_context(message, mode="response")
            messages = [{"role": "user", "content": context}]
            
            # Generate response using Gooby's personality
            async with LMStudioClient() as llm:
                response = await llm.chat_completion(
                    messages,
                    GOOBY_SYSTEM_PROMPT
                    # Uses default temperature and max_tokens from Config
                )
                
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
        
        # Check channel restriction
        if Config.ALLOWED_CHANNELS and message.channel.id not in Config.ALLOWED_CHANNELS:
            return
        
        # Store message in context
        await self.context_manager.add_message(
            str(message.channel.id),
            str(message.author.id),
            message.author.display_name,
            message.content
        )
        
        # Store message in history for reaction targeting and context
        self.message_history.append(message)
        
        # Check if we should evaluate this message
        if not await self.should_evaluate(message):
            return  # Skip due to rate limiting or other filters
        
        try:
            # Stage 1: Get LLM decision
            decision = await self.get_llm_decision(message)
            
            # Check if LLM decided to respond
            if "[RESPOND]" in decision:
                # Stage 2: Generate and send response
                async with message.channel.typing():
                    response = await self.generate_response(message)
                    
                    # Parse reaction command if present
                    clean_response, reaction_target, reaction_emoji = self.parse_reaction_command(response)
                    
                    # Only send message if there's actual content
                    if clean_response and clean_response.strip():
                        sent_message = await message.channel.send(clean_response)
                        
                        # Record bot message response
                        await self.context_manager.add_message(
                            str(message.channel.id),
                            str(self.bot.user.id),
                            self.bot.user.display_name,
                            clean_response,
                            bot_responded=True
                        )
                    
                    # Apply reaction if specified
                    if reaction_target and reaction_emoji:
                        await self.apply_reaction(reaction_target, reaction_emoji, message.channel)
                        
                        # If we only reacted (no text), still record that the bot responded
                        if not (clean_response and clean_response.strip()):
                            await self.context_manager.add_message(
                                str(message.channel.id),
                                str(self.bot.user.id),
                                self.bot.user.display_name,
                                f"[Reacted with {reaction_emoji}]",
                                bot_responded=True
                            )
                    
                    # Update rate limiting
                    self.last_response_time[message.channel.id] = time.time()
                    
            # If [SKIP], do nothing
            
        except Exception as e:
            logger.error(f"Failed in message handling: {e}")
    
    
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
                
                # Parse and clean response
                clean_response, reaction_target, reaction_emoji = self.parse_reaction_command(response)
                
                # Only send message if there's actual content
                if clean_response and clean_response.strip():
                    await ctx.send(clean_response)
                
                # Apply reaction if specified
                if reaction_target and reaction_emoji:
                    await self.apply_reaction(reaction_target, reaction_emoji, ctx.channel)
                
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
            # Reload both personality and decision prompts
            global GOOBY_SYSTEM_PROMPT, GOOBY_DECISION_PROMPT
            new_personality = load_personality()
            new_decision = load_decision_prompt()
            
            # Update the global variables
            import config
            config.GOOBY_SYSTEM_PROMPT = new_personality
            config.GOOBY_DECISION_PROMPT = new_decision
            
            # Also update the local references
            GOOBY_SYSTEM_PROMPT = new_personality
            GOOBY_DECISION_PROMPT = new_decision
            
            await interaction.followup.send(
                "Personality and decision logic reloaded. Fresh perspective acquired."
            )
            logger.info("Personality and decision prompts reloaded via slash command")
            
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
            # Reload both personality and decision prompts
            global GOOBY_SYSTEM_PROMPT, GOOBY_DECISION_PROMPT
            new_personality = load_personality()
            new_decision = load_decision_prompt()
            
            # Update the global variables
            import config
            config.GOOBY_SYSTEM_PROMPT = new_personality
            config.GOOBY_DECISION_PROMPT = new_decision
            
            # Also update the local references
            GOOBY_SYSTEM_PROMPT = new_personality
            GOOBY_DECISION_PROMPT = new_decision
            
            await ctx.send("Personality and decision logic reloaded. Perspective shift complete.")
            logger.info("Personality and decision prompts reloaded via prefix command")
            
        except Exception as e:
            logger.error(f"Failed to reload personality: {e}")
            await ctx.send("Personality reload failed. How embarrassing.")

async def setup(bot):
    await bot.add_cog(ChatCog(bot))