"""
Multimodal Handler for Tables and Images
Uses Gemini to generate natural language summaries
"""
import logging
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings

logger = logging.getLogger(__name__)

class MultimodalHandler:
    """
    Generate natural language summaries for tables and images
    using Gemini's multimodal capabilities
    """
    
    def __init__(self):
        """Initialize Gemini model for multimodal processing"""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1  # Low temperature for consistent summaries
        )
        
        logger.info(f"Multimodal handler initialized with {settings.GEMINI_MODEL}")
    
    def summarize_table(self, table_markdown: str, metadata: Dict[str, Any]) -> str:
        """
        Generate natural language summary of a markdown table
        
        Args:
            table_markdown: Markdown table content
            metadata: Context information (source, section_header)
        
        Returns:
            Natural language summary for vector search
        """
        prompt = f"""
You are summarizing a table from a document for search purposes.

Document: {metadata.get('source', 'Unknown')}
Section: {metadata.get('section_header', 'Unknown')}

Table:
{table_markdown}

Generate a detailed natural language summary that:
1. Describes what the table contains
2. Lists all key information, values, and relationships
3. Includes specific numbers, names, and details
4. Is optimized for semantic search

Summary:"""
        
        try:
            response = self.llm.invoke(prompt)
            summary = response.content.strip()
            
            logger.debug(f"Generated table summary ({len(summary)} chars)")
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing table: {e}")
            # Fallback: return table as-is
            return f"Table from {metadata.get('source')}: {table_markdown[:200]}..."
    
    def generate_image_caption(
        self, 
        image_url: str, 
        metadata: Dict[str, Any]
    ) -> str:
        """
        Generate descriptive caption for an image
        
        Args:
            image_url: Public URL of the image
            metadata: Context information (source, section_header, page_num)
        
        Returns:
            Detailed caption for vector search
        """
        prompt = f"""
You are describing an image from a document for search purposes.

Document: {metadata.get('source', 'Unknown')}
Section: {metadata.get('section_header', 'Unknown')}
Page: {metadata.get('page_num', 'Unknown')}

Describe this image in detail for search purposes. Include:
1. What objects, text, or diagrams are visible
2. Colors, shapes, and layout
3. The purpose or context of the image
4. Any text visible in the image
5. Technical details if it's a blueprint, diagram, or chart

Be specific and detailed. This description will be used for semantic search.

Description:"""
        
        try:
            # For now, use text-only model
            # In production, you'd use Gemini Vision API with the actual image
            response = self.llm.invoke(prompt)
            caption = response.content.strip()
            
            logger.debug(f"Generated image caption ({len(caption)} chars)")
            return caption
            
        except Exception as e:
            logger.error(f"Error generating image caption: {e}")
            # Fallback caption
            return (
                f"Image from {metadata.get('source')} "
                f"(Page {metadata.get('page_num', 'N/A')}, "
                f"Section: {metadata.get('section_header', 'N/A')})"
            )
    
    def generate_caption_from_context(
        self, 
        image_markdown: str,
        surrounding_text: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Generate image caption using surrounding text context
        (Alternative when direct image analysis isn't available)
        
        Args:
            image_markdown: Markdown image syntax with alt text
            surrounding_text: Text before/after the image
            metadata: Context information
        
        Returns:
            Caption based on context
        """
        # Extract alt text from markdown
        alt_text = ""
        if '![' in image_markdown and ']' in image_markdown:
            start = image_markdown.find('![') + 2
            end = image_markdown.find(']', start)
            alt_text = image_markdown[start:end]
        
        prompt = f"""
You are creating a searchable description for an image in a document.

Document: {metadata.get('source', 'Unknown')}
Section: {metadata.get('section_header', 'Unknown')}
Image Alt Text: {alt_text}

Context (surrounding text):
{surrounding_text[:500]}

Based on the alt text and surrounding context, generate a detailed description 
of what this image likely shows. Include technical details if relevant.

Description:"""
        
        try:
            response = self.llm.invoke(prompt)
            caption = response.content.strip()
            
            logger.debug(f"Generated context-based caption ({len(caption)} chars)")
            return caption
            
        except Exception as e:
            logger.error(f"Error generating context-based caption: {e}")
            return f"Image: {alt_text} from {metadata.get('source')}"
