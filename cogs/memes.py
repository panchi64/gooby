import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
from typing import List
from utils.image_maker import MemeGenerator

logger = logging.getLogger(__name__)

class MemesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.meme_generator = MemeGenerator()
        self.popular_templates = [
            "drake", "distracted_boyfriend", "woman_yelling_at_cat", 
            "two_buttons", "expanding_brain", "this_is_fine",
            "change_my_mind", "surprised_pikachu"
        ]
    
    async def template_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice[str]]:
        """Autocomplete for template names"""
        templates = self.meme_generator.list_templates()
        
        if not current:
            # Return popular templates first
            choices = self.popular_templates[:10]
        else:
            # Filter templates that match current input
            current_lower = current.lower()
            choices = [t for t in templates if current_lower in t.lower()][:10]
        
        return [
            app_commands.Choice(name=template.replace('_', ' ').title(), value=template)
            for template in choices
        ]
    
    @app_commands.command(name="meme", description="Create a goob-tastic meme!")
    @app_commands.describe(
        template="Choose a meme template",
        top_text="Text for the top of the meme",
        bottom_text="Text for the bottom of the meme (optional)"
    )
    @app_commands.autocomplete(template=template_autocomplete)
    async def meme_slash(
        self, 
        interaction: discord.Interaction, 
        template: str,
        top_text: str,
        bottom_text: str = ""
    ):
        """Create a meme with specified template and text"""
        await interaction.response.defer()
        
        try:
            # Generate the meme
            meme_data = self.meme_generator.create_meme(template, top_text, bottom_text)
            
            if meme_data:
                # Create Discord file
                file = discord.File(meme_data, filename=f"gooby_meme_{template}.png")
                
                # Create embed
                embed = discord.Embed(
                    title="Fresh Meme, Hot Off the Press",
                    color=0x7289da,
                    description=f"Template: **{template.replace('_', ' ').title()}**"
                )
                embed.set_author(name=f"Created by {interaction.user.display_name}")
                embed.set_image(url=f"attachment://gooby_meme_{template}.png")
                embed.set_footer(text="Made with questionable taste.")
                
                await interaction.followup.send(embed=embed, file=file)
                
                logger.info(f"Created meme '{template}' for {interaction.user.display_name}")
                
            else:
                await interaction.followup.send(
                    f"Can't find the '{template}' template, chief. "
                    f"Try `/templates` to see what's actually available."
                )
                
        except Exception as e:
            logger.error(f"Meme creation error: {e}")
            await interaction.followup.send(
                "Meme generation failed. Technology is amazing, isn't it?"
            )
    
    @app_commands.command(name="templates", description="See available meme templates")
    async def templates_slash(self, interaction: discord.Interaction):
        """List available meme templates"""
        await interaction.response.defer()
        
        try:
            templates = self.meme_generator.list_templates()
            
            if not templates:
                await interaction.followup.send(
                    "No templates found. Someone forgot to set things up properly."
                )
                return
            
            # Group templates for better display
            popular = [t for t in templates if t in self.popular_templates]
            others = [t for t in templates if t not in self.popular_templates]
            
            embed = discord.Embed(
                title="🎭 Available Meme Templates",
                color=0x7289da,
                description="Here are the templates that actually work."
            )
            
            if popular:
                popular_list = "\n".join([f"• **{t.replace('_', ' ').title()}**" for t in popular])
                embed.add_field(
                    name="🔥 Popular Templates",
                    value=popular_list,
                    inline=False
                )
            
            if others:
                others_list = "\n".join([f"• {t.replace('_', ' ').title()}" for t in others[:15]])
                if len(others) > 15:
                    others_list += f"\n• ... and {len(others) - 15} more!"
                
                embed.add_field(
                    name="📚 Other Templates",
                    value=others_list,
                    inline=False
                )
            
            embed.add_field(
                name="💡 Usage",
                value="Use `/meme [template] [top text] [bottom text]` to create your meme!",
                inline=False
            )
            
            embed.set_footer(text=f"Total templates: {len(templates)} | Use them wisely.")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Templates command error: {e}")
            await interaction.followup.send("Template loading failed. Shocking.")
    
    @commands.command(name="meme", aliases=['m'])
    async def meme_prefix(self, ctx, template: str = None, *, text: str = ""):
        """Prefix version of meme command"""
        if not template:
            await ctx.send("Usage: `!meme [template] [top text] | [bottom text]`\nUse `!templates` to see available templates!")
            return
        
        # Parse text - split by | for top/bottom
        if '|' in text:
            parts = text.split('|', 1)
            top_text = parts[0].strip()
            bottom_text = parts[1].strip()
        else:
            top_text = text.strip()
            bottom_text = ""
        
        if not top_text:
            await ctx.send("You need some text for your meme, goober! 🤔")
            return
        
        try:
            async with ctx.typing():
                meme_data = self.meme_generator.create_meme(template, top_text, bottom_text)
                
                if meme_data:
                    file = discord.File(meme_data, filename=f"gooby_meme_{template}.png")
                    await ctx.send(f"🫘 Here's your goob-tastic meme!", file=file)
                else:
                    await ctx.send(f"Couldn't find template '{template}', goober! Use `!templates` to see what's available!")
                    
        except Exception as e:
            logger.error(f"Prefix meme error: {e}")
            await ctx.send("My meme maker got all goobly! 🤖")
    
    @commands.command(name="templates", aliases=['t'])
    async def templates_prefix(self, ctx):
        """Prefix version of templates command"""
        try:
            templates = self.meme_generator.list_templates()
            
            if not templates:
                await ctx.send("No templates found, goober! 😱")
                return
            
            # Simple list format for prefix command
            template_list = ", ".join([t.replace('_', ' ') for t in templates[:20]])
            if len(templates) > 20:
                template_list += f"... and {len(templates) - 20} more!"
            
            embed = discord.Embed(
                title="🎭 Meme Templates",
                description=f"**Available templates:** {template_list}",
                color=0x7289da
            )
            embed.add_field(
                name="Usage",
                value="`!meme [template] [top text] | [bottom text]`",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Prefix templates error: {e}")
            await ctx.send("Couldn't load templates! 😅")
    
    @app_commands.command(name="randommeme", description="Create a meme with a random template!")
    @app_commands.describe(
        top_text="Text for the top",
        bottom_text="Text for the bottom (optional)"
    )
    async def random_meme_slash(
        self,
        interaction: discord.Interaction,
        top_text: str,
        bottom_text: str = ""
    ):
        """Create a meme with a random template"""
        await interaction.response.defer()
        
        try:
            import random
            templates = self.meme_generator.list_templates()
            
            if not templates:
                await interaction.followup.send("No templates available for random meme! 😱")
                return
            
            # Pick a random template
            template = random.choice(templates)
            
            meme_data = self.meme_generator.create_meme(template, top_text, bottom_text)
            
            if meme_data:
                file = discord.File(meme_data, filename=f"gooby_random_meme.png")
                
                embed = discord.Embed(
                    title="🎲 Random Goob Meme!",
                    color=0x7289da,
                    description=f"Randomly picked: **{template.replace('_', ' ').title()}**"
                )
                embed.set_author(name=f"Created by {interaction.user.display_name}")
                embed.set_image(url="attachment://gooby_random_meme.png")
                embed.set_footer(text="Feeling lucky, goober? 🍀")
                
                await interaction.followup.send(embed=embed, file=file)
            else:
                await interaction.followup.send("Random meme generation went goobly! 😅")
                
        except Exception as e:
            logger.error(f"Random meme error: {e}")
            await interaction.followup.send("My random meme picker broke! 🎲")

async def setup(bot):
    await bot.add_cog(MemesCog(bot))