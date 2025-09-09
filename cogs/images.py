import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
from typing import List, Optional
from utils.image_search import ImageSearcher

logger = logging.getLogger(__name__)

class ImagePaginator(discord.ui.View):
    """Paginated view for image search results"""
    
    def __init__(self, results: List[dict], query: str, author: discord.Member):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.results = results
        self.query = query
        self.author = author
        self.current_page = 0
        self.max_pages = len(results)
        
    def create_embed(self) -> discord.Embed:
        """Create embed for current page"""
        if not self.results:
            return discord.Embed(
                title="🔍 No Images Found",
                description=f"No images found for **{self.query}**. Shocking.",
                color=0xff6b6b
            )
        
        result = self.results[self.current_page]
        
        embed = discord.Embed(
            title="🖼️ Image Search Results",
            description=f"**Query:** {self.query}",
            color=0x7289da
        )
        
        embed.add_field(
            name="Title",
            value=result['title'][:100] or "Untitled",
            inline=False
        )
        
        embed.add_field(
            name="Source",
            value=result['source'][:50] or "Unknown",
            inline=True
        )
        
        embed.set_image(url=result['url'])
        embed.set_footer(
            text=f"Page {self.current_page + 1} of {self.max_pages} • Requested by {self.author.display_name}"
        )
        
        return embed
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the original user to use buttons"""
        return interaction.user == self.author
    
    @discord.ui.button(label='◀️ Previous', style=discord.ButtonStyle.blurple, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        
        # Update button states
        if self.current_page == 0:
            button.disabled = True
        
        self.next_button.disabled = False
        
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='Next ▶️', style=discord.ButtonStyle.blurple)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        
        # Update button states
        if self.current_page == self.max_pages - 1:
            button.disabled = True
            
        self.previous_button.disabled = False
        
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label='🗑️ Close', style=discord.ButtonStyle.red)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔍 Search Closed",
            description=f"Image search for **{self.query}** has been closed.",
            color=0x95a5a6
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()
    
    async def on_timeout(self):
        """Disable all buttons when view times out"""
        for item in self.children:
            item.disabled = True
        
        # Note: We can't edit the message here since we don't have the interaction

class ImagesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.search_cache = {}  # Simple cache to avoid repeated searches
        self.cache_ttl = 300  # 5 minutes cache
    
    def is_cache_valid(self, query: str) -> bool:
        """Check if cached result is still valid"""
        import time
        if query not in self.search_cache:
            return False
        
        cached_time = self.search_cache[query]['timestamp']
        return time.time() - cached_time < self.cache_ttl
    
    def cache_results(self, query: str, results: List[dict]):
        """Cache search results"""
        import time
        self.search_cache[query] = {
            'results': results,
            'timestamp': time.time()
        }
        
        # Clean old cache entries
        current_time = time.time()
        to_remove = []
        for key, value in self.search_cache.items():
            if current_time - value['timestamp'] > self.cache_ttl:
                to_remove.append(key)
        
        for key in to_remove:
            del self.search_cache[key]
    
    @app_commands.command(name="image", description="Search for images on the internet!")
    @app_commands.describe(query="What to search for")
    async def image_slash(self, interaction: discord.Interaction, query: str):
        """Search for images using DuckDuckGo"""
        await interaction.response.defer()
        
        try:
            # Clean query
            clean_query = query.strip()[:100]
            
            if not clean_query:
                await interaction.followup.send("You need to actually tell me what to search for, genius.")
                return
            
            # Check cache first
            if self.is_cache_valid(clean_query):
                results = self.search_cache[clean_query]['results']
                logger.info(f"Using cached results for: {clean_query}")
            else:
                # Perform search
                async with ImageSearcher() as searcher:
                    results = await searcher.search_with_fallback(clean_query, max_results=8)
                
                # Cache results
                self.cache_results(clean_query, results)
                logger.info(f"Found {len(results)} images for: {clean_query}")
            
            if not results:
                embed = discord.Embed(
                    title="🔍 No Images Found",
                    description=f"No images found for **{clean_query}**. Try different terms.",
                    color=0xff6b6b
                )
                embed.set_footer(text="Pro tip: Try words that actually exist.")
                await interaction.followup.send(embed=embed)
                return
            
            # Create paginated view
            view = ImagePaginator(results, clean_query, interaction.user)
            embed = view.create_embed()
            
            # Enable navigation buttons if multiple results
            if len(results) <= 1:
                view.next_button.disabled = True
                view.previous_button.disabled = True
            
            await interaction.followup.send(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Image search error: {e}")
            await interaction.followup.send(
                "Image search failed. Technology at its finest."
            )
    
    @commands.command(name="image", aliases=['img', 'pic'])
    async def image_prefix(self, ctx, *, query: str = None):
        """Prefix version of image search"""
        if not query:
            await ctx.send("What exactly am I supposed to search for, chief?")
            return
        
        try:
            async with ctx.typing():
                clean_query = query.strip()[:100]
                
                # Check cache
                if self.is_cache_valid(clean_query):
                    results = self.search_cache[clean_query]['results']
                else:
                    async with ImageSearcher() as searcher:
                        results = await searcher.search_with_fallback(clean_query, max_results=5)
                    self.cache_results(clean_query, results)
                
                if not results:
                    await ctx.send(f"No images found for **{clean_query}**. Tragic.")
                    return
                
                # For prefix commands, just show the first result
                result = results[0]
                
                embed = discord.Embed(
                    title="🖼️ Image Found!",
                    description=f"**Query:** {clean_query}",
                    color=0x7289da
                )
                
                embed.add_field(
                    name="Title",
                    value=result['title'][:100] or "Untitled",
                    inline=False
                )
                
                embed.set_image(url=result['url'])
                embed.set_footer(
                    text=f"Result 1 of {len(results)} • Use slash command for more options!"
                )
                
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Prefix image search error: {e}")
            await ctx.send("Image search broke. Wonderful.")
    
    @app_commands.command(name="randomimage", description="Get a random image!")
    async def random_image_slash(self, interaction: discord.Interaction):
        """Get a random interesting image"""
        await interaction.response.defer()
        
        try:
            import random
            
            # List of fun, safe random search terms
            random_terms = [
                "cute animals", "beautiful landscape", "space nebula", "flowers",
                "sunset", "mountains", "ocean waves", "forest", "rainbow",
                "cute cats", "puppies", "butterflies", "northern lights",
                "cherry blossom", "geometric patterns", "abstract art",
                "vintage cars", "architecture", "city skyline", "waterfalls"
            ]
            
            query = random.choice(random_terms)
            
            async with ImageSearcher() as searcher:
                results = await searcher.search_with_fallback(query, max_results=3)
            
            if not results:
                await interaction.followup.send("Random image generator failed. Great.")
                return
            
            result = random.choice(results)
            
            embed = discord.Embed(
                title="Random Image of Questionable Quality",
                description=f"**Random search:** {query}",
                color=0x7289da
            )
            
            embed.add_field(
                name="Title",
                value=result['title'][:100] or "Untitled",
                inline=False
            )
            
            embed.set_image(url=result['url'])
            embed.set_footer(text="Hope you weren't expecting something good.")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Random image error: {e}")
            await interaction.followup.send("My random image picker broke! 🎲")
    
    @commands.command(name="randomimage", aliases=['rimg', 'random'])
    async def random_image_prefix(self, ctx):
        """Prefix version of random image"""
        try:
            async with ctx.typing():
                import random
                
                random_terms = [
                    "cute animals", "beautiful landscape", "space", "flowers",
                    "sunset", "mountains", "ocean", "forest", "cats", "dogs"
                ]
                
                query = random.choice(random_terms)
                
                async with ImageSearcher() as searcher:
                    results = await searcher.search_with_fallback(query, max_results=3)
                
                if results:
                    result = random.choice(results)
                    embed = discord.Embed(
                        title="🎲 Random Image!",
                        color=0x7289da
                    )
                    embed.set_image(url=result['url'])
                    embed.set_footer(text=f"Random: {query}")
                    
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("Random search failed. Shocking.")
                    
        except Exception as e:
            logger.error(f"Random image prefix error: {e}")
            await ctx.send("Random image picker broke. Fantastic.")

async def setup(bot):
    await bot.add_cog(ImagesCog(bot))