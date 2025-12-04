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
        prompt = f"""You are an expert at analyzing tables and extracting structured information for semantic search.

Context:
- Document: {metadata.get('source', 'Unknown')}
- Section: {metadata.get('section_header', 'Unknown')}

Table Content:
{table_markdown}

Your task: Create a comprehensive summary that captures ALL key information from this table.

Requirements:
1. Start with what the table represents (purpose/domain)
2. Extract ALL column headers and what they measure
3. List ALL rows with their key data points and values
4. Identify patterns, ranges, relationships between columns
5. Include specific numbers, units, categories, and identifiers
6. Preserve technical terms, acronyms, and domain-specific language
7. Make it searchable - someone should be able to find this table by querying any value or concept in it

Generate a detailed, information-dense summary (aim for 200-400 words) that preserves all searchable content:
"""
        
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
        prompt = f"""You are an expert at analyzing images and creating detailed descriptions for semantic search.

Context:
- Document: {metadata.get('source', 'Unknown')}
- Section: {metadata.get('section_header', 'Unknown')}
- Page: {metadata.get('page_num', 'Unknown')}
- Image URL: {image_url}

Your task: Analyze this image and create a comprehensive, searchable description.

Requirements:
1. Identify the type of image (photo, diagram, chart, blueprint, screenshot, etc.)
2. Describe ALL visible elements:
   - Objects, people, structures
   - Text, labels, annotations
   - Charts/graphs: axes, data points, trends
   - Diagrams: components, connections, flow
3. Extract ALL readable text verbatim
4. Describe colors, shapes, spatial relationships
5. Infer purpose and context from the surrounding section
6. Include technical terminology for infrastructure/engineering content
7. Make it searchable - preserve key terms, numbers, identifiers

Generate a detailed, information-dense description (aim for 200-400 words):
"""
        
        try:
            # Use Gemini Vision to analyze the actual image
            # Create a message with the image URL
            from langchain_core.messages import HumanMessage
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    }
                ]
            )
            
            response = self.llm.invoke([message])
            caption = response.content.strip()
            
            logger.debug(f"Generated image caption from vision API ({len(caption)} chars)")
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
