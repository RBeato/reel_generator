import os
import logging
from pathlib import Path

# Set API_KEY environment variable for testing
os.environ['API_KEY'] = '410850697a62310eae3996723aeff023d04d14a6d739ee3aad84c4048e1fa454'

# Now import the VideoProcessor after setting environment variable
from app.video_processor import VideoProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    base_dir = Path(__file__).parent
    input_dir = base_dir / 'input'
    output_dir = base_dir / 'processed'
    
    # Ensure directories exist
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # Required files check
    required_files = {
        'background.mp4': 'background video',
        'test_output.mp3': 'processed audio',
        'logo.png': 'logo image',
        'BebasNeue-Regular.ttf': 'font file'
    }
    
    missing_files = []
    for filename, description in required_files.items():
        if not (input_dir / filename).exists():
            missing_files.append(f"{description} ({filename})")
    
    if missing_files:
        print("Error: Missing required files in /input folder:")
        for missing in missing_files:
            print(f"- {missing}")
        exit(1)
    
    # Test data
    test_data = {
        'video_filename': 'background.mp4',
        'audio_filename': 'test_output.mp3',
        'logo_filename': 'logo.png',
        'header_text': 'Daily Affirmation',
        'body_text': 'I am worthy of all the good things that happen in my life.',
        'author_text': 'AffirmMe',
        'output_filename': 'test_video_output.mp4'
    }
    
    try:
        logger.info("Starting video processing test...")
        logger.info(f"Input directory: {input_dir}")
        logger.info(f"Output directory: {output_dir}")
        
        # Initialize processor
        processor = VideoProcessor(input_dir, output_dir)
        
        # Process video
        logger.info("Processing video with test data...")
        processor.process_video(**test_data)
        
        output_path = output_dir / test_data['output_filename']
        logger.info(f"Success! Video saved as: {output_path}")
        
        # Verify output file exists and has size > 0
        if output_path.exists() and output_path.stat().st_size > 0:
            logger.info(f"Output file size: {output_path.stat().st_size / (1024*1024):.2f} MB")
        else:
            logger.error("Output file is missing or empty!")
            
    except Exception as e:
        logger.error(f"Error during video processing: {str(e)}")
        raise