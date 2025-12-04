"""
RAG Query System with Citations
Combines retrieval + Gemini generation with source attribution
"""
import logging
from typing import List, Dict, Any, Optional
from retrieval.hybrid_search import HybridRetriever
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings

logger = logging.getLogger(__name__)


class RAGQuerySystem:
    """
    End-to-end RAG system:
    1. Retrieve relevant chunks with timestamps
    2. Generate response using Gemini
    3. Include citations (page numbers, sources, sections)
    """
    
    def __init__(self):
        """Initialize retriever and LLM"""
        self.retriever = HybridRetriever()
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.2  # Low for factual responses
        )
        logger.info("RAG Query System initialized")
    
    def query(
        self,
        question: str,
        top_k: int = 5,
        include_tables: bool = True,
        include_images: bool = True
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG with citations
        
        Args:
            question: User's question
            top_k: Number of relevant chunks to retrieve
            include_tables: Include table results
            include_images: Include image results
        
        Returns:
            {
                "answer": Generated response with inline citations,
                "sources": List of source documents with metadata,
                "retrieved_chunks": Raw chunks used for generation
            }
        """
        logger.info(f"Processing query: '{question}'")
        
        # Step 1: Retrieve relevant chunks
        results = self.retriever.search(question, top_k=top_k)
        
        if not results:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "sources": [],
                "retrieved_chunks": []
            }
        
        # Step 2: Build context with source tracking
        context_with_citations = self._build_context(results)
        
        # Step 3: Generate response with citations
        answer = self._generate_answer(question, context_with_citations, results)
        
        # Step 4: Extract source metadata
        sources = self._extract_sources(results)
        
        return {
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": results
        }
    
    def _build_context(self, results: List[Dict[str, Any]]) -> str:
        """
        Build context string with source attribution markers
        
        Args:
            results: Retrieved chunks
        
        Returns:
            Context string with [Source N] markers
        """
        context_parts = []
        
        for i, result in enumerate(results, 1):
            metadata = result["metadata"]
            
            # Build source header
            source_info = f"[Source {i}]"
            source_details = []
            
            if metadata.get("source"):
                source_details.append(f"Document: {metadata['source']}")
            if metadata.get("page_num"):
                source_details.append(f"Page: {metadata['page_num']}")
            if metadata.get("section_header"):
                source_details.append(f"Section: {metadata['section_header']}")
            if metadata.get("uploaded_at"):
                source_details.append(f"Date: {metadata['uploaded_at']}")
            
            if source_details:
                source_info += " (" + ", ".join(source_details) + ")"
            
            # Add content
            content = result["parent_content"]
            
            context_parts.append(f"{source_info}\n{content}\n")
        
        return "\n---\n".join(context_parts)
    
    def _generate_answer(
        self,
        question: str,
        context: str,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Generate answer using Gemini with citation requirements
        
        Args:
            question: User's question
            context: Retrieved context with source markers
            results: Retrieved chunks for source mapping
        
        Returns:
            Answer with inline citations
        """
        # Build citation reference guide
        citation_guide = self._build_citation_guide(results)
        
        prompt = f"""You are a helpful assistant answering questions about infrastructure documentation.

CONTEXT (Retrieved from database with source markers):
{context}

CITATION GUIDE:
{citation_guide}

USER QUESTION:
{question}

INSTRUCTIONS:
1. Answer the question using ONLY the information provided in the context above
2. You MUST cite sources for every fact, claim, or piece of information you mention
3. Use inline citations in this format: [Source N] where N is the source number
4. If information comes from multiple sources, cite all: [Source 1, Source 2]
5. Include page numbers and sections when relevant: [Source 1, Page 5, Section 3]
6. If the context doesn't contain enough information to answer, say so clearly
7. Be specific and detailed, but concise
8. Preserve technical terminology and exact values from the sources

ANSWER (with citations):"""

        try:
            response = self.llm.invoke(prompt)
            answer = response.content.strip()
            
            logger.info("Generated answer with citations")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Error generating response: {str(e)}"
    
    def _build_citation_guide(self, results: List[Dict[str, Any]]) -> str:
        """
        Build a reference guide for citations
        
        Args:
            results: Retrieved chunks
        
        Returns:
            Formatted citation guide
        """
        guide_parts = []
        
        for i, result in enumerate(results, 1):
            metadata = result["metadata"]
            
            parts = [f"Source {i}:"]
            
            if metadata.get("source"):
                parts.append(f"'{metadata['source']}'")
            if metadata.get("page_num"):
                parts.append(f"(Page {metadata['page_num']})")
            if metadata.get("section_header"):
                parts.append(f"Section: {metadata['section_header']}")
            if metadata.get("type"):
                parts.append(f"[{metadata['type']}]")
            
            guide_parts.append(" ".join(parts))
        
        return "\n".join(guide_parts)
    
    def _extract_sources(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract clean source metadata for response
        
        Args:
            results: Retrieved chunks
        
        Returns:
            List of source metadata dictionaries
        """
        sources = []
        
        for i, result in enumerate(results, 1):
            metadata = result["metadata"]
            
            source = {
                "source_number": i,
                "document": metadata.get("source", "Unknown"),
                "page": metadata.get("page_num", "N/A"),
                "section": metadata.get("section_header", "N/A"),
                "type": metadata.get("type", "unknown"),
                "timestamp": metadata.get("uploaded_at", "N/A"),
                "similarity_score": result.get("similarity_score", 0.0)
            }
            
            sources.append(source)
        
        return sources
    
    def format_response(self, response: Dict[str, Any]) -> str:
        """
        Format the RAG response for display
        
        Args:
            response: Response from query()
        
        Returns:
            Formatted string for console/UI display
        """
        output = []
        
        output.append("=" * 70)
        output.append("ANSWER:")
        output.append("=" * 70)
        output.append(response["answer"])
        output.append("")
        
        if response["sources"]:
            output.append("=" * 70)
            output.append("SOURCES:")
            output.append("=" * 70)
            
            for source in response["sources"]:
                output.append(f"\n[Source {source['source_number']}]")
                output.append(f"  Document: {source['document']}")
                output.append(f"  Page: {source['page']}")
                output.append(f"  Section: {source['section']}")
                output.append(f"  Type: {source['type']}")
                output.append(f"  Timestamp: {source['timestamp']}")
                output.append(f"  Relevance: {source['similarity_score']:.3f}")
        
        return "\n".join(output)
