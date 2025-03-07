import os
import time
import logging
from typing import Tuple, Optional
from pathlib import Path
from textwrap import wrap
from PIL import Image, ImageDraw
import numpy as np
from moviepy.editor import VideoFileClip, ImageClip, TextClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
from .config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Add file handler for video processor specific logs
if not os.path.exists('logs'):
    os.makedirs('logs')
video_handler = logging.FileHandler('logs/video_processor.log')
video_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s: %(message)s [%(filename)s:%(lineno)d]'
))
video_handler.setLevel(logging.INFO)
logger.addHandler(video_handler)

class VideoProcessor:
    def __init__(
        self,
        input_folder: str,
        output_folder: str,
        font: str = None
    ):
        """Initialize the video processor with input/output paths."""
        self.input_folder = Path(input_folder).resolve()
        self.output_folder = Path(output_folder).resolve()

        # Set ImageMagick path explicitly
        from moviepy.config import change_settings
        change_settings({"IMAGEMAGICK_BINARY": Config.IMAGEMAGICK_BINARY})

        # Verify BebasNeue font exists
        font_path = self.input_folder / 'BebasNeue-Regular.ttf'
        if not font_path.exists():
            raise FileNotFoundError(f"Required font not found: {font_path}")
        self.font = str(font_path)

        self.output_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using font: {self.font}")

        # Add debug logging
        logger.info(f"Input folder: {self.input_folder}")
        logger.info(f"Font path: {self.input_folder / 'BebasNeue-Regular.ttf'}")
        logger.info(f"Font exists: {(self.input_folder / 'BebasNeue-Regular.ttf').exists()}")
        logger.info(f"Directory contents: {list(self.input_folder.glob('*'))}")

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

    def create_circular_logo(self, logo_path: str, size: int = 100) -> ImageClip:
        """Create a circular logo clip."""
        logo = Image.open(logo_path)

        # Create a circular mask
        mask = Image.new('L', (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, size, size), fill=255)

        # Resize logo to fill the circle
        logo = logo.resize((size, size), Image.Resampling.LANCZOS)

        # Apply mask
        output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        output.paste(logo, (0, 0))
        output.putalpha(mask)

        return ImageClip(np.array(output))

    def resize_and_crop_video(
        self,
        clip: VideoFileClip,
        target_size: Tuple[int, int]
    ) -> VideoFileClip:
        """Resize video to target size while maintaining aspect ratio and crop."""
        resize_factor = target_size[1] / clip.size[1]
        resized_width = int(clip.size[0] * resize_factor)

        resized = clip.resize(width=resized_width, height=target_size[1])

        x_center = resized.size[0] * 0.8
        x1 = int(x_center - target_size[0]/2)
        x1 = max(0, min(x1, resized.size[0] - target_size[0]))

        return resized.crop(x1=x1, y1=0, width=target_size[0], height=target_size[1])

    def cleanup_old_files(self, max_age_hours: int = 24, min_files_to_keep: int = 50):
        """Clean up old processed files while keeping a minimum number of recent files.
        
        Args:
            max_age_hours: Maximum age of files in hours before they're eligible for deletion
            min_files_to_keep: Minimum number of most recent files to keep regardless of age
        """
        try:
            logger.info(f"Starting cleanup of processed videos older than {max_age_hours} hours...")
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            # Get all mp4 files in the output directory with their creation times
            files = []
            for file in self.output_folder.glob('*.mp4'):
                creation_time = file.stat().st_mtime
                files.append((file, creation_time))
            
            # Sort files by creation time (newest first)
            files.sort(key=lambda x: x[1], reverse=True)
            
            # Keep minimum number of recent files
            files_to_check = files[min_files_to_keep:]
            
            deleted_count = 0
            for file_path, creation_time in files_to_check:
                if current_time - creation_time > max_age_seconds:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old file: {file_path.name}")
                    except Exception as e:
                        logger.error(f"Failed to delete file {file_path.name}: {str(e)}")
            
            logger.info(f"Cleanup completed. Deleted {deleted_count} files.")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    def process_video(
        self,
        video_filename: str = 'background.mp4',
        audio_filename: str = 'sound.mp3',
        logo_filename: str = 'logo.png',
        header_text: str = 'POSITIVITYHUB',
        body_text: str = None,
        author_text: str = None,
        output_filename: Optional[str] = None
    ):
        try:
            logger.info("Starting video processing...")
            
            # Handle paths
            if os.path.isabs(audio_filename):
                audio_path = Path(audio_filename)
            else:
                audio_path = self.input_folder / audio_filename
                
            video_path = self.input_folder / video_filename
            logo_path = self.input_folder / logo_filename

            # Load audio and apply fade out
            logger.info(f"Loading audio from: {audio_path}")
            audio = AudioFileClip(str(audio_path))
            audio = audio.audio_fadeout(3)
            logger.info("Audio loaded successfully")
            
            video_duration = audio.duration + 0.5
            fps = 24  # Reduced from 30

            logger.info(f"Loading video from: {video_path}")
            with VideoFileClip(str(video_path)) as video:
                logger.info("Video loaded successfully")
                # Process video with reduced resolution
                if video.duration < video_duration:
                    processed_video = self.resize_and_crop_video(video, (720, 1280))  # Half resolution
                    processed_video = processed_video.loop(duration=video_duration)
                else:
                    processed_video = self.resize_and_crop_video(video, (720, 1280))  # Half resolution
                    processed_video = processed_video.subclip(0, video_duration)

                logger.info("Creating overlay elements...")
                # Scale down text and logo sizes for smaller resolution
                logo = (self.create_circular_logo(str(logo_path), size=96)
                .set_position((30, 60))
                .set_duration(video_duration))

                header_name = (self.create_text_clip(
                    header_text,
                    54,  # Adjusted for 720p
                    color='white',
                    stroke_width=0
                ).set_position((150, 67))
                .set_duration(video_duration))

                subtitle = (self.create_text_clip(
                    "www.positivityhub.net",
                    22,  # Reduced from 43
                    color='#808080',
                    stroke_width=0
                ).set_position((150, 121))
                .set_duration(video_duration))

                # Create body text first
                body = (self.create_text_clip(
                    body_text,
                    68,
                    width=20,
                    color='white',
                    stroke_width=0
                ).set_position(('center', 'center'))
                .set_duration(video_duration))

                # Calculate author position relative to body text
                # Get body text height
                body_height = body.size[1]
                # Center point is at 640 (half of 1280)
                # Add half of body height to get to bottom of body text
                # Then add 50 pixels spacing
                author_y = 640 + (body_height/2) + 50

                author = (self.create_text_clip(
                    f"- {author_text}",
                    25,
                    color='#808080',
                    stroke_width=0
                ).set_position((75, author_y))
                .set_duration(video_duration))

                logger.info("Compositing final video...")
                final_video = CompositeVideoClip(
                    [processed_video, logo, header_name, subtitle, body, author],
                    size=(720, 1280)  # Half resolution
                ).set_duration(video_duration)

                final_video = final_video.set_audio(audio)
                final_video = final_video.fadeout(3)

                logger.info(f"Writing output to: {output_filename}")
                output_path = self.output_folder / output_filename
                final_video.write_videofile(
                    str(output_path),
                    codec='libx264',
                    audio_codec='aac',
                    audio_bitrate='192k',  # Better audio quality
                preset='medium',  # Better quality, reasonable speed
                    fps=fps,
                    threads=1,  # Single thread
                    ffmpeg_params=[
                        '-pix_fmt', 'yuv420p',
                        '-movflags', '+faststart',
                        '-crf', '26',  # Better quality (23-28 is good range)
                        '-tune', 'film'  # Better for general video content
                    ]
                )
                logger.info(f"Video processing completed: {output_filename}")
                # Clean up old files after successful processing
                self.cleanup_old_files()

        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            raise

    def generate_output_filename(self):
        timestamp = int(time.time())
        # Remove all special characters
        return f"processed{timestamp}video.mp4"