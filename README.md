# Document Processor Service

A powerful document processing service built on [Docling](https://github.com/DS4SD/docling) that converts various document formats (PDF, DOCX, PPTX, images, etc.) into structured text with advanced enrichments like table extraction, formula recognition, and image analysis.

## ✨ Features

### Document Format Support
- **PDF Documents** - Advanced processing with OCR, table extraction, and layout analysis
- **Microsoft Office** - Word (DOCX), PowerPoint (PPTX), Excel (XLSX)
- **Images** - PNG, JPEG with vision-language model processing
- **Text/Markup** - Markdown, HTML, AsciiDoc
- **Structured Data** - CSV, JSON
- **Scientific** - USPTO Patents (XML), JATS XML
- **Audio** - Audio file processing

### Advanced Processing Capabilities
- **🔍 OCR** - Text extraction from images and scanned documents
- **📊 Table Structure** - Intelligent table detection and extraction
- **🧮 Formula Recognition** - Mathematical formula detection and conversion
- **🖼️ Image Analysis** - Picture classification and description using vision models
- **📝 Code Detection** - Code block identification and extraction
- **📄 Layout Analysis** - Document structure understanding

### Output Formats
- **Markdown** - Clean, structured markdown output
- **HTML** - Rich HTML with preserved formatting
- **JSON** - Structured data with metadata
- **Plain Text** - Simple text extraction

## 🚀 Deployment Options

### 1. RunPod Serverless (Recommended)
Deploy as a serverless worker on RunPod for automatic scaling and GPU acceleration.

```bash
# Build and deploy
docker build --platform linux/amd64 -t your-registry/doc-processor .
docker push your-registry/doc-processor
```

### 2. FastAPI Service
Run as a standalone web service with REST API.

```bash
# Install dependencies
pip install -r requirements.txt

# Download models (first time only)
python preloader.py

# Start the service
python app.py
```

### 3. Docker Container
```bash
# Build
docker build -t doc-processor .

# Run FastAPI service
docker run -p 8000:8000 -e SERVICE=fastapi doc-processor

# Run RunPod handler
docker run -e SERVICE=runpod doc-processor
```

## 📖 API Usage

### RunPod Serverless

```python
import runpod

# Submit job
job = runpod.submit({
    "input": {
        "document_url": "https://example.com/document.pdf"
    }
})

# Get result
result = runpod.get_job(job['id'])
print(result['output']['content'])  # Processed document content
```

### FastAPI Service

```bash
# Health check
curl http://localhost:8000/

# Process document
curl -X POST "http://localhost:8000/process" \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "document_url": "https://example.com/document.pdf"
  }'
```

```python
import httpx

# Using Python client
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/process",
        headers={"Authorization": "Bearer your-api-key"},
        json={"document_url": "https://example.com/document.pdf"}
    )
    result = response.json()
    print(result['result']['content'])
```

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEVICE_CAPABILITY` | `high` | Processing capability level (`low`, `medium`, `high`) |
| `API_KEY` | `admin` | API authentication key for FastAPI service |
| `SERVICE` | `runpod` | Service mode (`runpod` or `fastapi`) |
| `WORKERS` | `1` | Number of FastAPI workers |

### Device Capability Levels

#### `low` - Minimal Resource Usage
- ✅ Basic OCR and table extraction
- ❌ Formula recognition disabled
- ❌ Image classification disabled
- ❌ Picture description disabled
- 💡 Best for: Simple text extraction, resource-constrained environments

#### `medium` - Balanced Processing
- ✅ Code and formula enrichment
- ✅ Advanced OCR and table structure
- ❌ Image processing disabled
- 💡 Best for: Most document types without heavy image analysis

#### `high` - Full Processing (Default)
- ✅ All enrichments enabled
- ✅ Vision-language model for image description
- ✅ Advanced table analysis with cell matching
- ✅ High-resolution image generation
- 💡 Best for: Complete document understanding, research papers

## 📊 Response Format

```json
{
  "content": "# Document Title\n\nProcessed content in markdown...",
  "metadata": {
    "source": "https://example.com/document.pdf",
    "filename": "document.pdf",
    "page_count": 10,
    "export_format": "markdown",
    "device_capability": "high",
    "enrichments_applied": {
      "code_enrichment": true,
      "formula_enrichment": true,
      "picture_classification": true,
      "picture_description": true,
      "table_structure": true,
      "ocr": true
    },
    "enrichment_stats": {
      "code_blocks": 5,
      "formulas": 12,
      "images": 8,
      "tables": 3
    }
  },
  "status": "success"
}
```

## 🛠️ Development

### Local Testing

```bash
# Test with sample input
python handler.py

# Custom test input
echo '{"input": {"document_url": "your-url-here"}}' > test_input.json
python handler.py
```

### Model Management

```python
# Download all models (required for first run)
python preloader.py

# Models are stored in ./models/ directory
# Includes: layout detection, table extraction, OCR, vision models
```

### Dependencies

Core dependencies:
- `docling` - Document processing framework
- `fastapi` - Web framework for API service
- `runpod` - Serverless platform integration
- `httpx` - HTTP client for document downloading
- `uvicorn` - ASGI server

## 🔧 System Requirements

### Minimum Requirements
- **Memory**: 8GB RAM
- **Storage**: 10GB for models
- **Python**: 3.12+

### Recommended for GPU Acceleration
- **GPU**: NVIDIA GPU with CUDA support
- **VRAM**: 8GB+ for full capability mode
- **CUDA**: 12.6+ (included in Docker image)

## 📝 Example Use Cases

### Research Paper Processing
```python
# Process arXiv paper
result = process_document("http://arxiv.org/pdf/1706.03762")
# Extracts: formulas, tables, figures, code snippets, references
```

### Business Document Analysis
```python
# Process financial reports, contracts, presentations
result = process_document("https://company.com/annual-report.pdf")
# Extracts: structured tables, charts, key metrics
```

### Multi-format Conversion
```python
# Convert between formats while preserving structure
# PDF → Markdown, DOCX → HTML, etc.
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with different document types
5. Submit a pull request

## 📄 License

This project is part of the larger application ecosystem. See the main repository for license information.

## 🔗 Related Links

- [Docling Documentation](https://github.com/DS4SD/docling)
- [RunPod Platform](https://runpod.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
