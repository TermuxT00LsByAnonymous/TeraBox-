FROM python:3.10-slim

# System dependencies aur FFmpeg ko clean tareeqe se install karna
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python environment caching optimize karna fast deployment ke liye
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Bot ko run karne ki command
CMD ["python", "bot.py"]
