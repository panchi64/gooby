#!/usr/bin/env python3
"""
Simple script to create basic meme template placeholders
Run this once to set up initial templates
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_placeholder_template(name, width=500, height=400):
    """Create a simple placeholder template with text label"""
    try:
        img = Image.new('RGB', (width, height), color='lightgray')
        draw = ImageDraw.Draw(img)
        
        # Add text label to identify the template
        try:
            # Try to use a font
            font = ImageFont.load_default()
        except:
            font = None
        
        text = name.replace('_', ' ').title()
        if font:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(text) * 6
            text_height = 11
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill='black', font=font)
        
        filename = f"assets/templates/{name}.jpg"
        img.save(filename, 'JPEG')
        print(f"✓ Created placeholder template: {filename}")
        return True
    except Exception as e:
        print(f"✗ Failed to create placeholder {name}: {e}")
        return False

def main():
    # Create templates directory
    os.makedirs("assets/templates", exist_ok=True)
    
    print("Setting up meme templates...")
    
    # Create some basic placeholder templates
    # In a real setup, you'd want actual meme images, but these placeholders work for testing
    templates = [
        "drake",
        "distracted_boyfriend", 
        "woman_yelling_at_cat",
        "two_buttons",
        "expanding_brain",
        "this_is_fine",
        "change_my_mind",
        "surprised_pikachu"
    ]
    
    for template in templates:
        create_placeholder_template(template)
    
    print(f"\nCreated {len(templates)} template placeholders.")
    print("Note: These are placeholder templates. For better memes, replace with actual meme images!")
    print("You can find popular meme templates at sites like imgflip.com or knowyourmeme.com")

if __name__ == "__main__":
    main()