from app import create_app

app = create_app()
app.config['TIMEOUT'] = 300
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['REQUEST_TIMEOUT'] = 300 