import discord
from discord.ext import commands
from discord import app_commands
import random
import re
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

class DiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Dice expression patterns
        self.dice_pattern = re.compile(r'(\d+)d(\d+)', re.IGNORECASE)
        self.modifier_pattern = re.compile(r'([+-]\s*\d+)')
        self.full_expression_pattern = re.compile(r'^[\dd\s+\-0-9]+$', re.IGNORECASE)
        
        # Safety limits
        self.max_dice = 100
        self.max_sides = 1000
        self.max_expression_length = 200
        
    def parse_dice_expression(self, expression: str) -> Tuple[bool, List[Tuple[int, int]], List[int], str]:
        """
        Parse a dice expression like "3d20 + 2d6 - 5"
        
        Returns:
            - success: bool - whether parsing succeeded
            - dice_groups: List[Tuple[int, int]] - [(count, sides), ...]
            - modifiers: List[int] - [+5, -2, ...]
            - error_message: str - error description if failed
        """
        
        if not expression or len(expression) > self.max_expression_length:
            return False, [], [], "Expression too long or empty"
        
        # Clean the expression
        expression = expression.strip().replace(' ', '')
        
        # Validate characters
        if not self.full_expression_pattern.match(expression):
            return False, [], [], "Invalid characters in expression. Use format like '3d20 + 2d6 - 5'"
        
        # Find all dice groups (XdY)
        dice_matches = self.dice_pattern.findall(expression)
        dice_groups = []
        
        for count_str, sides_str in dice_matches:
            count = int(count_str)
            sides = int(sides_str)
            
            # Validate limits
            if count > self.max_dice:
                return False, [], [], f"Too many dice in one group (max {self.max_dice})"
            if sides > self.max_sides:
                return False, [], [], f"Too many sides on die (max {self.max_sides})"
            if count < 1 or sides < 1:
                return False, [], [], "Dice count and sides must be positive"
                
            dice_groups.append((count, sides))
        
        # Find all modifiers (+5, -3, etc)
        # First remove dice expressions to avoid false matches
        expression_without_dice = self.dice_pattern.sub('', expression)
        modifier_matches = self.modifier_pattern.findall(expression_without_dice)
        
        modifiers = []
        for mod_str in modifier_matches:
            try:
                # Remove spaces and convert
                mod_value = int(mod_str.replace(' ', ''))
                modifiers.append(mod_value)
            except ValueError:
                return False, [], [], f"Invalid modifier: {mod_str}"
        
        if not dice_groups:
            return False, [], [], "No dice found in expression. Use format like '3d20' or '1d4 + 2d6'"
        
        return True, dice_groups, modifiers, ""
    
    def roll_dice_group(self, count: int, sides: int) -> Tuple[List[int], int]:
        """
        Roll a group of dice and return individual results and sum
        
        Returns:
            - rolls: List[int] - individual die results
            - total: int - sum of all rolls
        """
        rolls = [random.randint(1, sides) for _ in range(count)]
        return rolls, sum(rolls)
    
    def format_dice_result(self, expression: str, dice_groups: List[Tuple[int, int]], 
                          dice_results: List[Tuple[List[int], int]], 
                          modifiers: List[int], total: int) -> discord.Embed:
        """
        Format the dice roll results into a clean, readable Discord embed
        """
        
        embed = discord.Embed(
            title="🎲 Dice Roll",
            color=0x7289da,
            description=f"`{expression}`"
        )
        
        # Main result - most prominent
        embed.add_field(
            name="🎯 **Result**",
            value=f"## {total}",
            inline=False
        )
        
        # Show breakdown only if there are multiple parts
        if len(dice_groups) > 1 or modifiers:
            calculation_parts = []
            
            for (count, sides), (rolls, group_total) in zip(dice_groups, dice_results):
                if count == 1:
                    calculation_parts.append(str(group_total))
                else:
                    calculation_parts.append(f"({'+'.join(map(str, rolls))})")
            
            # Add modifiers
            for modifier in modifiers:
                if modifier >= 0:
                    calculation_parts.append(f"+{modifier}")
                else:
                    calculation_parts.append(str(modifier))
            
            calculation = " ".join(calculation_parts) + f" = **{total}**"
            embed.add_field(
                name="📊 Breakdown",
                value=calculation,
                inline=False
            )
        
        # Show individual dice only when helpful (multiple dice, not too many)
        if len(dice_groups) == 1 and 2 <= dice_groups[0][0] <= 8:
            count, sides = dice_groups[0]
            rolls, _ = dice_results[0]
            
            # Format rolls nicely
            roll_display = []
            for roll in rolls:
                if roll == sides:
                    roll_display.append(f"**{roll}** ⭐")  # Max roll
                elif roll == 1 and sides > 1:
                    roll_display.append(f"**{roll}** 💔")  # Min roll
                else:
                    roll_display.append(str(roll))
            
            embed.add_field(
                name=f"🎲 {count}d{sides} Rolls",
                value=", ".join(roll_display),
                inline=True
            )
        
        # Simple Gooby personality
        if total == 1:
            footer_text = "Ooof, that's rough goober! 🍀"
        elif total >= 50:
            footer_text = "Holy goob! Big numbers! 🎉"
        elif total <= 5:
            footer_text = "Not exactly goob-tier, but hey! 📉"
        else:
            footer_text = "Another goob-solutely random roll! 🎲"
            
        embed.set_footer(text=footer_text)
        
        return embed
    
    @app_commands.command(name="roll", description="Roll dice with expressions like '3d20' or '1d4 + 2d6 + 5'")
    @app_commands.describe(expression="Dice expression (e.g., '3d20', '1d4 + 2d6', '2d10 + 5')")
    async def roll_slash(self, interaction: discord.Interaction, expression: str):
        """Slash command for rolling dice"""
        await interaction.response.defer()
        
        try:
            # Parse the expression
            success, dice_groups, modifiers, error_msg = self.parse_dice_expression(expression)
            
            if not success:
                embed = discord.Embed(
                    title="🎲 Dice Roll Error",
                    color=0xff0000,
                    description=f"**Oops!** {error_msg}"
                )
                embed.add_field(
                    name="💡 Examples",
                    value="`3d20` • `1d4 + 2d6` • `2d10 + 5` • `1d20 - 2`",
                    inline=False
                )
                embed.set_footer(text="Even goobers need proper dice notation! 🤖")
                await interaction.followup.send(embed=embed)
                return
            
            # Roll all dice groups
            dice_results = []
            total = 0
            
            for count, sides in dice_groups:
                rolls, group_total = self.roll_dice_group(count, sides)
                dice_results.append((rolls, group_total))
                total += group_total
            
            # Add modifiers
            for modifier in modifiers:
                total += modifier
            
            # Create result embed
            result_embed = self.format_dice_result(expression, dice_groups, dice_results, modifiers, total)
            result_embed.set_author(name=f"{interaction.user.display_name}'s Roll")
            
            await interaction.followup.send(embed=result_embed)
            
            logger.info(f"Dice roll by {interaction.user.display_name}: {expression} = {total}")
            
        except Exception as e:
            logger.error(f"Dice roll error: {e}")
            await interaction.followup.send(
                "My dice got all goobly! The roll exploded somehow. 🎲💥"
            )
    
    @commands.command(name="roll", aliases=['dice', 'r'])
    async def roll_prefix(self, ctx, *, expression: str = None):
        """Prefix command for rolling dice"""
        if not expression:
            embed = discord.Embed(
                title="🎲 Dice Rolling Help",
                color=0x7289da,
                description="Roll some dice, goober! Here's how:"
            )
            embed.add_field(
                name="📖 Usage",
                value=f"`{ctx.prefix}roll <expression>`",
                inline=False
            )
            embed.add_field(
                name="💡 Examples",
                value=(
                    f"`{ctx.prefix}roll 3d20` - Roll 3 twenty-sided dice\n"
                    f"`{ctx.prefix}roll 1d4 + 2d6` - Roll 1d4 and 2d6, add them\n"
                    f"`{ctx.prefix}roll 2d10 + 5` - Roll 2d10 and add 5\n"
                    f"`{ctx.prefix}roll 1d20 - 2 + 1d4` - Complex expression"
                ),
                inline=False
            )
            embed.set_footer(text="Time to get goobly with some randomness! 🎯")
            await ctx.send(embed=embed)
            return
        
        try:
            # Parse the expression
            success, dice_groups, modifiers, error_msg = self.parse_dice_expression(expression)
            
            if not success:
                embed = discord.Embed(
                    title="🎲 Dice Roll Error",
                    color=0xff0000,
                    description=f"**Oops!** {error_msg}"
                )
                embed.add_field(
                    name="💡 Examples",
                    value="`3d20` • `1d4 + 2d6` • `2d10 + 5` • `1d20 - 2`",
                    inline=False
                )
                embed.set_footer(text="Even goobers need proper dice notation! 🤖")
                await ctx.send(embed=embed)
                return
            
            # Roll all dice groups
            dice_results = []
            total = 0
            
            for count, sides in dice_groups:
                rolls, group_total = self.roll_dice_group(count, sides)
                dice_results.append((rolls, group_total))
                total += group_total
            
            # Add modifiers
            for modifier in modifiers:
                total += modifier
            
            # Create result embed
            result_embed = self.format_dice_result(expression, dice_groups, dice_results, modifiers, total)
            result_embed.set_author(name=f"{ctx.author.display_name}'s Roll")
            
            await ctx.send(embed=result_embed)
            
            logger.info(f"Dice roll by {ctx.author.display_name}: {expression} = {total}")
            
        except Exception as e:
            logger.error(f"Dice roll error: {e}")
            await ctx.send(
                "My dice got all goobly! The roll exploded somehow. 🎲💥"
            )

async def setup(bot):
    await bot.add_cog(DiceCog(bot))