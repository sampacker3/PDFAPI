FROM python:3.11-slim

# Install wkhtmltopdf dependencies
RUN apt-get update && apt-get install -y \
    wget \
    xvfb \
    fontconfig \
    libjpeg62-turbo \
    libxrender1 \
    xfonts-base \
    xfonts-75dpi \
    && rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf from .deb release
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb \
    && apt-get update \
    && apt-get install -y ./wkhtmltox_0.12.6-1.buster_amd64.deb \
    && rm wkhtmltox_0.12.6-1.buster_amd64.deb

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8080

# Run application
CMD exec gunicorn --bind :$PORT --workers 1 --threads 4 --timeout 0 main:app
