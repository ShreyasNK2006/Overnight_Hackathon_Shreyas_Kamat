"""
Text Splitter for Child Nodes
Recursively splits text into small searchable chunks
"""
import logging
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config.settings import settings

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Split text content into child nodes using recursive character splitting
    Creates small, searchable chunks for vector embeddings
    """
    
    def __init__(self):
        """Initialize recursive text splitter"""
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.TEXT_CHUNK_SIZE,
            chunk_overlap=settings.TEXT_CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len
        )
        
        logger.info(
            f"Text chunker initialized (size={settings.TEXT_CHUNK_SIZE}, "
            f"overlap={settings.TEXT_CHUNK_OVERLAP})"
        )
    
    def chunk_text(
        self, 
        text_content: str,
        parent_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Split text into small chunks for child vectors
        
        Args:
            text_content: Text to split
            parent_metadata: Metadata from parent node to copy
        
        Returns:
            List of child chunks with:
            - content: Small text snippet
            - metadata: Copied from parent
        """
        # Skip if content is too short
        if len(text_content.strip()) < 50:
            logger.debug("Content too short, returning as single chunk")
            return [{
                "content": text_content.strip(),
                "metadata": parent_metadata
            }]
        
        # Split text into chunks
        chunks = self.splitter.split_text(text_content)
        
        child_nodes = []
        for idx, chunk in enumerate(chunks):
            child_node = {
                "content": chunk,
                "metadata": {
                    **parent_metadata,
                    "child_chunk_index": idx,
                    "total_child_chunks": len(chunks)
                }
            }
            child_nodes.append(child_node)
        
        logger.debug(f"Split text into {len(child_nodes)} child chunks")
        return child_nodes
