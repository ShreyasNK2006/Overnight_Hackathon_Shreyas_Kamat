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
        # Including H4 and H5 for more granular splitting
        self.headers_to_split_on = [
            ("#", "Header1"),
            ("##", "Header2"),
            ("###", "Header3"),
            ("####", "Header4"),
            ("#####", "Header5"),
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
        
        # Improved pattern to match markdown tables (including header row and separator)
        # Matches: | col1 | col2 |\n| --- | --- |\n| val1 | val2 |
        table_pattern = r'(?:^\|.+\|$\n)+(?:^\|[\s:-]+\|$\n)+(?:^\|.+\|$\n?)+'
        
        # Pattern to match markdown images  
        image_pattern = r'!\[.*?\]\(.*?\)'
        
        # Split content by lines to better handle tables
        lines = content.split('\n')
        current_chunk = []
        current_type = None
        in_table = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this is an image line
            if re.match(image_pattern, line.strip()):
                # Save current chunk if exists
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk).strip()
                    if chunk_text:
                        chunks.append({"content": chunk_text, "type": current_type or "text"})
                    current_chunk = []
                    current_type = None
                
                # Add image as separate chunk
                chunks.append({"content": line.strip(), "type": "image"})
                i += 1
                continue
            
            # Check if this line is part of a table
            is_table_line = bool(re.match(r'^\s*\|.*\|\s*$', line))
            
            if is_table_line:
                if not in_table:
                    # Starting a new table - save previous chunk
                    if current_chunk:
                        chunk_text = '\n'.join(current_chunk).strip()
                        if chunk_text:
                            chunks.append({"content": chunk_text, "type": current_type or "text"})
                        current_chunk = []
                    
                    in_table = True
                    current_type = "table"
                
                current_chunk.append(line)
            else:
                # Not a table line
                if in_table:
                    # Table ended - save it
                    if current_chunk:
                        chunk_text = '\n'.join(current_chunk).strip()
                        if chunk_text:
                            chunks.append({"content": chunk_text, "type": "table"})
                        current_chunk = []
                    
                    in_table = False
                    current_type = "text"
                
                # Add to text chunk only if not empty/whitespace
                if line.strip():
                    if current_type != "text":
                        # Save previous chunk if switching types
                        if current_chunk:
                            chunk_text = '\n'.join(current_chunk).strip()
                            if chunk_text:
                                chunks.append({"content": chunk_text, "type": current_type or "text"})
                            current_chunk = []
                    
                    current_type = "text"
                    current_chunk.append(line)
            
            i += 1
        
        # Save any remaining chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk).strip()
            if chunk_text:
                chunks.append({"content": chunk_text, "type": current_type or "text"})
        
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
            header_metadata: Dict with Header1, Header2, Header3, Header4, Header5 keys
            
        Returns:
            Combined section header string
        """
        headers = []
        for key in ['Header1', 'Header2', 'Header3', 'Header4', 'Header5']:
            if key in header_metadata and header_metadata[key]:
                headers.append(header_metadata[key])
        
        return ' > '.join(headers) if headers else 'No Header'
