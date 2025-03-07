import os
from pathlib import Path

class Config:
    # Base directory for the application
    if os.getenv('FLASK_ENV') == 'development':
        # In Docker, use absolute paths
        BASE_DIR = Path('/app')
    else:
        # Outside Docker, use relative paths
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
    
    # ImageMagick binary path (cross-platform)
    if os.name == 'posix':  # Linux/Unix
        IMAGEMAGICK_BINARY = "/usr/bin/convert"
    elif os.name == 'nt':   # Windows
        IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
    else:
        raise ValueError("Unsupported operating system")
    
    # API Authentication
    API_KEY = os.getenv('API_KEY')
    if not API_KEY:
        raise ValueError("API_KEY environment variable is not set")