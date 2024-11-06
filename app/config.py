import os
from pathlib import Path

class Config:
    # Base directory for the application
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # Temporary storage for uploaded files
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    PROCESSED_FOLDER = BASE_DIR / 'processed'
    INPUT_FOLDER = BASE_DIR / 'input'
    
    # Create necessary directories
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    PROCESSED_FOLDER.mkdir(exist_ok=True)
    INPUT_FOLDER.mkdir(exist_ok=True)
    
    # Maximum file size (50MB)
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        'video': {'mp4', 'mov'},
        'audio': {'mp3', 'wav'},
        'image': {'png', 'jpg', 'jpeg'},
        'text': {'txt'}
    }
    
    # ImageMagick binary path
    IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
    
    # API Authentication
    API_KEY = os.getenv('API_KEY')
    if not API_KEY:
        raise ValueError("API_KEY environment variable is not set")