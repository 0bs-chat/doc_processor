FROM runpod/base:0.6.3-cuda11.8.0

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

# Install dependencies
COPY requirements.txt /requirements.txt
RUN uv pip install --upgrade -r /requirements.txt --no-cache-dir --system

# Copy model pre-download script
COPY preload_models.py /preload_models.py

# Set environment variables for model downloads
ENV HF_HUB_DISABLE_PROGRESS_BARS=1
ENV TRANSFORMERS_VERBOSITY=error
ENV DOCLING_ARTIFACTS_PATH=/root/.cache/docling/models
ENV OMP_NUM_THREADS=4

# Pre-download all models during build
RUN echo "🚀 Starting model pre-download process..." && \
    python /preload_models.py && \
    echo "✅ Model pre-download completed!" && \
    du -sh /root/.cache/* 2>/dev/null || true

# Add application files
ADD handler.py .
ADD test_input.json .

# Set proper permissions for cache directories
RUN chmod -R 755 /root/.cache/ 2>/dev/null || true

# Health check to verify models are available
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from docling.document_converter import DocumentConverter; print('✅ Docling ready')" || exit 1

# Run the handler
CMD python -u /handler.py

# Build and push commands:
# sudo docker build --platform linux/amd64 --tag mantrakp04/doc_processor:enhanced . && sudo docker push mantrakp04/doc_processor:enhanced
# sudo docker run -it --runtime=nvidia --rm mantrakp04/doc_processor:enhanced