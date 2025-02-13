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
from urllib.parse import quote, unquote
import logging

logger = logging.getLogger(__name__)

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

        # Handle audio files
        required_audio = ['affirmation', 'music']
        audio_files = {}
        
        for audio_key in required_audio:
            if audio_key not in request.files:
                return jsonify({'error': f'No {audio_key} file provided'}), 400
                
            audio_file = request.files[audio_key]
            if not audio_file.filename:
                return jsonify({'error': f'No {audio_key} file selected'}), 400
                
            if not audio_file.filename.lower().endswith(('.mp3', '.wav')):
                return jsonify({'error': f'Invalid {audio_key} file format. Only .mp3 and .wav files are allowed'}), 400
                
            # Save audio file
            filename = secure_filename(audio_file.filename)
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            audio_file.save(filepath)
            audio_files[audio_key] = filename

        # Process audio files
        try:
            audio_processor = AudioProcessor(
                input_folder=Config.UPLOAD_FOLDER,
                output_folder=Config.UPLOAD_FOLDER
            )
            
            combined_audio = audio_processor.process_audio(
                affirmation_filename=audio_files['affirmation'],
                music_filename=audio_files['music'],
                output_filename='combined_audio.mp3'
            )
        except Exception as e:
            # Clean up uploaded files
            for filepath in [os.path.join(Config.UPLOAD_FOLDER, f) for f in audio_files.values()]:
                if os.path.exists(filepath):
                    os.remove(filepath)
            return jsonify({'error': f'Audio processing failed: {str(e)}'}), 500

        # Initialize video processor
        try:
            processor = VideoProcessor(
                input_folder=Config.INPUT_FOLDER,
                output_folder=Config.PROCESSED_FOLDER
            )
            
            # Add debug logging before processing
            logger.info(f"Processing video with:")
            logger.info(f"Input folder: {processor.input_folder}")
            logger.info(f"Font path: {processor.input_folder / 'BebasNeue-Regular.ttf'}")
            logger.info(f"Directory contents: {list(processor.input_folder.glob('*'))}")
            
            # Generate output filename without underscores
            timestamp = int(time.time())
            output_filename = f"processed{timestamp}video.mp4"
            
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
        except Exception as e:
            # Clean up all uploaded files
            for filepath in [os.path.join(Config.UPLOAD_FOLDER, f) for f in [*audio_files.values(), combined_audio]]:
                if os.path.exists(filepath):
                    os.remove(filepath)
            return jsonify({'error': f'Video processing failed: {str(e)}'}), 500

        # Clean up uploaded files after successful processing
        for filepath in [os.path.join(Config.UPLOAD_FOLDER, f) for f in [*audio_files.values(), combined_audio]]:
            if os.path.exists(filepath):
                os.remove(filepath)

        return jsonify({
            'status': 'success',
            'output_file': output_filename,
            'download_url': f'/download/{quote(output_filename)}'
        })

    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@api.route('/download/<filename>')
def download_file(filename):
    try:
        # Decode the URL-encoded filename
        filename = unquote(filename)
        filename = secure_filename(filename)
        
        file_path = os.path.join(Config.PROCESSED_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        response = send_from_directory(
            Config.PROCESSED_FOLDER, 
            filename, 
            as_attachment=True,
            mimetype='video/mp4'
        )
        
        # Set headers separately
        response.headers['Content-Type'] = 'video/mp4'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({'error': str(e)}), 500