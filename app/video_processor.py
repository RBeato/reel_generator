import os
import logging
import time
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

    def cleanup_old_files(self, max_age_hours: int = 24, min_files_to_keep: int = 10):
        """Clean up old processed videos while keeping a minimum number of recent files."""
        try:
            logger.info(f"Starting cleanup of processed videos older than {max_age_hours} hours...")
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            files = []
            for file in self.output_folder.glob('*.mp4'):
                creation_time = file.stat().st_mtime
                files.append((file, creation_time))
            
            files.sort(key=lambda x: x[1], reverse=True)
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
        header_text: str = None,
        body_text: str = None,
        author_text: str = None,
        output_filename: Optional[str] = None
    ):
        try:
            logger.info("Starting video processing...")
            
            if os.path.isabs(audio_filename):
                audio_path = Path(audio_filename)
            else:
                audio_path = self.input_folder / audio_filename
                
            video_path = self.input_folder / video_filename
            logo_path = self.input_folder / logo_filename

            logger.info(f"Loading audio from: {audio_path}")
            audio = AudioFileClip(str(audio_path))
            audio = audio.audio_fadeout(3)
            logger.info("Audio loaded successfully")
            
            video_duration = audio.duration + 0.5
            fps = 30  # Restored to 30 fps

            logger.info(f"Loading video from: {video_path}")
            with VideoFileClip(str(video_path)) as video:
                logger.info("Video loaded successfully")
                if video.duration < video_duration:
                    processed_video = self.resize_and_crop_video(video, (1080, 1920))  # Full HD
                    processed_video = processed_video.loop(duration=video_duration)
                else:
                    processed_video = self.resize_and_crop_video(video, (1080, 1920))  # Full HD
                    processed_video = processed_video.subclip(0, video_duration)

                logger.info("Creating overlay elements...")
                logo = (self.create_circular_logo(str(logo_path), size=144)
                    .set_position((40, 80))
                    .set_duration(video_duration))

                header_name = (self.create_text_clip(
                    header_text,
                    72,  # Restored to original size
                    color='white',
                    stroke_width=2
                ).set_position((200, 90))
                .set_duration(video_duration))

                subtitle = (self.create_text_clip(
                    "/@affirmMe",
                    43,  # Restored to original size
                    color='#808080',
                    stroke_width=1
                ).set_position((200, 162))
                .set_duration(video_duration))

                body = (self.create_text_clip(
                    body_text,
                    90,  # Restored to original size
                    width=20,
                    color='white',
                    stroke_width=2
                ).set_position(('center', 'center'))
                .set_duration(video_duration))

                author = (self.create_text_clip(
                    f"- {author_text}",
                    50,  # Restored to original size
                    color='#808080',
                    stroke_width=1
                ).set_position((100, 1750))
                .set_duration(video_duration))

                logger.info("Compositing final video...")
                final_video = CompositeVideoClip(
                    [processed_video, logo, header_name, subtitle, body, author],
                    size=(1080, 1920)  # Full HD
                ).set_duration(video_duration)

                final_video = final_video.set_audio(audio)
                final_video = final_video.fadeout(3)

                logger.info(f"Writing output to: {output_filename}")
                output_path = self.output_folder / output_filename
                final_video.write_videofile(
                    str(output_path),
                    codec='libx264',
                    audio_codec='aac',
                    audio_bitrate='192k',  # Increased quality
                    preset='medium',  # Better quality compression
                    fps=fps,
                    threads=2,  # Balanced threading
                    ffmpeg_params=[
                        '-pix_fmt', 'yuv420p',
                        '-movflags', '+faststart',
                        '-crf', '23',  # Better quality (lower value)
                        '-tune', 'film'  # Optimized for high-quality video
                    ]
                )
                logger.info(f"Video processing completed: {output_filename}")
                self.cleanup_old_files()

        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            raise