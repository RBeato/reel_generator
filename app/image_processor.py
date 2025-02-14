import os
import time
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self, input_folder: str, output_folder: str):
        """Initialize the image processor with input/output paths."""
        self.input_folder = Path(input_folder).resolve()
        self.output_folder = Path(output_folder).resolve()
        
        # Verify BebasNeue font exists
        font_path = self.input_folder / 'BebasNeue-Regular.ttf'
        if not font_path.exists():
            raise FileNotFoundError(f"Required font not found: {font_path}")
        self.font = str(font_path)
        
        self.output_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using font: {self.font}")

    def create_circular_logo(self, logo_path: str, size: int = 100) -> Image:
        """Create a circular logo."""
        logo = Image.open(logo_path)
        mask = Image.new('L', (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, size, size), fill=255)
        logo = logo.resize((size, size), Image.Resampling.LANCZOS)
        output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        output.paste(logo, (0, 0))
        output.putalpha(mask)
        return output

    def process_image(self, image_path: str, text: str, output_filename: str = None):
        try:
            logger.info("Starting image processing...")
            
            # Load and resize image to 9:16 ratio
            img = Image.open(image_path)
            img = img.convert('RGBA')
            img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
            
            draw = ImageDraw.Draw(img)
            
            # Add logo
            logo = self.create_circular_logo(str(self.input_folder / 'logo.png'), size=96)
            img.paste(logo, (30, 60), logo)
            
            # Add header text
            header_font = ImageFont.truetype(self.font, 54)
            draw.text((150, 67), "POSITIVITYHUB", font=header_font, fill='white')
            
            # Add subtitle
            subtitle_font = ImageFont.truetype(self.font, 22)
            draw.text((150, 121), "www.positivityhub.net", font=subtitle_font, fill='#808080')
            
            # Add main text (centered horizontally, lower third vertically)
            main_font = ImageFont.truetype(self.font, 68)
            bbox = draw.textbbox((0, 0), text, font=main_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center horizontally
            text_x = (1080 - text_width) // 2
            
            # Position in lower third (approximately 2/3 down the screen)
            text_y = int(1920 * (2/3))  # This puts it at the 2/3 mark of the screen height
            
            draw.text((text_x, text_y), text, font=main_font, fill='white')
            
            # Generate output filename
            if not output_filename:
                timestamp = int(time.time())
                output_filename = f"processed{timestamp}image.png"
            
            output_path = self.output_folder / output_filename
            img.save(str(output_path), 'PNG')
            logger.info(f"Image processing completed: {output_filename}")
            
            return output_filename
            
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise 