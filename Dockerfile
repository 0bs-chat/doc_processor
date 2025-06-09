FROM runpod/base:0.6.3-cuda12.6.2

# Set python3.11 as the default python
RUN ln -sf $(which python3.11) /usr/local/bin/python && \
    ln -sf $(which python3.11) /usr/local/bin/python3

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
    
# Add application files
ADD requirements.txt .
ADD handler.py .
ADD test_input.json .
ADD preloader.py .

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv pip install --upgrade -r /requirements.txt --no-cache-dir --system && uv run /preloader.py

# Run the handler
CMD uv run /handler.py

# Build and push commands:
# sudo docker build --platform linux/amd64 --tag mantrakp04/doc_processor:enhancedv3 . && sudo docker push mantrakp04/doc_processor:enhancedv3
# sudo docker run -it --runtime=nvidia --rm mantrakp04/doc_processor:enhancedv3 /bin/bash -c 'tail -f /dev/null'