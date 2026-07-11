# Menggunakan image base Ubuntu 22.04 LTS yang stabil dan mendukung FFmpeg terbaru
FROM ubuntu:22.04

# Hindari interaktif prompt saat instalasi apt
ENV DEBIAN_FRONTEND=noninteractive

# Update apt dan install Python3, Pip, serta FFmpeg
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory sesuai permintaan
WORKDIR /home/ubuntu/clipper/scripts/python

# Copy dan install requirements Python
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Biarkan container idle / standby selamanya
CMD ["tail", "-f", "/dev/null"]
