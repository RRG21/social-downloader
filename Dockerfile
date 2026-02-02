FROM python:3.9-slim

# Install FFmpeg and system tools
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set up user to avoid permission issues
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /home/user/app
COPY --chown=user . .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Hugging Face port
EXPOSE 7860

# Run the app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]
