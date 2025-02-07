FROM python:3.9-slim

# Install system dependencies including ffmpeg and imagemagick
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app

CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"] 