from flask import Blueprint, request, jsonify, current_app, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os
from .video_processor import VideoProcessor
from .utils import allowed_file, require_api_key
from pathlib import Path
import time
from .config import Config
from werkzeug.serving import WSGIRequestHandler

WSGIRequestHandler.protocol_version = "HTTP/1.1"  # Use HTTP/1.1 for better timeout handling

api = Blueprint('api', __name__)

@api.route('/')
def home():
    return render_template('test.html')

@api.route('/process_video', methods=['POST'])
def process_video():
    """
    API endpoint for video processing
    Expects multipart/form-data with:
    - audio: audio file
    - header_text: string
    - body_text: string
    - author_text: string
    Uses logo.png from input folder
    """
    try:
        # Validate API key
        api_key = request.headers.get('X-API-Key')
        if api_key != Config.API_KEY:
            return jsonify({'error': 'Invalid API key'}), 401

        # Get and validate text content
        header_text = request.form.get('header_text', '').strip()
        body_text = request.form.get('body_text', '').strip()
        author_text = request.form.get('author_text', '').strip()

        # Specific validation for each text field
        if not header_text:
            return jsonify({'error': 'Header text is required'}), 400
        if not body_text:
            return jsonify({'error': 'Body text is required'}), 400
        if not author_text:
            return jsonify({'error': 'Author text is required'}), 400

        # Validate text lengths
        if len(header_text) > 100:
            return jsonify({'error': 'Header text exceeds maximum length of 100 characters'}), 400
        if len(body_text) > 500:
            return jsonify({'error': 'Body text exceeds maximum length of 500 characters'}), 400
        if len(author_text) > 50:
            return jsonify({'error': 'Author text exceeds maximum length of 50 characters'}), 400

        # Handle audio file
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']
        if not audio_file.filename:
            return jsonify({'error': 'No audio file selected'}), 400

        # Validate audio file type
        if not audio_file.filename.lower().endswith(('.mp3', '.wav')):
            return jsonify({'error': 'Invalid audio file format. Only .mp3 and .wav files are allowed'}), 400

        # Verify required files exist in input folder
        required_files = {
            'logo.png': 'Logo image',
            'background.mp4': 'Background video',
            'BebasNeue-Regular.ttf': 'Font file'
        }
        
        for filename, description in required_files.items():
            file_path = os.path.join(Config.INPUT_FOLDER, filename)
            if not os.path.exists(file_path):
                return jsonify({'error': f'{description} not found: {filename}'}), 400

        # Validate directories exist and are writable
        if not os.path.exists(Config.UPLOAD_FOLDER):
            return jsonify({'error': 'Upload folder not found'}), 500
        if not os.access(Config.UPLOAD_FOLDER, os.W_OK):
            return jsonify({'error': 'Upload folder is not writable'}), 500

        # Save audio file with error handling
        try:
            audio_filename = secure_filename(audio_file.filename)
            audio_path = os.path.join(Config.UPLOAD_FOLDER, audio_filename)
            audio_file.save(audio_path)
        except Exception as e:
            return jsonify({'error': f'Failed to save audio file: {str(e)}'}), 500

        # Initialize video processor with error handling
        try:
            processor = VideoProcessor(
                input_folder=Config.INPUT_FOLDER,
                output_folder=Config.PROCESSED_FOLDER
            )
        except Exception as e:
            return jsonify({'error': f'Failed to initialize video processor: {str(e)}'}), 500

        # Generate unique output filename
        timestamp = int(time.time())
        output_filename = f"processed_{timestamp}_{secure_filename(os.path.splitext(audio_filename)[0])}.mp4"
        
        # Process video with error handling
        try:
            processor.process_video(
                video_filename='background.mp4',
                audio_filename=os.path.join(Config.UPLOAD_FOLDER, audio_filename),
                logo_filename='logo.png',
                header_text=header_text,
                body_text=body_text,
                author_text=author_text,
                output_filename=output_filename
            )
        except Exception as e:
            # Clean up uploaded audio file on error
            if os.path.exists(audio_path):
                os.remove(audio_path)
            return jsonify({'error': f'Video processing failed: {str(e)}'}), 500

        # Clean up uploaded audio file after successful processing
        if os.path.exists(audio_path):
            os.remove(audio_path)

        return jsonify({
            'status': 'success',
            'output_file': output_filename,
            'download_url': f'/download/{output_filename}'
        })

    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@api.route('/download/<filename>')
def download_file(filename):
    """Endpoint to download processed videos"""
    try:
        if not os.path.exists(Config.PROCESSED_FOLDER):
            return jsonify({'error': 'Processed folder not found'}), 500
            
        if not filename or '..' in filename:
            return jsonify({'error': 'Invalid filename'}), 400
            
        file_path = os.path.join(Config.PROCESSED_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        return send_from_directory(Config.PROCESSED_FOLDER, filename)
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500