from moviepy.config import change_settings
import os

# Set the path to ImageMagick binary - Updated with correct folder name
IMAGEMAGICK_BINARY = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"

# Configure MoviePy to use ImageMagick
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_BINARY})