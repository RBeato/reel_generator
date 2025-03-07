FROM python:3.9-slim

# Install system dependencies including ffmpeg and imagemagick
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Configure ImageMagick policy to allow reading text files
RUN sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@*"/' /etc/ImageMagick-6/policy.xml

WORKDIR /app

# Copy requirements first and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./app /app/app

# Set permissions
RUN chmod -R 755 /app

# Run the application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8000"]