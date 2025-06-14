FROM nvidia/cuda:12.6.3-cudnn-devel-ubuntu22.04

# Install Python 3 and set it as the default interpreter
RUN apt-get update && apt-get install -y python3 python3-pip && \
    ln -sf $(which python3) /usr/local/bin/python

# Install system dependencies for docling
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgraphicsmagick1-dev \
    libatlas-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
ADD requirements.txt .
ADD preloader.py .
ADD processor.py .
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv pip install --upgrade -r /requirements.txt --no-cache-dir --system && uv run /preloader.py

# Add application files
ADD app.py .

CMD uv run /app.py

# Build and push commands:
# sudo docker build --platform linux/amd64 --tag mantrakp04/doc_processor:v1 . && sudo docker push mantrakp04/doc_processor:v1
# sudo docker run -it --runtime=nvidia -p 7860:7860 --rm mantrakp04/doc_processor:v1 /bin/bash -c 'tail -f /dev/null'