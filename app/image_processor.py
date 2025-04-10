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

    def center_crop_to_ratio(self, img: Image.Image, target_ratio: float = 9/16) -> Image.Image:
        """
        Center crops the image to match the target ratio (default 9:16).
        Maintains the maximum possible area of the original image.
        """
        width, height = img.size
        current_ratio = width / height

        if current_ratio > target_ratio:
            # Image is too wide - crop width
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            right = left + new_width
            return img.crop((left, 0, right, height))
        elif current_ratio < target_ratio:
            # Image is too tall - crop height
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            bottom = top + new_height
            return img.crop((0, top, width, bottom))
        return img

    def process_image(self, image_path: str, text: str, output_filename: str = None):
        try:
            logger.info(f"Starting image processing with image: {image_path}")
            logger.info(f"Image exists: {os.path.exists(image_path)}")
            logger.info(f"Image size: {os.path.getsize(image_path)}")
            
            # Load image
            img = Image.open(image_path)
            logger.info(f"Original image format: {img.format}")
            logger.info(f"Original image size: {img.size}")
            logger.info(f"Original image mode: {img.mode}")
            
            # Convert to RGBA
            img = img.convert('RGBA')
            
            # Center crop to 9:16 ratio
            img = self.center_crop_to_ratio(img, target_ratio=9/16)
            logger.info(f"After cropping size: {img.size}")
            
            # Resize to target dimensions while maintaining aspect ratio
            img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
            logger.info(f"Final size: {img.size}")
            
            draw = ImageDraw.Draw(img)
            
            # Add logo
            logo = self.create_circular_logo(str(self.input_folder / 'logo.png'), size=96)
            img.paste(logo, (30, 60), logo)
            
            # Add header text
            header_font = ImageFont.truetype(self.font, 54)
            draw.text((150, 67), "MEDITNATION", font=header_font, fill='white')
            
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
            
            # Position in lower third
            text_y = int(1920 * (2/3))
            
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