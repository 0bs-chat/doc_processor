import runpod
import httpx
from io import BytesIO
from docling.document_converter import DocumentConverter, PdfFormatOption, ImageFormatOption, PowerpointFormatOption, WordFormatOption
from docling_core.types.io import DocumentStream
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableFormerMode,
    EasyOcrOptions,
    granite_picture_description,
    PictureDescriptionVlmOptions
)
import os

# Configure enhanced pipeline with all enrichments enabled
def create_enhanced_converter():
    """Create a fully enhanced DocumentConverter with all enrichments enabled."""
    
    # Configure PDF pipeline with all enrichments
    pipeline_options = PdfPipelineOptions()
    
    # Enable all enrichment features
    pipeline_options.do_code_enrichment = True           # Code block understanding
    pipeline_options.do_formula_enrichment = True       # LaTeX formula extraction
    pipeline_options.do_picture_classification = True   # Classify image types
    pipeline_options.do_picture_description = True      # Generate image captions
    
    # Enhanced table processing
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True  # Map structure to PDF cells
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE  # Use most accurate mode
    
    # Enhanced image processing
    pipeline_options.generate_picture_images = True     # Extract images
    pipeline_options.images_scale = 2                   # Higher resolution images
    
    # Enhanced OCR options
    pipeline_options.do_ocr = True
    pipeline_options.ocr_options = EasyOcrOptions(
        force_full_page_ocr=True,    # OCR entire pages when needed
        use_gpu=True                 # Use GPU if available
    )
    
    # Use Granite Vision model for picture descriptions (high quality)
    try:
        pipeline_options.picture_description_options = granite_picture_description
    except Exception as e:
        print(f"Warning: Failed to set granite_picture_description: {e}")
        from docling.datamodel.pipeline_options import PictureDescriptionVlmOptions
        pipeline_options.picture_description_options = PictureDescriptionVlmOptions(
            repo_id="ibm-granite/granite-vision-3.2-2b",
            prompt="Describe this image in detail, including any text, charts, diagrams, and visual elements.",
        )

    # Create converter with enhanced options
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
            InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipeline_options),
            InputFormat.PPTX: PowerpointFormatOption(pipeline_options=pipeline_options),
            InputFormat.DOCX: WordFormatOption(pipeline_options=pipeline_options),
        }
    )
    
    return converter

# Initialize the enhanced converter (this will download models on first use)
print("Initializing enhanced Docling converter with all enrichments...")
converter = create_enhanced_converter()
print("Enhanced converter ready!")

def handler(job):
    """Enhanced handler function with full document processing capabilities."""
    
    input_data = job.get('input', {})
    sources = input_data.get('sources', [])
    
    # Configuration options from input
    export_format = input_data.get('export_format', 'markdown')  # markdown, html, json, text
    max_pages = input_data.get('max_pages', None)
    max_file_size = input_data.get('max_file_size', 100 * 1024 * 1024)  # 100MB default
    include_images = input_data.get('include_images', True)
    
    if not sources:
        return {"error": "No sources provided", "status_code": 400}
    
    results = []
    
    for source in sources:
        if not source:
            results.append({"error": "Empty source", "source": source})
            continue
            
        try:
            print(f"Processing: {source}")
            
            # Download document
            with httpx.Client(timeout=60.0) as client:
                response = client.get(source)
                response.raise_for_status()
                
                # Create document stream
                stream = BytesIO(response.content)
                filename = source.split("/")[-1] if "/" in source else "document"
                doc_stream = DocumentStream(name=filename, stream=stream)
                
                # Convert with limits
                convert_kwargs = {}
                if max_pages:
                    convert_kwargs['max_num_pages'] = max_pages
                if max_file_size:
                    convert_kwargs['max_file_size'] = max_file_size
                
                print(f"Converting {filename} with enhanced pipeline...")
                result = converter.convert(doc_stream, **convert_kwargs)
                doc = result.document
                
                # Export in requested format
                if export_format.lower() == 'markdown':
                    output_content = doc.export_to_markdown()
                elif export_format.lower() == 'html':
                    output_content = doc.export_to_html()
                elif export_format.lower() == 'json':
                    output_content = doc.export_to_json()
                elif export_format.lower() == 'text':
                    output_content = doc.export_to_text()
                else:
                    output_content = doc.export_to_markdown()  # fallback
                
                # Collect processing metadata
                metadata = {
                    "source": source,
                    "filename": filename,
                    "page_count": len(doc.pages) if hasattr(doc, 'pages') else None,
                    "export_format": export_format,
                    "enrichments_applied": {
                        "code_enrichment": True,
                        "formula_enrichment": True,
                        "picture_classification": True,
                        "picture_description": True,
                        "table_structure": True,
                        "ocr": True
                    }
                }
                
                # Count enriched elements
                enrichment_stats = {
                    "code_blocks": 0,
                    "formulas": 0,
                    "images": 0,
                    "tables": 0
                }
                
                # Count different element types
                for item in doc.texts:
                    if hasattr(item, 'label'):
                        if item.label == 'FORMULA':
                            enrichment_stats["formulas"] += 1
                
                if hasattr(doc, 'pictures'):
                    enrichment_stats["images"] = len(doc.pictures)
                
                if hasattr(doc, 'tables'):
                    enrichment_stats["tables"] = len(doc.tables)
                    
                if hasattr(doc, 'code'):
                    enrichment_stats["code_blocks"] = len(doc.code)
                
                metadata["enrichment_stats"] = enrichment_stats
                
                results.append({
                    "content": output_content,
                    "metadata": metadata,
                    "status": "success"
                })
                
                print(f"Successfully processed {filename}")
                print(f"Stats: {enrichment_stats}")
                
        except httpx.RequestError as e:
            error_msg = f"HTTP request failed: {str(e)}"
            print(f"Error processing {source}: {error_msg}")
            results.append({
                "error": error_msg,
                "source": source,
                "status": "failed"
            })
            
        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            print(f"Error processing {source}: {error_msg}")
            results.append({
                "error": error_msg,
                "source": source,
                "status": "failed"
            })
    
    return {
        "output": results,
        "status_code": 200,
        "total_processed": len([r for r in results if r.get("status") == "success"]),
        "total_failed": len([r for r in results if r.get("status") == "failed"])
    }

# Prefetch models for faster cold starts (optional)
def prefetch_models():
    """Prefetch all models to avoid download delays during processing."""
    try:
        from docling.utils.model_downloader import download_models
        print("Prefetching all models...")
        download_models()
        print("Models prefetched successfully!")
    except Exception as e:
        print(f"Model prefetch failed (will download on demand): {e}")

# Uncomment to prefetch models during container startup
# prefetch_models()

print("Starting enhanced Docling serverless handler...")
runpod.serverless.start({"handler": handler})