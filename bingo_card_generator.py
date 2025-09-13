from PIL import Image, ImageDraw, ImageFont
import io
import math

def draw_hand_drawn_circle(draw, x, y, radius, color, width=5, variations=3):
    for i in range(variations):
        angle = (i / variations) * 2 * math.pi
        offset_x = math.cos(angle) * (radius * 0.1)
        offset_y = math.sin(angle) * (radius * 0.1)
        
        perturbed_radius = radius * (1 + (i % 2 - 0.5) * 0.2)
        
        draw.ellipse(
            (x - perturbed_radius + offset_x, y - perturbed_radius + offset_y, 
             x + perturbed_radius + offset_x, y + perturbed_radius + offset_y),
            outline=color, width=width
        )

def generate_card_image(card, marked, dimension):
    cell_size = 150
    margin = 50
    img_size = dimension * cell_size + 2 * margin
    
    img = Image.new("RGB", (img_size, img_size), "white")
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        font = ImageFont.load_default()

    for i in range(dimension):
        for j in range(dimension):
            x0 = margin + j * cell_size
            y0 = margin + i * cell_size
            x1 = x0 + cell_size
            y1 = y0 + cell_size
            
            draw.rectangle([x0, y0, x1, y1], outline="black")
            
            text = card[i][j]
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = x0 + (cell_size - text_width) / 2
            text_y = y0 + (cell_size - text_height) / 2
            draw.text((text_x, text_y), text, fill="black", font=font)
            
            if marked[i][j]:
                center_x = x0 + cell_size / 2
                center_y = y0 + cell_size / 2
                radius = cell_size / 3
                draw_hand_drawn_circle(draw, center_x, center_y, radius, "red")

    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)
    return buffer