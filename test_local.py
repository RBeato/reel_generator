from app.video_processor import VideoProcessor

def test_video():
    processor = VideoProcessor(
        input_folder=r'C:\Users\rbsou\Desktop\ffmpeg_test\input',
        output_folder=r'C:\Users\rbsou\Desktop\ffmpeg_test\output'
    )

    # Process with direct text input
    processor.process_video(
        video_filename='background.mp4',
        audio_filename='sound.mp3',
        logo_filename='logo.png',
        header_text="Your Header Text",
        body_text="Your Body Text Here\nSecond Line",
        author_text="Author Name",
        output_filename='high_quality_test.mp4'
    )

if __name__ == "__main__":
    test_video() 