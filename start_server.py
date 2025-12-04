"""
Start FastAPI server
"""
import uvicorn

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Starting Infrastructure RAG API Server")
    print("=" * 70)
    print("\n📡 Server will be available at:")
    print("   http://localhost:8000")
    print("\n📚 API Documentation:")
    print("   http://localhost:8000/docs")
    print("\n✨ Endpoints:")
    print("   GET  /health  - Health check")
    print("   POST /ingest  - Upload document")
    print("   POST /query   - Ask questions")
    print("   GET  /stats   - Database statistics")
    print("\n" + "=" * 70 + "\n")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
