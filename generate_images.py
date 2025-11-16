"""
Script to generate placeholder images for menu items
Run this script to create images for the default menu items
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Create images directory if it doesn't exist
images_dir = 'static/images'
os.makedirs(images_dir, exist_ok=True)

# Menu items with their colors
menu_items = [
    {'name': 'Idly', 'color': (255, 255, 240), 'text_color': (139, 69, 19)},
    {'name': 'Dosa', 'color': (255, 218, 185), 'text_color': (139, 69, 19)},
    {'name': 'Poori', 'color': (255, 215, 0), 'text_color': (139, 69, 19)},
    {'name': 'Vada', 'color': (222, 184, 135), 'text_color': (139, 69, 19)},
    {'name': 'Tea', 'color': (139, 69, 19), 'text_color': (255, 255, 255)},
    {'name': 'Coffee', 'color': (101, 67, 33), 'text_color': (255, 255, 255)},
    {'name': 'Milk', 'color': (255, 255, 255), 'text_color': (0, 0, 0)},
    {'name': 'Boost', 'color': (255, 140, 0), 'text_color': (255, 255, 255)},
]

def create_image(name, bg_color, text_color):
    # Create a 400x300 image
    width, height = 400, 300
    image = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(image)
    
    # Try to use a nice font, fallback to default if not available
    try:
        # Try to use a larger font
        font_size = 60
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
    
    # Get text bounding box
    bbox = draw.textbbox((0, 0), name, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center the text
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw text with shadow for better visibility
    shadow_offset = 2
    draw.text((x + shadow_offset, y + shadow_offset), name, fill=(0, 0, 0, 128), font=font)
    draw.text((x, y), name, fill=text_color, font=font)
    
    # Add a border
    draw.rectangle([0, 0, width-1, height-1], outline=(200, 200, 200), width=3)
    
    # Save the image
    filename = f"{name.lower()}.jpg"
    filepath = os.path.join(images_dir, filename)
    image.save(filepath, 'JPEG', quality=85)
    print(f"Created: {filepath}")

if __name__ == '__main__':
    print("Generating menu item images...")
    for item in menu_items:
        create_image(item['name'], item['color'], item['text_color'])
    print(f"\nAll images created in {images_dir}/")
    print("You can now run the Flask app and the images will be displayed!")

