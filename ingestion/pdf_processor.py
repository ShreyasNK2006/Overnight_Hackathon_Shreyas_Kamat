"""
Docling PDF Processor
Converts PDF to Markdown and extracts images
"""
import os
import uuid
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import logging

from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)


class DoclingProcessor:
    """
    Process PDF documents using Docling:
    1. Extract images and save to Supabase storage
    2. Convert document to Markdown
    3. Return markdown content with image references
    """
    
    def __init__(self, output_dir: str = "temp_markdown"):
        """
        Initialize Docling processor
        
        Args:
            output_dir: Directory to temporarily store markdown files
        """
        self.converter = DocumentConverter()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info("Docling processor initialized")
    
    def process_pdf(
        self, 
        pdf_path: str,
        doc_id: str = None
    ) -> Tuple[str, List[Dict], Dict]:
        """
        Process PDF document to extract markdown and images
        
        Args:
            pdf_path: Path to PDF file
            doc_id: Unique document identifier (generated if not provided)
            
        Returns:
            Tuple of (markdown_content, extracted_images, metadata)
            - markdown_content: Full markdown text with image placeholders
            - extracted_images: List of {image_bytes, image_path, page_num}
            - metadata: {source, total_pages, processed_at}
        """
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Convert PDF using Docling
        result = self.converter.convert(pdf_path)
        
        # Get markdown content
        markdown_content = result.document.export_to_markdown()
        
        # Extract images
        extracted_images = []
        for idx, picture in enumerate(result.document.pictures):
            image_data = {
                "image_bytes": picture.get_image().tobytes(),
                "image_path": f"{doc_id}/image_{idx}.png",
                "page_num": getattr(picture, 'page', idx + 1),  # Get page if available
                "format": "PNG"
            }
            extracted_images.append(image_data)
        
        # Create metadata
        metadata = {
            "source": Path(pdf_path).name,
            "doc_id": doc_id,
            "total_pages": len(result.document.pages) if hasattr(result.document, 'pages') else None,
            "processed_at": datetime.utcnow().isoformat(),
            "total_images": len(extracted_images)
        }
        
        # Save markdown to temp file for reference
        markdown_path = self.output_dir / f"{doc_id}.md"
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        logger.info(f"Processed PDF: {metadata['source']}, Images: {len(extracted_images)}")
        
        return markdown_content, extracted_images, metadata
