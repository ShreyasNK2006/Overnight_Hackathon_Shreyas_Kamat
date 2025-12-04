"""
Example: How Metadata is Used in RAG Retrieval
"""
from database.supabase_client import get_supabase_client
from retrieval.embeddings import get_embedding_model

def demonstrate_metadata_usage():
    """Show practical examples of metadata usage"""
    
    print("="*70)
    print("METADATA USAGE DEMONSTRATION")
    print("="*70)
    
    client = get_supabase_client()
    embedding_model = get_embedding_model()
    
    # Example query
    query = "Show me images from math document"
    
    print(f"\n🔍 User Query: '{query}'")
    print("\n" + "="*70)
    print("STEP 1: Vector Search (Using child_vectors)")
    print("="*70)
    
    # Embed the query
    query_embedding = embedding_model.embed_text(query)
    print(f"✅ Query embedded ({len(query_embedding)} dimensions)")
    
    # Search child vectors
    results = client.search_similar_vectors(
        query_embedding=query_embedding,
        top_k=3,
        threshold=0.3
    )
    
    print(f"\n✅ Found {len(results)} similar documents")
    
    print("\n" + "="*70)
    print("STEP 2: Use Metadata to Build Context")
    print("="*70)
    
    for i, result in enumerate(results, 1):
        print(f"\n--- Result #{i} ---")
        
        # Extract metadata
        metadata = result.get('parent_metadata', {})
        parent_content = result.get('parent_content', '')
        similarity = result.get('similarity', 0)
        
        print(f"📊 Similarity Score: {similarity:.3f}")
        print(f"\n📝 METADATA EXTRACTED:")
        print(f"   Source: {metadata.get('source', 'N/A')}")
        print(f"   Type: {metadata.get('type', 'N/A')}")
        print(f"   Section: {metadata.get('section_header', 'N/A')}")
        print(f"   Uploaded: {metadata.get('uploaded_at', 'N/A')}")
        
        # Show how metadata is used
        print(f"\n💡 HOW METADATA IS USED:")
        
        # Use Case 1: Source Citation
        source = metadata.get('source', 'Unknown')
        page = metadata.get('page_num', 'N/A')
        print(f"   1. Citation: [Source: {source}, Page: {page}]")
        
        # Use Case 2: Content Type Handling
        content_type = metadata.get('type', 'text')
        if content_type == 'image':
            print(f"   2. Image Handling: Extract and display image URL")
            # Extract URL from parent_content
            import re
            match = re.search(r'https://[^\s\)]+', parent_content)
            if match:
                url = match.group(0)
                print(f"      Image URL: {url[:60]}...")
        elif content_type == 'table':
            print(f"   2. Table Handling: Preserve markdown formatting")
        else:
            print(f"   2. Text Handling: Display as plain text")
        
        # Use Case 3: Timestamp for versioning
        uploaded = metadata.get('uploaded_at', 'N/A')
        print(f"   3. Versioning: Document uploaded at {uploaded}")
        
        # Use Case 4: Section context
        section = metadata.get('section_header', 'No Header')
        print(f"   4. Context: From section '{section}'")
        
        print(f"\n📄 Parent Content Preview:")
        print(f"   {parent_content[:150]}...")
    
    print("\n" + "="*70)
    print("STEP 3: Generate LLM Response with Metadata")
    print("="*70)
    
    # Build context with metadata
    context_parts = []
    for result in results:
        metadata = result.get('parent_metadata', {})
        content = result.get('parent_content', '')
        
        # Format with metadata for LLM
        context_part = f"""
[Source: {metadata.get('source', 'Unknown')}]
[Type: {metadata.get('type', 'text')}]
[Section: {metadata.get('section_header', 'N/A')}]
[Uploaded: {metadata.get('uploaded_at', 'N/A')}]

Content:
{content}
"""
        context_parts.append(context_part)
    
    full_context = "\n---\n".join(context_parts)
    
    print("\n📋 Context sent to LLM:")
    print(full_context[:500] + "...\n")
    
    print("="*70)
    print("EXAMPLE LLM RESPONSE:")
    print("="*70)
    
    # Simulated LLM response using metadata
    print(f"""
Based on the documents, I found the following images from the math document:

1. Image from MATHS_CIE1.docx
   - URL: [Image Link]
   - Uploaded: {results[0].get('parent_metadata', {}).get('uploaded_at', 'N/A')}
   - This image contains mathematical formulas and diagrams.
   
[Source: MATHS_CIE1.docx, Uploaded: {results[0].get('parent_metadata', {}).get('uploaded_at', 'N/A')}]
    """)
    
    print("\n" + "="*70)
    print("KEY TAKEAWAYS:")
    print("="*70)
    print("""
1. ✅ Metadata enables SOURCE CITATION
   → Users know where info came from
   
2. ✅ Metadata enables CONTENT TYPE HANDLING
   → Images, tables, text handled differently
   
3. ✅ Metadata enables TEMPORAL AWARENESS
   → Can identify latest versions
   
4. ✅ Metadata enables CONTEXT PRESERVATION
   → Sections and structure maintained
   
5. ✅ Metadata enables FILTERING
   → Can query specific doc types or sources
    """)


if __name__ == "__main__":
    demonstrate_metadata_usage()
