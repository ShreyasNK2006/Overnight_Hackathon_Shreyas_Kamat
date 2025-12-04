"""
Test FastAPI endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health check"""
    print("\n" + "=" * 70)
    print("Testing Health Check")
    print("=" * 70)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_stats():
    """Test stats endpoint"""
    print("\n" + "=" * 70)
    print("Testing Stats")
    print("=" * 70)
    
    response = requests.get(f"{BASE_URL}/stats")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_ingest(file_path):
    """Test document ingestion"""
    print("\n" + "=" * 70)
    print("Testing Document Ingestion")
    print("=" * 70)
    print(f"File: {file_path}")
    
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/ingest", files=files)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.text}")

def test_query(question):
    """Test RAG query"""
    print("\n" + "=" * 70)
    print("Testing RAG Query")
    print("=" * 70)
    print(f"Question: {question}")
    
    payload = {
        "question": question,
        "top_k": 5,
        "include_tables": True,
        "include_images": True
    }
    
    response = requests.post(f"{BASE_URL}/query", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n" + "=" * 70)
        print("ANSWER:")
        print("=" * 70)
        print(result["answer"])
        
        print("\n" + "=" * 70)
        print(f"SOURCES ({len(result['sources'])}):")
        print("=" * 70)
        
        for source in result["sources"]:
            print(f"\n[Source {source['source_number']}]")
            print(f"  Document: {source['document']}")
            print(f"  Page: {source['page']}")
            print(f"  Section: {source['section']}")
            print(f"  Type: {source['type']}")
            print(f"  Relevance: {source['similarity_score']:.3f}")
        
        print(f"\nProcessing time: {result['processing_time_ms']:.2f}ms")
        print(f"Retrieved chunks: {result['retrieved_chunks_count']}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    import sys
    
    print("=" * 70)
    print("FastAPI RAG System - API Tests")
    print("=" * 70)
    print("\nMake sure the server is running: python api.py")
    print("=" * 70)
    
    # Test health
    test_health()
    
    # Test stats
    test_stats()
    
    # Test query if question provided
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        test_query(question)
    else:
        print("\nℹ️  To test query: python test_api.py 'Your question here'")
