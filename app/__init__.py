from flask import Flask, request
from .config import Config
import logging
from logging.handlers import RotatingFileHandler
import os
from werkzeug.serving import WSGIRequestHandler

# Use HTTP/1.1 for better timeout handling
WSGIRequestHandler.protocol_version = "HTTP/1.1"

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize logging with larger file size
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler(
        'logs/video_service.log',
        maxBytes=102400,  # Increased to 100KB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    
    # Enhanced request logging
    @app.before_request
    def log_request_info():
        app.logger.info('Request Method: %s, Path: %s', request.method, request.path)
        app.logger.info('Headers: %s', dict(request.headers))
        if not request.files:
            app.logger.info('Body: %s', request.get_data())
        else:
            app.logger.info('Files in request: %s', list(request.files.keys()))
    
    # Response logging
    @app.after_request
    def log_response_info(response):
        app.logger.info('Response Status: %s', response.status)
        if response.status_code >= 400:  # Log headers only for errors
            app.logger.info('Response Headers: %s', dict(response.headers))
        return response
    
    app.logger.info('Video service startup')
    
    from .routes import api
    app.register_blueprint(api)
    
    return app 