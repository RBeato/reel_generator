import os
import logging
from pathlib import Path
from pydub import AudioSegment
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAudioProcessor:
    def __init__(self, input_folder: str, output_folder: str):
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def process_audio(self, affirmation_filename: str, music_filename: str, output_filename: str = 'audio.mp3') -> str:
        try:
            # Load audio files
            affirmation = AudioSegment.from_mp3(str(self.input_folder / affirmation_filename))
            music = AudioSegment.from_mp3(str(self.input_folder / music_filename))

            # Convert to stereo if mono
            if affirmation.channels == 1:
                affirmation = affirmation.set_channels(2)
            if music.channels == 1:
                music = music.set_channels(2)

            # Ensure consistent sample rates
            affirmation = affirmation.set_frame_rate(44100)
            music = music.set_frame_rate(44100)

            logger.info(f"Affirmation duration: {len(affirmation) / 1000} seconds")
            logger.info(f"Music duration: {len(music) / 1000} seconds")

            # Set duration for both clips
            affirmation_duration = len(affirmation)
            total_duration = affirmation_duration + 6000

            # Process music
            if len(music) < total_duration:
                music = music * (total_duration // len(music) + 1)
            music = music[:total_duration]

            # Instead of RMS adjustment, use simple volume reduction
            music = music - 12  # Reduce music by 12dB
            
            # Add fade effects
            music = music.fade_in(3000).fade_out(3000)
            affirmation = affirmation.fade_in(100).fade_out(100)

            # Combine tracks
            silence = AudioSegment.silent(duration=3000)
            final_audio = music.overlay(silence + affirmation)

            # Export with high quality settings
            output_path = self.output_folder / output_filename
            final_audio.export(
                str(output_path),
                format="mp3",
                bitrate="320k",
                parameters=["-q:a", "0"]
            )
            
            return output_filename

        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise

if __name__ == "__main__":
    base_dir = Path(__file__).parent
    input_dir = base_dir / 'input'
    output_dir = base_dir / 'processed'
    
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    processor = TestAudioProcessor(input_dir, output_dir)
    
    try:
        output = processor.process_audio('affirmation.mp3', 'music.mp3', 'test_output.mp3')
        print(f"Success! Output saved as: {output_dir}/{output}")
    except Exception as e:
        print(f"Error: {str(e)}")