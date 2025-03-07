import os
import logging
from typing import Tuple, Optional
from pathlib import Path
from textwrap import wrap
from PIL import Image

# Import MoviePy configuration
import app.moviepy_conf as moviepy_conf

# # Open terminal in Cursor IDE and run:
# python -m venv venv

# # Activate virtual environment
# # On Windows:
# .\venv\Scripts\activate
# # On macOS/Linux:
# source venv/bin/activate


from moviepy.editor import (
    VideoFileClip, 
    ImageClip, 
    TextClip, 
    CompositeVideoClip,
    AudioFileClip
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(
        self,
        input_folder: str,
        output_folder: str,
        font: str = None
    ):
        """Initialize the video processor with input/output paths and settings."""
        self.input_folder = Path(input_folder).resolve()
        self.output_folder = Path(output_folder).resolve()
        
        # Use BebasNeue font if available, otherwise fallback to Arial
        font_path = self.input_folder / 'BebasNeue-Regular.ttf'  # Changed to BebasNeue
        self.font = str(font_path) if font_path.exists() else 'Arial'
        
        # Verify input folder exists
        if not self.input_folder.exists():
            raise FileNotFoundError(f"Input folder not found: {self.input_folder}")
        
        # Create output folder if it doesn't exist
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Input folder: {self.input_folder}")
        logger.info(f"Output folder: {self.output_folder}")
        logger.info(f"Using font: {self.font}")
        
    def read_text_file(self, filename: str) -> Optional[str]:
        """Read content from a text file."""
        try:
            file_path = self.input_folder / filename
            logger.info(f"Attempting to read file: {file_path}")
            
            if not file_path.exists():
                logger.error(f"File does not exist: {file_path}")
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                logger.info(f"Successfully read file: {filename}")
                return content
        except Exception as e:
            logger.error(f"Error reading {filename}: {str(e)}")
            return None

    def create_text_clip(
        self,
        text: str,
        font_size: int,
        color: str = 'white',
        stroke_color: str = 'black',
        stroke_width: int = 2,
        width: Optional[int] = None
    ) -> TextClip:
        """Create a text clip with the specified styling."""
        if width:
            # Wrap text to specified width (in characters)
            text = '\n'.join(wrap(text, width=width))
            
        return TextClip(
            text,
            fontsize=font_size,
            color=color,
            font=self.font,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            method='label'
        )

    def resize_and_crop_video(
        self,
        clip: VideoFileClip,
        target_size: Tuple[int, int]
    ) -> VideoFileClip:
        """Resize video to target size while maintaining aspect ratio and crop."""
        # Calculate resize factor to fill the height
        resize_factor = target_size[1] / clip.size[1]
        resized_width = int(clip.size[0] * resize_factor)
        
        # Resize the clip (removed resample parameter)
        resized = clip.resize(
            width=resized_width,
            height=target_size[1]
        )
        
        # Calculate crop position (crop more from the left to keep right portion)
        x_center = resized.size[0] * 0.6  # Adjust this value to control crop position
        x1 = int(x_center - target_size[0]/2)
        x1 = max(0, min(x1, resized.size[0] - target_size[0]))
        
        # Crop the clip
        return resized.crop(
            x1=x1,
            y1=0,
            width=target_size[0],
            height=target_size[1]
        )

    def process_video(
        self,
        video_filename: str = 'background.mp4',
        audio_filename: str = 'sound.mp3',
        logo_filename: str = 'logo.png',
        output_filename: Optional[str] = None
    ):
        """Process the video with all required modifications."""
        try:
            # Check if all required files exist
            required_files = [
                ('background.mp4', video_filename),
                ('logo.png', logo_filename),
                ('header_text.TXT', 'header_text.TXT'),
                ('body.TXT', 'body.TXT'),
                ('author.txt', 'author.txt')
            ]
            
            for desc, filename in required_files:
                file_path = self.input_folder / filename
                if not file_path.exists():
                    raise FileNotFoundError(f"Required file {desc} not found at: {file_path}")

            # Read text content
            header_text = self.read_text_file('header_text.TXT')
            body_text = self.read_text_file('body.TXT')
            author_text = self.read_text_file('author.txt')
            
            if not all([header_text, body_text, author_text]):
                raise ValueError("Failed to read required text files")

            # Load video and audio
            video_path = self.input_folder / video_filename
            audio_path = self.input_folder / audio_filename
            logo_path = self.input_folder / logo_filename
            
            logger.info(f"Processing video: {video_filename}")
            
            with VideoFileClip(str(video_path)) as video:
                # Get the video duration
                video_duration = video.duration
                
                # Resize and crop video
                processed_video = self.resize_and_crop_video(video, (1080, 1920))
                
                # Create logo clip
                logo = (ImageClip(str(logo_path))
                       .resize(width=200)
                       .set_position((20, 20))
                       .set_duration(video_duration))
                
                # Create text clips with updated sizes and positions
                header = (self.create_text_clip(
                    header_text,
                    80,
                    stroke_width=3
                ).set_position(('center', 100))
                 .set_duration(video_duration))
                
                # Updated body text: bigger font and centered
                body = (self.create_text_clip(
                    body_text, 
                    72,  # Increased font size from 64 to 72
                    width=25,  # Adjusted for better text wrapping
                    color='white',
                    stroke_width=3
                ).set_position(('center', 'center'))  # Center both horizontally and vertically
                 .set_duration(video_duration))
                
                author = (self.create_text_clip(
                    author_text,
                    48,
                    stroke_width=2
                ).set_position(('center', 1860))  # Centered horizontally
                 .set_duration(video_duration))
                
                # Combine all clips
                final_video = CompositeVideoClip(
                    [processed_video, logo, header, body, author],
                    size=(1080, 1920)
                ).set_duration(video_duration)
                
                # Add audio if specified
                if audio_path.exists():
                    audio = AudioFileClip(str(audio_path))
                    final_video = final_video.set_audio(audio)
                
                # Generate output filename if not provided
                if not output_filename:
                    output_filename = f"processed_{video_filename}"
                
                output_path = self.output_folder / output_filename
                
                # Write final video
                final_video.write_videofile(
                    str(output_path),
                    codec='libx264',
                    audio_codec='aac',
                    audio_bitrate='128k',
                    preset='medium',
                    fps=30,
                    threads=4,
                    ffmpeg_params=[
                        '-pix_fmt', 'yuv420p',
                        '-movflags', '+faststart'
                    ]
                )
                
                logger.info(f"Video processing completed: {output_filename}")
                
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            raise

def main():
    """Main function to demonstrate usage."""
    try:
        processor = VideoProcessor(
            input_folder=r'C:\Users\rbsou\Desktop\ffmpeg_test\input',
            output_folder=r'C:\Users\rbsou\Desktop\ffmpeg_test\output'
        )
        
        processor.process_video(
            video_filename='background.mp4',
            audio_filename='sound.mp3',
            logo_filename='logo.png',
            output_filename='final_video.mp4'
        )
    except Exception as e:
        logger.error(f"Main execution error: {str(e)}")
        raise

if __name__ == "__main__":
    main()