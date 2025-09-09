from PIL import Image, ImageDraw, ImageFont
import io
import os
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class MemeGenerator:
    def __init__(self, assets_path: str = "assets"):
        self.assets_path = assets_path
        self.templates_path = os.path.join(assets_path, "templates")
        self.fonts_path = os.path.join(assets_path, "fonts")
        
        # Default font settings
        self.default_font_size = 40
        self.font_color = "white"
        self.outline_color = "black"
        self.outline_width = 2
    
    def get_font(self, size: int = None) -> ImageFont.ImageFont:
        """Get the meme font (Impact or fallback)"""
        font_size = size or self.default_font_size
        font_paths = [
            os.path.join(self.fonts_path, "impact.ttf"),
            os.path.join(self.fonts_path, "arial.ttf"),
            "arial.ttf",  # System font fallback
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, font_size)
            except Exception as e:
                logger.debug(f"Failed to load font {font_path}: {e}")
        
        # Ultimate fallback
        try:
            return ImageFont.load_default()
        except:
            logger.warning("Using basic font as all font loading failed")
            return ImageFont.load_default()
    
    def calculate_text_size(self, text: str, font: ImageFont.ImageFont, max_width: int) -> Tuple[int, int]:
        """Calculate optimal text size and wrapping"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    # Word is too long, break it
                    lines.append(word)
        
        if current_line:
            lines.append(" ".join(current_line))
        
        # Calculate total height
        line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
        total_height = len(lines) * line_height * 1.2  # 1.2 for line spacing
        
        return lines, int(total_height)
    
    def draw_text_with_outline(self, draw: ImageDraw.ImageDraw, text: str, 
                              position: Tuple[int, int], font: ImageFont.ImageFont):
        """Draw text with black outline"""
        x, y = position
        
        # Draw outline
        for dx in [-self.outline_width, 0, self.outline_width]:
            for dy in [-self.outline_width, 0, self.outline_width]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=self.outline_color)
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=self.font_color)
    
    def auto_size_font(self, text: str, max_width: int, max_height: int, 
                      min_size: int = 20, max_size: int = 60) -> ImageFont.ImageFont:
        """Automatically size font to fit text in given dimensions"""
        for size in range(max_size, min_size - 1, -2):
            font = self.get_font(size)
            lines, total_height = self.calculate_text_size(text, font, max_width)
            
            if total_height <= max_height and len(lines) <= 4:  # Max 4 lines
                return font
        
        return self.get_font(min_size)
    
    def create_meme(self, template_name: str, top_text: str = "", bottom_text: str = "") -> Optional[io.BytesIO]:
        """
        Create a meme with the specified template and text
        
        Args:
            template_name: Name of the template image
            top_text: Text for the top of the meme
            bottom_text: Text for the bottom of the meme
            
        Returns:
            BytesIO object containing the meme image, or None if failed
        """
        try:
            # Find template file
            template_path = None
            possible_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            
            for ext in possible_extensions:
                test_path = os.path.join(self.templates_path, f"{template_name}{ext}")
                if os.path.exists(test_path):
                    template_path = test_path
                    break
            
            if not template_path:
                logger.error(f"Template '{template_name}' not found")
                return None
            
            # Load template image
            with Image.open(template_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create a copy to work with
                meme_img = img.copy()
                draw = ImageDraw.Draw(meme_img)
                
                width, height = meme_img.size
                text_margin = width * 0.05  # 5% margin
                max_text_width = width - (2 * text_margin)
                max_text_height = height * 0.25  # Max 25% of image height per text
                
                # Draw top text
                if top_text.strip():
                    font = self.auto_size_font(top_text, max_text_width, max_text_height)
                    lines, total_height = self.calculate_text_size(top_text, font, max_text_width)
                    
                    # Calculate starting position (centered, top)
                    start_y = 20
                    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
                    
                    for i, line in enumerate(lines):
                        bbox = font.getbbox(line)
                        text_width = bbox[2] - bbox[0]
                        x = (width - text_width) // 2
                        y = start_y + (i * line_height * 1.2)
                        
                        self.draw_text_with_outline(draw, line, (x, int(y)), font)
                
                # Draw bottom text
                if bottom_text.strip():
                    font = self.auto_size_font(bottom_text, max_text_width, max_text_height)
                    lines, total_height = self.calculate_text_size(bottom_text, font, max_text_width)
                    
                    # Calculate starting position (centered, bottom)
                    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
                    start_y = height - total_height - 20
                    
                    for i, line in enumerate(lines):
                        bbox = font.getbbox(line)
                        text_width = bbox[2] - bbox[0]
                        x = (width - text_width) // 2
                        y = start_y + (i * line_height * 1.2)
                        
                        self.draw_text_with_outline(draw, line, (x, int(y)), font)
                
                # Save to BytesIO
                output = io.BytesIO()
                meme_img.save(output, format='PNG', quality=95)
                output.seek(0)
                
                logger.info(f"Created meme with template '{template_name}'")
                return output
                
        except Exception as e:
            logger.error(f"Failed to create meme: {e}")
            return None
    
    def list_templates(self) -> list:
        """List available meme templates"""
        templates = []
        
        if not os.path.exists(self.templates_path):
            return templates
        
        for filename in os.listdir(self.templates_path):
            name, ext = os.path.splitext(filename)
            if ext.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                templates.append(name)
        
        return sorted(templates)
    
    def get_template_info(self, template_name: str) -> Optional[dict]:
        """Get information about a template"""
        for ext in ['.jpg', '.jpeg', '.png', '.gif']:
            template_path = os.path.join(self.templates_path, f"{template_name}{ext}")
            if os.path.exists(template_path):
                try:
                    with Image.open(template_path) as img:
                        return {
                            'name': template_name,
                            'size': img.size,
                            'mode': img.mode,
                            'format': img.format,
                            'path': template_path
                        }
                except Exception as e:
                    logger.error(f"Failed to get template info: {e}")
        
        return None