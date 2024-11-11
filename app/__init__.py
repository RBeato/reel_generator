import os
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
    level=logging.DEBUG,  # Changed from INFO to DEBUG
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
        try:
            if width:
                text = '\n'.join(wrap(text, width=width))
            logger.debug(f"Creating text clip: {text[:30]}...")
            return TextClip(
                text,
                fontsize=font_size,
                color=color,
                font=self.font,
                stroke_color=stroke_color,
                stroke_width=stroke_width,
                method='label'
            )
        except Exception as e:
            logger.error(f"Error creating text clip: {str(e)}")
            raise

    def create_circular_logo(self, logo_path: str, size: int = 100) -> ImageClip:
        """Create a circular logo clip."""
        try:
            logger.debug(f"Loading logo from: {logo_path}")
            logo = Image.open(logo_path)
            mask = Image.new('L', (size, size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, size, size), fill=255)
            logo = logo.resize((size, size), Image.Resampling.LANCZOS)
            output = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            output.paste(logo, (0, 0))
            output.putalpha(mask)
            return ImageClip(np.array(output))
        except Exception as e:
            logger.error(f"Error creating circular logo: {str(e)}")
            raise

    def resize_and_crop_video(
        self,
        clip: VideoFileClip,
        target_size: Tuple[int, int]
    ) -> VideoFileClip:
        """Resize video to target size while maintaining aspect ratio and crop."""
        try:
            logger.debug(f"Resizing video from {clip.size} to {target_size}")
            # Reduce target size by half for better performance
            target_size = (target_size[0] // 2, target_size[1] // 2)
            resize_factor = target_size[1] / clip.size[1]
            resized_width = int(clip.size[0] * resize_factor)
            resized = clip.resize(width=resized_width, height=target_size[1])
            x_center = resized.size[0] * 0.8
            x1 = int(x_center - target_size[0]/2)
            x1 = max(0, min(x1, resized.size[0] - target_size[0]))
            return resized.crop(x1=x1, y1=0, width=target_size[0], height=target_size[1])
        except Exception as e:
            logger.error(f"Error resizing video: {str(e)}")
            raise

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
            
            # Handle paths
            if os.path.isabs(audio_filename):
                audio_path = Path(audio_filename)
            else:
                audio_path = self.input_folder / audio_filename
                
            video_path = self.input_folder / video_filename
            logo_path = self.input_folder / logo_filename
            
            logger.debug(f"Loading audio from: {audio_path}")
            audio = AudioFileClip(str(audio_path))
            audio = audio.audio_fadeout(3)
            
            video_duration = audio.duration + 0.5
            fps = 24  # Reduced from 30
            
            logger.debug(f"Loading video from: {video_path}")
            with VideoFileClip(str(video_path)) as video:
                processed_video = self.resize_and_crop_video(video, (540, 960))  # Half resolution
                if video.duration < video_duration:
                    processed_video = processed_video.loop(duration=video_duration)
                else:
                    processed_video = processed_video.subclip(0, video_duration)

                logger.debug("Creating overlay elements...")
                logo = (self.create_circular_logo(str(logo_path), size=72)  # Reduced from 144
                    .set_position((20, 40))  # Adjusted for smaller size
                    .set_duration(video_duration))

                header_name = (self.create_text_clip(
                    header_text,
                    36,  # Reduced from 72
                    color='white',
                    stroke_width=0
                ).set_position((100, 45))  # Adjusted for smaller size
                .set_duration(video_duration))

                subtitle = (self.create_text_clip(
                    "/@affirmMe",
                    22,  # Reduced from 43
                    color='#808080',
                    stroke_width=0
                ).set_position((100, 81))  # Adjusted for smaller size
                .set_duration(video_duration))

                body = (self.create_text_clip(
                    body_text,
                    45,  # Reduced from 90
                    width=20,
                    color='white',
                    stroke_width=0
                ).set_position(('center', 'center'))
                .set_duration(video_duration))

                author = (self.create_text_clip(
                    f"- {author_text}",
                    25,  # Reduced from 50
                    color='#808080',
                    stroke_width=0
                ).set_position((50, 875))  # Adjusted for smaller size
                .set_duration(video_duration))

                logger.debug("Compositing final video...")
                final_video = CompositeVideoClip(
                    [processed_video, logo, header_name, subtitle, body, author],
                    size=(540, 960)  # Half resolution
                ).set_duration(video_duration)

                final_video = final_video.set_audio(audio)
                final_video = final_video.fadeout(3)

                logger.info(f"Writing output to: {output_filename}")
                output_path = self.output_folder / output_filename
                final_video.write_videofile(
                    str(output_path),
                    codec='libx264',
                    audio_codec='aac',
                    audio_bitrate='128k',  # Further reduced from 192k
                    preset='ultrafast',
                    fps=fps,
                    threads=1,  # Reduced from 2
                    ffmpeg_params=[
                        '-pix_fmt', 'yuv420p',
                        '-movflags', '+faststart',
                        '-crf', '32',  # Increased from 28 (even lower quality)
                        '-tune', 'fastdecode'
                    ]
                )
                logger.info(f"Video processing completed: {output_filename}")

        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            raise