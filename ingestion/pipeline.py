"""
Main Ingestion Pipeline
Orchestrates the entire document processing workflow
"""
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from ingestion.pdf_processor import DoclingProcessor
from ingestion.markdown_splitter import MarkdownSplitter
from ingestion.text_chunker import TextChunker
from ingestion.multimodal_handler import MultimodalHandler
from retrieval.embeddings import get_embedding_model
from database.supabase_client import get_supabase_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Complete ingestion pipeline:
    1. PDF → Docling → Markdown + Images
    2. Markdown → Header Splitter → Parent Nodes (text/table/image sections)
    3. Text Nodes → Recursive Splitter → Child Chunks → Embeddings
    4. Table Nodes → Gemini Summary → Child Vector
    5. Image Nodes → Upload to Storage → Gemini Caption → Child Vector
    6. Store all in Supabase (parent_docs + child_vectors)
    """
    
    def __init__(self):
        """Initialize all pipeline components"""
        self.pdf_processor = DoclingProcessor()
        self.markdown_splitter = MarkdownSplitter()
        self.text_chunker = TextChunker()
        self.multimodal_handler = MultimodalHandler()
        self.embedding_model = get_embedding_model()
        self.db_client = get_supabase_client()
        
        logger.info("Ingestion pipeline initialized")
    
    def ingest_document(self, pdf_path: str) -> Dict[str, Any]:
        """
        Complete document ingestion workflow
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Statistics about ingestion (parent_count, child_count, images_uploaded)
        """
        logger.info(f"Starting ingestion for: {pdf_path}")
        stats = {
            "source": Path(pdf_path).name,
            "parent_nodes": 0,
            "child_vectors": 0,
            "images_uploaded": 0,
            "tables_processed": 0,
            "text_sections": 0,
            "doc_id": None,
            "total_pages": None
        }
        
        # ===== STEP 1: PDF → Markdown + Images =====
        markdown_content, extracted_images, base_metadata = \
            self.pdf_processor.process_pdf(pdf_path)
        
        # Add document ID and page count to stats
        stats["doc_id"] = base_metadata.get("doc_id")
        stats["total_pages"] = base_metadata.get("total_pages")
        
        # Add upload timestamp for temporal conflict resolution
        upload_timestamp = datetime.utcnow().isoformat()
        base_metadata["uploaded_at"] = upload_timestamp
        
        # ===== STEP 2: Upload Images to Supabase Storage =====
        image_url_map = {}  # Map image_path to public_url
        for image_data in extracted_images:
            try:
                public_url = self.db_client.upload_image(
                    file_path=image_data["image_path"],
                    file_bytes=image_data["image_bytes"]
                )
                image_url_map[image_data["image_path"]] = public_url
                stats["images_uploaded"] += 1
                
                logger.debug(f"Uploaded image: {image_data['image_path']}")
            except Exception as e:
                logger.error(f"Failed to upload image {image_data['image_path']}: {e}")
        
        # ===== STEP 2.5: Replace image paths in markdown with Supabase URLs =====
        markdown_content = self._replace_image_urls(markdown_content, image_url_map)
        
        # ===== STEP 3: Split Markdown into Parent Nodes =====
        parent_nodes = self.markdown_splitter.split_markdown(
            markdown_content, 
            base_metadata
        )
        
        # ===== STEP 4: Process Each Parent Node =====
        for parent_node in parent_nodes:
            try:
                self._process_parent_node(parent_node, upload_timestamp, stats)
            except Exception as e:
                logger.error(f"Error processing parent node: {e}")
                continue
        
        logger.info(
            f"Ingestion complete: {stats['parent_nodes']} parents, "
            f"{stats['child_vectors']} children, {stats['images_uploaded']} images"
        )
        
        return stats
    
    def _process_parent_node(
        self, 
        parent_node: Dict[str, Any],
        upload_timestamp: str,
        stats: Dict[str, Any]
    ):
        """
        Process a single parent node and create child vectors
        
        Args:
            parent_node: Node with content, metadata, type
            upload_timestamp: ISO timestamp for conflict resolution
            stats: Statistics dict to update
        """
        content = parent_node["content"]
        metadata = parent_node["metadata"]
        node_type = parent_node["type"]
        
        # Insert parent document
        parent_id = self.db_client.insert_parent_doc(
            content=content,
            metadata=metadata,
            source_created_at=upload_timestamp
        )
        stats["parent_nodes"] += 1
        
        # Create child vectors for all types
        # Text: recursive split into chunks
        # Tables: Gemini-generated summary
        # Images: Gemini-generated caption
        if node_type == "text":
            self._process_text_node(content, metadata, parent_id, stats)
        elif node_type == "table":
            self._process_table_node(content, metadata, parent_id, stats)
        elif node_type == "image":
            self._process_image_node(content, metadata, parent_id, stats)
    
    def _process_text_node(
        self,
        content: str,
        metadata: Dict[str, Any],
        parent_id: str,
        stats: Dict[str, Any]
    ):
        """Process text node: recursive split → embed → store"""
        # Split into child chunks
        child_chunks = self.text_chunker.chunk_text(content, metadata)
        
        # Embed and store each chunk
        for chunk in child_chunks:
            embedding = self.embedding_model.embed_text(chunk["content"])
            
            self.db_client.insert_child_vector(
                content=chunk["content"],
                embedding=embedding,
                parent_id=parent_id,
                metadata=chunk["metadata"]
            )
            stats["child_vectors"] += 1
        
        stats["text_sections"] += 1
        logger.debug(f"Processed text node: {len(child_chunks)} child chunks")
    
    def _process_table_node(
        self,
        content: str,
        metadata: Dict[str, Any],
        parent_id: str,
        stats: Dict[str, Any]
    ):
        """Process table node: generate summary → embed → store"""
        # Generate natural language summary
        summary = self.multimodal_handler.summarize_table(content, metadata)
        
        # Embed summary
        embedding = self.embedding_model.embed_text(summary)
        
        # Store child vector with summary
        self.db_client.insert_child_vector(
            content=summary,
            embedding=embedding,
            parent_id=parent_id,
            metadata=metadata
        )
        
        stats["child_vectors"] += 1
        stats["tables_processed"] += 1
        logger.debug(f"Processed table node with summary")
    
    def _process_image_node(
        self,
        content: str,
        metadata: Dict[str, Any],
        parent_id: str,
        stats: Dict[str, Any]
    ):
        """Process image node: extract URL → generate caption → embed → store"""
        # Extract image URL from markdown
        image_url = self._extract_image_url(content)
        
        if not image_url:
            logger.warning("Could not extract image URL from content")
            return
        
        # Generate caption using actual image via Gemini Vision
        caption = self.multimodal_handler.generate_image_caption(
            image_url=image_url,
            metadata=metadata
        )
        
        # Embed caption
        embedding = self.embedding_model.embed_text(caption)
        
        # Store child vector with caption
        self.db_client.insert_child_vector(
            content=caption,
            embedding=embedding,
            parent_id=parent_id,
            metadata=metadata
        )
        
        stats["child_vectors"] += 1
        logger.debug(f"Processed image node with caption")
    
    def _extract_image_url(self, markdown_image: str) -> str:
        """Extract URL from markdown image syntax: ![alt](url)"""
        try:
            start = markdown_image.find('](') + 2
            end = markdown_image.find(')', start)
            return markdown_image[start:end]
        except:
            return ""
    
    def _replace_image_urls(
        self, 
        markdown_content: str, 
        image_url_map: Dict[str, str]
    ) -> str:
        """
        Replace local image paths in markdown with Supabase public URLs
        
        Args:
            markdown_content: Original markdown with local image paths
            image_url_map: Mapping of {local_path: supabase_url}
        
        Returns:
            Updated markdown with Supabase URLs
        """
        import re
        
        # Pattern to match markdown images: ![alt text](image_path)
        pattern = r'!\[(.*?)\]\((.*?)\)'
        
        def replace_url(match):
            alt_text = match.group(1)
            original_path = match.group(2)
            
            # Check if this path is in our uploaded images map
            for local_path, supabase_url in image_url_map.items():
                # Match by filename or full path
                if original_path in local_path or local_path.endswith(original_path):
                    logger.debug(f"Replacing {original_path} with {supabase_url}")
                    return f'![{alt_text}]({supabase_url})'
            
            # If no match found, return original
            return match.group(0)
        
        updated_markdown = re.sub(pattern, replace_url, markdown_content)
        return updated_markdown


def main():
    """Example usage"""
    # Create pipeline
    pipeline = IngestionPipeline()
    
    # Process a PDF
    pdf_path = "path/to/your/document.pdf"
    stats = pipeline.ingest_document(pdf_path)
    
    print("\n" + "="*50)
    print("INGESTION COMPLETE")
    print("="*50)
    print(f"Source: {stats['source']}")
    print(f"Parent Nodes: {stats['parent_nodes']}")
    print(f"Child Vectors: {stats['child_vectors']}")
    print(f"Images Uploaded: {stats['images_uploaded']}")
    print(f"Tables Processed: {stats['tables_processed']}")
    print(f"Text Sections: {stats['text_sections']}")
    print("="*50)


if __name__ == "__main__":
    main()
