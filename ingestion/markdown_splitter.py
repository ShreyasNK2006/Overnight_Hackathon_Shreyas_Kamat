"""
Markdown Splitter for Parent Nodes
Splits markdown into logical sections based on headers,
then further splits each section to separate text, tables, and images
"""

import logging
import re
from typing import List, Dict, Any
from langchain_text_splitters import MarkdownHeaderTextSplitter

logger = logging.getLogger(__name__)


class MarkdownSplitter:
    """
    Split markdown content into parent nodes:
    1. First split by headers (logical sections)
    2. Within each section, separate text, tables, and images
    """
    
    def __init__(self):
        """Initialize markdown header splitter"""
        # Split on markdown headers to preserve logical sections
        self.headers_to_split_on = [
            ("#", "Header1"),
            ("##", "Header2"),
            ("###", "Header3"),
        ]
        
        self.splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False  # Keep headers in the content
        )
        
        logger.info("Markdown splitter initialized")
    
    def split_markdown(
        self, 
        markdown_content: str,
        base_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Split markdown into parent nodes:
        1. Split by headers (sections)
        2. Within each section, separate text, tables, and images
        
        Args:
            markdown_content: Full markdown document
            base_metadata: Base metadata to attach to each chunk
                          {source, doc_id, processed_at}
        
        Returns:
            List of parent nodes with:
            - content: Separate chunks for text/table/image
            - metadata: Enhanced with section_header, type
            - type: 'text', 'table', or 'image'
        """
        # Step 1: Split by headers
        splits = self.splitter.split_text(markdown_content)
        
        parent_nodes = []
        chunk_index = 0
        
        for split in splits:
            section_content = split.page_content
            header_metadata = split.metadata
            section_header = self._extract_section_header(header_metadata)
            
            # Step 2: Within this section, separate text, tables, and images
            sub_chunks = self._split_section_content(section_content)
            
            for sub_chunk in sub_chunks:
                metadata = {
                    **base_metadata,
                    "chunk_index": chunk_index,
                    "section_header": section_header,
                    "type": sub_chunk["type"]
                }
                
                parent_node = {
                    "content": sub_chunk["content"],
                    "metadata": metadata,
                    "type": sub_chunk["type"]
                }
                
                parent_nodes.append(parent_node)
                chunk_index += 1
            
        logger.info(f"Split markdown into {len(parent_nodes)} parent nodes")
        return parent_nodes
    
    def _split_section_content(self, content: str) -> List[Dict[str, str]]:
        """
        Split a section into separate text, table, and image chunks
        
        Args:
            content: Section content (may contain mixed text/tables/images)
        
        Returns:
            List of {content, type} dicts
        """
        chunks = []
        
        # Pattern to match markdown tables
        table_pattern = r'(\|.+\|[\r\n]+\|[\s:-]+\|[\r\n]+(?:\|.+\|[\r\n]*)+)'
        
        # Pattern to match markdown images  
        image_pattern = r'(!\[.*?\]\(.*?\))'
        
        # Combine patterns
        combined_pattern = f'({table_pattern}|{image_pattern})'
        
        # Split content by tables and images
        parts = re.split(combined_pattern, content, flags=re.MULTILINE)
        
        for part in parts:
            if not part or not part.strip():
                continue
            
            # Determine what this part is
            if re.match(table_pattern, part.strip(), re.MULTILINE):
                chunks.append({"content": part.strip(), "type": "table"})
            elif re.match(image_pattern, part.strip()):
                chunks.append({"content": part.strip(), "type": "image"})
            else:
                # It's text - but skip if it's just whitespace or table separators
                clean_text = part.strip()
                if clean_text and not re.match(r'^[\s\-|:]+$', clean_text):
                    chunks.append({"content": clean_text, "type": "text"})
        
        # If no chunks found, treat entire content as text
        if not chunks:
            chunks.append({"content": content.strip(), "type": "text"})
        
        return chunks
    
    def _determine_content_type(self, content: str) -> str:
        """
        Determine if content is text, table, or image
        
        Args:
            content: Section content
            
        Returns:
            'text', 'table', or 'image'
        """
        # Check for table (markdown table format)
        if '|' in content and ('---' in content or '|-' in content):
            return 'table'
        
        # Check for image (markdown image format)
        if '![' in content and '](' in content:
            return 'image'
        
        # Default to text
        return 'text'
    
    def _extract_section_header(self, header_metadata: Dict) -> str:
        """
        Extract section header from metadata
        
        Args:
            header_metadata: Dict with Header1, Header2, Header3 keys
            
        Returns:
            Combined section header string
        """
        headers = []
        for key in ['Header1', 'Header2', 'Header3']:
            if key in header_metadata and header_metadata[key]:
                headers.append(header_metadata[key])
        
        return ' > '.join(headers) if headers else 'No Header'
