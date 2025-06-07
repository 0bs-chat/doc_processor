#!/usr/bin/env python3
"""
Model pre-download script for Docling
Downloads all models during Docker build to avoid cold start delays
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_docling_models():
    """Download all Docling models using the official downloader."""
    try:
        logger.info("Starting Docling model downloads...")
        
        # Use the official model downloader
        from docling.utils.model_downloader import download_models
        download_models()
        
        logger.info("✅ Official Docling models downloaded successfully")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Failed to import docling model downloader: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to download official models: {e}")
        return False

def download_vision_models():
    """Pre-download vision models for picture description."""
    try:
        logger.info("Pre-downloading vision models...")
        
        # Import and initialize the vision models to trigger download
        from transformers import AutoProcessor, AutoModelForVision2Seq
        import torch
        
        # Granite Vision model (used for picture descriptions)
        model_id = "ibm-granite/granite-vision-3.1-2b-preview"
        logger.info(f"Downloading {model_id}...")
        
        processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        model = AutoModelForVision2Seq.from_pretrained(
            model_id, 
            trust_remote_code=True,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        
        # Clear from memory
        del processor, model
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        logger.info("✅ Vision models downloaded successfully")
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️  Transformers not available, skipping vision models: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to download vision models: {e}")
        return False

def download_ocr_models():
    """Pre-download EasyOCR models."""
    try:
        logger.info("Pre-downloading OCR models...")
        
        import easyocr
        
        # Initialize EasyOCR reader (downloads models)
        reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available() if 'torch' in globals() else False)
        
        # Clear from memory
        del reader
        
        logger.info("✅ OCR models downloaded successfully")
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️  EasyOCR not available, skipping OCR models: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Failed to download OCR models: {e}")
        return False

def test_model_loading():
    """Test that we can initialize the enhanced converter without errors."""
    try:
        logger.info("Testing enhanced converter initialization...")
        
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import (
            PdfPipelineOptions,
            TableFormerMode,
            granite_picture_description
        )
        
        # Create the same enhanced pipeline as in handler
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_code_enrichment = True
        pipeline_options.do_formula_enrichment = True
        pipeline_options.do_picture_classification = True
        pipeline_options.do_picture_description = True
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
        pipeline_options.generate_picture_images = True
        pipeline_options.images_scale = 2
        pipeline_options.picture_description_options = granite_picture_description
        
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        
        logger.info("✅ Enhanced converter initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize enhanced converter: {e}")
        return False

def set_cache_permissions():
    """Set proper permissions for model cache directories."""
    try:
        cache_dirs = [
            Path.home() / ".cache" / "docling",
            Path.home() / ".cache" / "transformers",
            Path.home() / ".cache" / "torch",
            Path.home() / ".cache" / "easyocr"
        ]
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                os.chmod(cache_dir, 0o755)
                logger.info(f"Set permissions for {cache_dir}")
                
        return True
    except Exception as e:
        logger.warning(f"⚠️  Failed to set cache permissions: {e}")
        return False

def main():
    """Main function to download all models."""
    logger.info("🚀 Starting model pre-download process...")
    
    # Set environment variables for faster downloads
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    
    success_count = 0
    total_downloads = 4
    
    # Download official Docling models
    if download_docling_models():
        success_count += 1
    
    # Download vision models
    if download_vision_models():
        success_count += 1
    
    # Download OCR models
    if download_ocr_models():
        success_count += 1
    
    # Test converter initialization
    if test_model_loading():
        success_count += 1
    
    # Set cache permissions
    set_cache_permissions()
    
    # Summary
    logger.info(f"📊 Model download summary: {success_count}/{total_downloads} successful")
    
    if success_count == total_downloads:
        logger.info("🎉 All models downloaded successfully! Container ready for fast inference.")
        sys.exit(0)
    elif success_count > 0:
        logger.warning("⚠️  Some models downloaded successfully. Container will work but may have slower cold starts.")
        sys.exit(0)
    else:
        logger.error("❌ No models downloaded successfully. Container may have slow cold starts.")
        sys.exit(1)

if __name__ == "__main__":
    main()