from flask import Blueprint, request, jsonify, current_app, render_template, send_from_directory
from werkzeug.utils import secure_filename
import os
from .video_processor import VideoProcessor
from .utils import allowed_file, require_api_key
from pathlib import Path
import time

api = Blueprint('api', __name__)

@api.route('/')
def home():
    return render_template('test.html')

@api.route('/api/process_video', methods=['POST'])
@require_api_key
def process_video():
    try:
        # Get text content from form data
        header_text = request.form.get('header_text')
        body_text = request.form.get('body_text')
        author_text = request.form.get('author_text')
        
        # Handle file uploads
        audio_file = request.files['audio']
        
        # Save audio file
        audio_filename = secure_filename(audio_file.filename)
        audio_path = Path(current_app.config['UPLOAD_FOLDER']) / audio_filename
        audio_file.save(str(audio_path))
        
        # Process the video
        processor = VideoProcessor(
            input_folder=current_app.config['UPLOAD_FOLDER'],
            output_folder=current_app.config['PROCESSED_FOLDER']
        )
        
        output_filename = f"processed_video_{int(time.time())}.mp4"
        
        processor.process_video(
            video_filename='background.mp4',  # Use default background video
            audio_filename=audio_filename,
            logo_filename='logo.png',         # Use default logo
            header_text=header_text,          # Pass text directly
            body_text=body_text,
            author_text=author_text,
            output_filename=output_filename
        )
        
        return jsonify({
            'success': True,
            'output_filename': output_filename,
            'output_url': f"/api/download/{output_filename}"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/download/<filename>')
@require_api_key
def download_file(filename):
    try:
        return send_from_directory(
            current_app.config['PROCESSED_FOLDER'],
            filename,
            as_attachment=True
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404 