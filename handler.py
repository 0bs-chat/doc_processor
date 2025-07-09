import runpod
import os
from processor import handler as process_handler

def handler(job):
    """
    RunPod serverless handler for document processing.
    
    Expected input format:
    {
        "input": {
            "document_url": "https://example.com/document.pdf",
            "export_format": "markdown",  # optional: markdown, html, json, text
            "max_pages": 10,              # optional: limit number of pages
            "max_file_size": 104857600    # optional: max file size in bytes (100MB default)
        }
    }
    
    Returns:
    {
        "content": "processed document content",
        "metadata": {...},
        "status": "success"
    }
    """
    try:
        print(f"[RunPod Handler] Starting job {job['id']}")
        job_input = job["input"]
        
        # Extract document URL (required)
        document_url = job_input.get("document_url")
        if not document_url:
            return {"error": "document_url is required"}
        
        print(f"[RunPod Handler] Processing document: {document_url}")
        
        # Use the existing processor handler
        result = process_handler(document_url)
        
        print(f"[RunPod Handler] Job {job['id']} completed successfully")
        return result
        
    except Exception as e:
        error_msg = f"Document processing failed: {str(e)}"
        print(f"[RunPod Handler] Error in job {job['id']}: {error_msg}")
        return {"error": error_msg, "status": "failed"}

# Start the RunPod serverless worker
if __name__ == "__main__":
    print("Starting RunPod Document Processor Worker...")
    runpod.serverless.start({"handler": handler}) 