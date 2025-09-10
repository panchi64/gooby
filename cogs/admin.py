import discord
from discord.ext import commands
from discord import app_commands
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AdminCog(commands.Cog):
    """Administrative commands for Gooby bot management"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name="wipememory",
        description="Completely wipe Gooby's memory and conversation history (Admin only)"
    )
    @app_commands.default_permissions(administrator=True)
    async def wipe_memory(self, interaction: discord.Interaction):
        """Wipe all of Gooby's memory - database and in-memory cache"""
        
        # Additional permission check for safety
        if not interaction.user.guild_permissions.administrator:
            # Log the user's roles for debugging
            user_roles = [role.name for role in interaction.user.roles if role.name != "@everyone"]
            logger.warning(f"User {interaction.user} ({interaction.user.id}) attempted wipememory without admin. Roles: {user_roles}")
            
            embed = discord.Embed(
                title="🚫 Permission Denied",
                color=discord.Color.red(),
                description="nice try, but you need Administrator permissions to scramble goob's brain!"
            )
            embed.add_field(
                name="Your Roles",
                value=", ".join(user_roles) if user_roles else "No roles",
                inline=False
            )
            embed.set_footer(text="goob's memories are MINE, not yours!")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Track what we're clearing
            messages_deleted = 0
            memory_cleared = False
            errors = []
            
            # Clear database through context manager
            try:
                # Get the context manager from chat cog
                chat_cog = self.bot.get_cog('ChatCog')
                if chat_cog and hasattr(chat_cog, 'context_manager'):
                    messages_deleted = await chat_cog.context_manager.wipe_all_messages()
                else:
                    errors.append("Could not access context manager")
            except Exception as e:
                logger.error(f"Failed to wipe database: {e}")
                errors.append(f"Database wipe failed: {str(e)}")
            
            # Clear in-memory state from chat cog
            try:
                chat_cog = self.bot.get_cog('ChatCog')
                if chat_cog:
                    await chat_cog.clear_memory()
                    memory_cleared = True
                else:
                    errors.append("Chat cog not found")
            except Exception as e:
                logger.error(f"Failed to clear chat memory: {e}")
                errors.append(f"Memory clear failed: {str(e)}")
            
            # Create response embed
            if errors:
                embed = discord.Embed(
                    title="⚠️ Partial Memory Wipe",
                    color=discord.Color.orange(),
                    description="goob's brain got partially scrambled, but some bits stuck around..."
                )
                embed.add_field(
                    name="❌ Errors",
                    value="\n".join(errors),
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title="🧹 Memory Wiped Successfully",
                    color=discord.Color.green(),
                    description="*goblin noises* goob's brain just got factory reset! fresh start, who dis?"
                )
            
            # Add details
            embed.add_field(
                name="📊 Database",
                value=f"Deleted {messages_deleted} messages" if messages_deleted > 0 else "No messages to delete",
                inline=True
            )
            embed.add_field(
                name="🧠 Memory Cache",
                value="✅ Cleared" if memory_cleared else "❌ Failed",
                inline=True
            )
            embed.add_field(
                name="👤 Executed By",
                value=interaction.user.mention,
                inline=True
            )
            
            embed.set_footer(text="goob feels... empty? but also sparkly new!")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Log the action with user's roles
            user_roles = [role.name for role in interaction.user.roles if role.name != "@everyone"]
            logger.info(f"Memory wipe executed by {interaction.user} ({interaction.user.id}) with roles: {user_roles}")
            
            # Send a public message in the channel if successful and no errors
            if not errors:
                public_embed = discord.Embed(
                    description="*confused goblin noises* ...wait, who are you people? goob just woke up!",
                    color=discord.Color.blue()
                )
                await interaction.channel.send(embed=public_embed)
                
        except Exception as e:
            logger.error(f"Critical error in memory wipe: {e}")
            error_embed = discord.Embed(
                title="💥 Critical Error",
                color=discord.Color.red(),
                description=f"goob's brain wipe exploded: {str(e)}"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)
    
    @wipe_memory.error
    async def wipe_memory_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle permission errors for the wipe memory command"""
        
        # Log detailed error information
        user_roles = [role.name for role in interaction.user.roles if role.name != "@everyone"]
        logger.error(f"wipememory command error for user {interaction.user} with roles {user_roles}: {error}")
        
        embed = discord.Embed(
            title="🚫 Command Error",
            color=discord.Color.red(),
            description="Something went wrong! Make sure you have Administrator permissions."
        )
        embed.add_field(
            name="Your Roles",
            value=", ".join(user_roles) if user_roles else "No roles",
            inline=False
        )
        embed.set_footer(text="Try asking a server admin for help!")
        
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))