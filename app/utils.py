from functools import wraps
from flask import request, jsonify, current_app
import os

def allowed_file(filename, file_type):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS'][file_type]

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == current_app.config['API_KEY']:
            return f(*args, **kwargs)
        return jsonify({'error': 'Invalid API key'}), 401
    return decorated_function 