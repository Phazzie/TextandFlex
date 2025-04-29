import tkinter as tk
from PIL import Image, ImageDraw, ImageFont
import os

# Create a simple icon for the application
def create_icon():
    # Create a new image with a white background
    img = Image.new('RGBA', (256, 256), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a rounded rectangle for the phone
    draw.rounded_rectangle([(48, 28), (208, 228)], fill=(52, 152, 219), radius=20)
    
    # Draw the screen area
    draw.rounded_rectangle([(58, 48), (198, 168)], fill=(236, 240, 241), radius=10)
    
    # Draw Excel icon
    draw.rectangle([(78, 78), (178, 138)], fill=(39, 174, 96))
    
    # Draw Excel lines
    for i in range(4):
        y = 88 + i * 10
        draw.line([(88, y), (168, y)], fill=(255, 255, 255), width=2)
    
    # Draw a conversion arrow
    arrow_points = [
        (128, 178),  # Tip
        (108, 158),  # Left wing
        (118, 158),  # Left inner
        (118, 138),  # Top
        (138, 138),  # Top right
        (138, 158),  # Right inner
        (148, 158),  # Right wing
    ]
    draw.polygon(arrow_points, fill=(231, 76, 60))
    
    # Save the image as ICO
    img.save('icon.ico', format='ICO')
    
    print("Icon created successfully!")

if __name__ == "__main__":
    create_icon()
