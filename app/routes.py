from flask import Blueprint, request, jsonify, current_app, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os
from .video_processor import VideoProcessor
from .utils import allowed_file, require_api_key
from pathlib import Path
import time
from .config import Config
from werkzeug.serving import WSGIRequestHandler
from .audio_processor import AudioProcessor

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
    - affirmation: affirmation audio file
    - music: music audio file
    - header_text: string
    - body_text: string
    - author_text: string
    Uses logo.png from input folder
    """
    try:
        current_app.logger.info("Starting video processing request")
        
        # Validate API key
        api_key = request.headers.get('X-API-Key')
        if api_key != Config.API_KEY:
            current_app.logger.warning("Invalid API key attempt")
            return jsonify({'error': 'Invalid API key'}), 401

        # Get and validate text content
        header_text = request.form.get('header_text', '').strip()
        body_text = request.form.get('body_text', '').strip()
        author_text = request.form.get('author_text', '').strip()

        # Log text content lengths
        current_app.logger.info(f"Text lengths - Header: {len(header_text)}, Body: {len(body_text)}, Author: {len(author_text)}")

        # Validate required fields
        if not all([header_text, body_text, author_text]):
            missing_fields = []
            if not header_text: missing_fields.append('header_text')
            if not body_text: missing_fields.append('body_text')
            if not author_text: missing_fields.append('author_text')
            current_app.logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
            return jsonify({'error': f"Missing required fields: {', '.join(missing_fields)}"}), 400

        # Validate text lengths
        text_limits = {
            'header_text': (header_text, 100),
            'body_text': (body_text, 500),
            'author_text': (author_text, 50)
        }
        
        for field, (text, limit) in text_limits.items():
            if len(text) > limit:
                current_app.logger.warning(f"{field} exceeds maximum length of {limit} characters")
                return jsonify({'error': f'{field} exceeds maximum length of {limit} characters'}), 400

        # Handle audio files
        required_audio = ['affirmation', 'music']
        audio_files = {}
        
        for audio_key in required_audio:
            if audio_key not in request.files:
                current_app.logger.warning(f"Missing {audio_key} file in request")
                return jsonify({'error': f'No {audio_key} file provided'}), 400
                
            audio_file = request.files[audio_key]
            if not audio_file.filename:
                current_app.logger.warning(f"No filename for {audio_key}")
                return jsonify({'error': f'No {audio_key} file selected'}), 400
                
            if not audio_file.filename.lower().endswith(('.mp3', '.wav')):
                current_app.logger.warning(f"Invalid file format for {audio_key}: {audio_file.filename}")
                return jsonify({'error': f'Invalid {audio_key} file format. Only .mp3 and .wav files are allowed'}), 400
                
            # Save audio file
            filename = secure_filename(audio_file.filename)
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            audio_file.save(filepath)
            audio_files[audio_key] = filename
            current_app.logger.info(f"Saved {audio_key} file: {filename}")

        # Process audio files
        try:
            current_app.logger.info("Starting audio processing")
            audio_processor = AudioProcessor(
                input_folder=Config.UPLOAD_FOLDER,
                output_folder=Config.UPLOAD_FOLDER
            )
            
            combined_audio = audio_processor.process_audio(
                affirmation_filename=audio_files['affirmation'],
                music_filename=audio_files['music'],
                output_filename='combined_audio.mp3'
            )
            current_app.logger.info("Audio processing completed successfully")
            
        except Exception as e:
            current_app.logger.error(f"Audio processing failed: {str(e)}")
            self._cleanup_files([os.path.join(Config.UPLOAD_FOLDER, f) for f in audio_files.values()])
            return jsonify({'error': f'Audio processing failed: {str(e)}'}), 500

        # Initialize video processor
        try:
            current_app.logger.info("Starting video processing")
            processor = VideoProcessor(
                input_folder=Config.INPUT_FOLDER,
                output_folder=Config.PROCESSED_FOLDER
            )
            
            # Generate output filename
            timestamp = int(time.time())
            output_filename = f"processed_{timestamp}_{secure_filename(os.path.splitext(audio_files['affirmation'])[0])}.mp4"
            
            # Process video using combined audio
            processor.process_video(
                video_filename='background.mp4',
                audio_filename=os.path.join(Config.UPLOAD_FOLDER, combined_audio),
                logo_filename='logo.png',
                header_text=header_text,
                body_text=body_text,
                author_text=author_text,
                output_filename=output_filename
            )
            current_app.logger.info("Video processing completed successfully")
            
        except Exception as e:
            current_app.logger.error(f"Video processing failed: {str(e)}")
            self._cleanup_files([os.path.join(Config.UPLOAD_FOLDER, f) for f in [*audio_files.values(), combined_audio]])
            return jsonify({'error': f'Video processing failed: {str(e)}'}), 500

        # Clean up uploaded files after successful processing
        self._cleanup_files([os.path.join(Config.UPLOAD_FOLDER, f) for f in [*audio_files.values(), combined_audio]])
        
        current_app.logger.info(f"Request completed successfully. Output file: {output_filename}")
        return jsonify({
            'status': 'success',
            'output_file': output_filename,
            'download_url': f'/download/{output_filename}'
        })

    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
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