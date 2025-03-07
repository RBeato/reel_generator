import os
import logging
from pathlib import Path
from pydub import AudioSegment
import numpy as np
import librosa
import soundfile as sf

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self, input_folder: str, output_folder: str):
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def slow_down_with_pitch_preservation(self, audio_path: Path, speed_factor: float) -> AudioSegment:
        # Load the audio file with higher sample rate
        y, sr = librosa.load(str(audio_path), sr=44100, res_type='kaiser_best')
        
        # Time stretch while preserving pitch with higher quality settings
        y_stretched = librosa.effects.time_stretch(y, rate=speed_factor)
        
        # Save to temporary file with high quality settings
        temp_path = self.output_folder / 'temp_stretched.wav'
        sf.write(
            str(temp_path), 
            y_stretched, 
            sr, 
            subtype='PCM_24',  # 24-bit audio for better quality
            format='WAV'
        )
        
        # Load back with PyDub with high quality settings
        audio_segment = AudioSegment.from_wav(str(temp_path))
        
        # Clean up temp file
        temp_path.unlink()
        
        return audio_segment

    def process_audio(self, affirmation_filename: str, music_filename: str, output_filename: str = 'audio.mp3') -> str:
        try:
            # Load and slow down affirmation
            affirmation_path = self.input_folder / affirmation_filename
            affirmation = self.slow_down_with_pitch_preservation(affirmation_path, 1)  # 20% slower
            
            # Load music with high quality
            music_path = self.input_folder / music_filename
            y_music, sr_music = librosa.load(str(music_path), sr=44100, res_type='kaiser_best')
            
            # Save music to temporary WAV with high quality settings
            temp_music_path = self.output_folder / 'temp_music.wav'
            sf.write(
                str(temp_music_path), 
                y_music, 
                sr_music, 
                subtype='PCM_24',
                format='WAV'
            )
            
            # Load back music with PyDub
            music = AudioSegment.from_wav(str(temp_music_path))
            temp_music_path.unlink()

            # Convert to stereo if mono
            if affirmation.channels == 1:
                affirmation = affirmation.set_channels(2)
            if music.channels == 1:
                music = music.set_channels(2)

            # Ensure consistent high quality sample rates
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

            # Reduce music volume
            music = music - 15  # Reduce music by 15dB
            
            # Add fade effects
            music = music.fade_in(3000).fade_out(3000)
            affirmation = affirmation.fade_in(100).fade_out(100)

            # Combine tracks
            silence = AudioSegment.silent(duration=3000)
            final_audio = music.overlay(silence + affirmation)

            # Export with maximum quality settings
            output_path = self.output_folder / output_filename
            final_audio.export(
                str(output_path),
                format="mp3",
                bitrate="320k",
                parameters=[
                    "-q:a", "0",  # Highest quality
                    "-ar", "44100",  # Sample rate
                    "-b:a", "320k",  # Constant bitrate
                    "-compression_level", "0"  # Less compression
                ]
            )
            
            return output_filename

        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise