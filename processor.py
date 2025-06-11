import httpx
from io import BytesIO
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.io import DocumentStream
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableFormerMode,
    EasyOcrOptions,
    smolvlm_picture_description
)
import os

AUTO_DETECT_PLATFORMS = os.getenv("AUTO_DETECT_PLATFORMS", "false").lower() == "true"
DEVICE_CAPABILITY = os.getenv("DEVICE_CAPABILITY", "high").lower()

VALID_CAPABILITIES = {"low", "medium", "high"}
if DEVICE_CAPABILITY not in VALID_CAPABILITIES:
    print(f"[Doc Processor] Unknown DEVICE_CAPABILITY='{DEVICE_CAPABILITY}', falling back to 'high'.")
    DEVICE_CAPABILITY = "high"

def _build_pdf_options(capability: str) -> PdfFormatOption:
    """Return a PdfFormatOption tuned for *capability* tier."""

    pipeline_options = PdfPipelineOptions()

    if capability == "low":
        # Disable the heaviest enrichments to minimise CPU/GPU & memory usage.
        pipeline_options.do_code_enrichment = False
        pipeline_options.do_formula_enrichment = False
        pipeline_options.generate_picture_images = False
        pipeline_options.do_picture_classification = False
        pipeline_options.do_picture_description = False
        pipeline_options.do_table_structure = False
        pipeline_options.do_ocr = False
    elif capability == "medium":
        # Keep most textual enrichments but skip vision heavy ones.
        pipeline_options.do_code_enrichment = True
        pipeline_options.do_formula_enrichment = True
        pipeline_options.generate_picture_images = False  # skip PNG rendering
        pipeline_options.do_picture_classification = False
        pipeline_options.do_picture_description = False
        pipeline_options.do_table_structure = True
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options = EasyOcrOptions(
            force_full_page_ocr=False,
            use_gpu=False,
        )
    else:  # "high"
        # Full-fat experience with all enrichments switched on.
        pipeline_options.do_code_enrichment = True
        pipeline_options.do_formula_enrichment = True
        pipeline_options.generate_picture_images = True
        pipeline_options.images_scale = 2
        pipeline_options.do_picture_classification = True
        pipeline_options.do_picture_description = True
        pipeline_options.picture_description_options = smolvlm_picture_description
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options = EasyOcrOptions(
            force_full_page_ocr=True,
            use_gpu=True,
        )

    return PdfFormatOption(pipeline_options=pipeline_options)

def create_converter() -> DocumentConverter:
    """Create a DocumentConverter configured from environment variables."""

    pdf_option = _build_pdf_options(DEVICE_CAPABILITY)

    if AUTO_DETECT_PLATFORMS:
        # Let Docling figure out the appropriate pipeline for each file type.
        return DocumentConverter()
    else:
        # Restrict to PDF only with the prepared options.
        return DocumentConverter(format_options={InputFormat.PDF: pdf_option})

converter = create_converter()

def handler(source: str):
    """Enhanced handler function with full document processing capabilities."""
    
    # Configuration options from input
    export_format = 'markdown'  # markdown, html, json, text
    max_pages = None
    max_file_size = 100 * 1024 * 1024  # 100MB default

    result = None
    try:
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
            
            print(f"Converting {filename} with {DEVICE_CAPABILITY} capability pipeline...")
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
            # Flag which enrichments were *actually* enabled based on DEVICE_CAPABILITY
            enrichment_flags = {
                "low": {
                    "code_enrichment": False,
                    "formula_enrichment": False,
                    "picture_classification": False,
                    "picture_description": False,
                    "table_structure": False,
                    "ocr": False,
                },
                "medium": {
                    "code_enrichment": True,
                    "formula_enrichment": True,
                    "picture_classification": False,
                    "picture_description": False,
                    "table_structure": True,
                    "ocr": True,
                },
                "high": {
                    "code_enrichment": True,
                    "formula_enrichment": True,
                    "picture_classification": True,
                    "picture_description": True,
                    "table_structure": True,
                    "ocr": True,
                },
            }

            metadata = {
                "source": source,
                "filename": filename,
                "page_count": len(doc.pages) if hasattr(doc, 'pages') else None,
                "export_format": export_format,
                "device_capability": DEVICE_CAPABILITY,
                "enrichments_applied": enrichment_flags[DEVICE_CAPABILITY],
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
            
            result = {
                "content": output_content,
                "metadata": metadata,
                "status": "success"
            }
            
    except httpx.RequestError as e:
        raise Exception(f"HTTP request failed: {str(e)}")
        
    except Exception as e:
        raise Exception(f"Processing failed: {str(e)}")
    
    return result