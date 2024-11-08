from flask import Flask, request
from .config import Config
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler(
        'logs/video_service.log',
        maxBytes=10240,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    
    # Add request logging
    @app.before_request
    def log_request_info():
        app.logger.info('Headers: %s', dict(request.headers))
        app.logger.info('Body: %s', request.get_data())
    
    app.logger.info('Video service startup')
    
    # Register blueprint without prefix
    from .routes import api
    app.register_blueprint(api)
    
    return app 