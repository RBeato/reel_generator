from app import create_app

app = create_app()

if __name__ == '__main__':
    app.config['TIMEOUT'] = 300
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max-length
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['REQUEST_TIMEOUT'] = 300
    app.run(host='0.0.0.0', port=5000, threaded=True, timeout=300) 