import os
import logging
from pathlib import Path
from typing import Optional
from moviepy.editor import AudioFileClip
import numpy as np

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self, input_folder: str, output_folder: str):
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(parents=True, exist_ok=True)

    def _get_rms_level(self, audio: AudioFileClip) -> float:
        """Calculate RMS level of audio clip"""
        samples = audio.to_soundarray()
        return np.sqrt(np.mean(samples**2))

    def _adjust_volume(self, audio: AudioFileClip, target_rms: float) -> AudioFileClip:
        """Adjust audio volume to match target RMS"""
        current_rms = self._get_rms_level(audio)
        adjustment_factor = target_rms / current_rms if current_rms > 0 else 1
        return audio.volumex(adjustment_factor)

    def process_audio(
        self,
        affirmation_filename: str,
        music_filename: str,
        output_filename: str = 'audio.mp3'
    ) -> str:
        """Process and combine audio files"""
        try:
            # Load audio files
            affirmation = AudioFileClip(str(self.input_folder / affirmation_filename))
            music = AudioFileClip(str(self.input_folder / music_filename))

            # Slow down affirmation using fl_time_symmetrize
            affirmation = affirmation.fl_time_symmetrize(0.8)  # 20% slower
            affirmation_duration = affirmation.duration

            # Calculate total duration
            total_duration = affirmation_duration + 6  # 3 seconds padding on each side

            # Crop and loop music if needed
            if music.duration < total_duration:
                music = music.loop(duration=total_duration)
            else:
                music = music.subclip(0, total_duration)

            # Add fade effects to music
            music = music.audio_fadein(2).audio_fadeout(2)

            # Balance volumes
            target_rms = 0.1  # Target RMS level for affirmation
            affirmation = self._adjust_volume(affirmation, target_rms)
            music = self._adjust_volume(music, target_rms * 0.8)  # Music 20% quieter

            # Position affirmation with 3-second padding
            affirmation = affirmation.set_start(3)

            # Combine tracks
            final_audio = CompositeAudioClip([music, affirmation])

            # Export
            output_path = self.output_folder / output_filename
            final_audio.write_audiofile(
                str(output_path),
                fps=44100,
                bitrate='192k'
            )

            return output_filename

        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            raise