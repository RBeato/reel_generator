from moviepy.config import change_settings
from .config import Config

# Set MoviePy's ImageMagick binary path
change_settings({"IMAGEMAGICK_BINARY": Config.IMAGEMAGICK_BINARY})