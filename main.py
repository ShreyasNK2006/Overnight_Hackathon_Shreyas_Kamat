"""
Main Application - Infrastructure RAG System
Complete pipeline: Ingestion → Retrieval → Generation with Citations
"""
import sys
import argparse
from ingestion.pipeline import IngestionPipeline
from retrieval.rag_query import RAGQuerySystem

def ingest_document(pdf_path: str):
    """Ingest a document into the system"""
    print("\n" + "=" * 70)
    print("DOCUMENT INGESTION")
    print("=" * 70)
    print(f"Document: {pdf_path}\n")
    
    pipeline = IngestionPipeline()
    stats = pipeline.ingest_document(pdf_path)
    
    print("\n✅ INGESTION COMPLETE!")
    print(f"   Parent Nodes: {stats['parent_nodes']}")
    print(f"   Child Vectors: {stats['child_vectors']}")
    print(f"   Tables: {stats['tables_processed']}")
    print(f"   Text Sections: {stats['text_sections']}")
    print(f"   Images: {stats['images_uploaded']}")
    print("=" * 70)

def query_system(question: str):
    """Query the system and get answer with citations"""
    print("\n" + "=" * 70)
    print("RAG QUERY")
    print("=" * 70)
    print(f"Question: {question}\n")
    
    rag = RAGQuerySystem()
    response = rag.query(question, top_k=5)
    
    print("\n" + rag.format_response(response))
    print("=" * 70)

def interactive_mode():
    """Interactive query mode"""
    print("\n" + "=" * 70)
    print("INTERACTIVE RAG SYSTEM")
    print("=" * 70)
    print("Type your questions (or 'exit' to quit)\n")
    
    rag = RAGQuerySystem()
    
    while True:
        try:
            question = input("\n📝 Question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            print("\n🔍 Searching...")
            response = rag.query(question, top_k=5)
            
            print("\n" + rag.format_response(response))
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Infrastructure RAG System - Ingest documents and query with citations"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest a document')
    ingest_parser.add_argument('pdf_path', help='Path to PDF/DOCX file')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query the system')
    query_parser.add_argument('question', nargs='+', help='Your question')
    
    # Interactive command
    subparsers.add_parser('interactive', help='Interactive query mode')
    
    args = parser.parse_args()
    
    if args.command == 'ingest':
        ingest_document(args.pdf_path)
    
    elif args.command == 'query':
        question = ' '.join(args.question)
        query_system(question)
    
    elif args.command == 'interactive':
        interactive_mode()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
