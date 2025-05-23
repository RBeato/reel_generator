# reel_generator

A Python-based video processing service.

## Local Development Setup

1. **Clone the repository**
```bash
git clone [repository-url]
cd reel_generator
```

2. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Run locally**
```bash
python run.py
```

## Making Changes

### Local Development
1. **Open the project in VS Code or your preferred IDE**
2. **Navigate to the file you want to modify**:
   - For video processing changes: `app/video_processor.py`
   - For configuration changes: `app/config.py`
   - For utility functions: `app/utils.py`

3. **Test your changes locally**:
   - Place test files in the `input` folder
   - Run `python run.py`
   - Check output in the `output` folder

### GitHub Updates
1. **Go to [GitHub Repository URL]**
2. **Navigate to the file you want to edit**
3. **Click the pencil icon (Edit this file)**
4. **Make your changes**
5. **Scroll down to "Commit changes"**
6. **Add a descriptive commit message**
7. **Click "Commit changes"**

## Cloud Deployment (DigitalOcean)

[Previous deployment instructions remain the same...]

## Updating Code

### Local Updates

1. **Make changes in your IDE**:
   - Open VS Code
   - Navigate to project folder
   - Make necessary changes
   - Test locally using steps in "Local Development"

2. **Commit changes:**
```bash
git add .
git commit -m "Your commit message"
git push origin main
```

### Cloud Updates

1. **SSH into your DigitalOcean droplet**:
   - Open terminal
   - `ssh root@your_droplet_ip`
   - Enter your password

2. **Stop the service:**
```bash
sudo systemctl stop reel_generator
```

3. **Pull updates:**
```bash
cd /var/www/reel_generator
git pull origin main
```

4. **Update dependencies (if needed):**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

5. **Restart service:**
```bash
sudo systemctl start reel_generator
sudo systemctl status reel_generator
```

## Monitoring

### View Service Logs
```bash
# View service logs
sudo journalctl -u reel_generator -f

# View application logs
tail -f /opt/py_video_creator/logs/video_service.log
```

### Check Service Status
```bash
sudo systemctl status reel_generator
```

## Troubleshooting

If the service fails to start:
1. Check logs: `sudo journalctl -u reel_generator -f`
2. Verify Python path: `which python` in the venv
3. Ensure all dependencies are installed
4. Check file permissions in /opt/py_video_creator

## Directory Structure
```
py_video_creator/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── moviepy_conf.py
│   ├── routes.py
│   ├── utils.py
│   └── video_processor.py
├── input/
├── logs/
├── output/
├── venv/
├── requirements.txt
└── run.py
```

## Maintenance

- Regularly check logs for errors
- Monitor disk space usage
- Keep dependencies updated
- Backup important configuration files
- Test updates locally before deploying to production

## Local Testing

### Prerequisites
1. **Required Dependencies**
```bash
pip install moviepy Pillow numpy
```

### Required Input Files
Ensure the following files are in your `input` folder:
- `background.mp4` (or your source video)
- `sound.mp3` (background audio)
- `logo.png` (watermark/logo)
- `header_text.txt` (title text)
- `body.txt` (main content)
- `author.txt` (attribution)
- `BebasNeue-Regular.ttf` (font file)

### Testing Process
1. **Configure your paths**:
   Edit `app/config.py` to set your local paths:
   ```python
   INPUT_FOLDER = "path/to/your/local/input/folder"
   OUTPUT_FOLDER = "path/to/your/local/output/folder"
   ```

2. **Run the test**:
   ```bash
   python run.py
   ```

3. **Check results**:
   - Look for the processed video in your output folder
   - Check the logs in `logs/video_service.log` for any errors
   - Verify video quality and content placement

### Common Testing Issues
- **File not found errors**: Verify all required files are in the input folder
- **Codec issues**: Install additional codecs if needed (`apt-get install ffmpeg`)
- **Memory errors**: Reduce video quality or resolution in config
- **Font errors**: **Ensure** font file path is correct

## API Testing

### Using curl
```bash
# Test video processing
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -F "audio=@/path/to/audio.mp3" \
  -F "header_text=Your Header" \
  -F "body_text=Your Body Text" \
  -F "author_text=Author Name" \
  https://your-domain.com/process_video

# Download processed video
curl -O -J -L https://your-domain.com/download/your_video_filename.mp4
```

### Using Postman
1. Create new POST request to `https://your-domain.com/process_video`
2. Add header: `X-API-Key: your-api-key`
3. In Body tab, select "form-data"
4. Add fields:
   - audio: Select File, choose audio file
   - header_text: Text input
   - body_text: Text input
   - author_text: Text input
5. Send request