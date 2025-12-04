"""
Setup verification script
Checks if all components are properly configured
"""
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_environment():
    """Check if .env file exists and has required variables"""
    try:
        from config.settings import settings
        
        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_KEY',
            'GOOGLE_API_KEY'
        ]
        
        missing = []
        for var in required_vars:
            value = getattr(settings, var, None)
            if not value or value.startswith('your_'):
                missing.append(var)
        
        if missing:
            logger.error(f"❌ Missing environment variables: {', '.join(missing)}")
            logger.info("Please create .env file and add your credentials")
            return False
        
        logger.info("✅ Environment variables configured")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error loading environment: {e}")
        logger.info("Make sure .env file exists (copy from .env.example)")
        return False


def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        ('langchain', 'langchain'),
        ('docling', 'docling'),
        ('supabase', 'supabase'),
        ('sentence_transformers', 'sentence-transformers'),
        ('langchain_google_genai', 'langchain-google-genai'),
        ('langchain_huggingface', 'langchain-huggingface'),
    ]
    
    missing = []
    for package_name, pip_name in required_packages:
        try:
            __import__(package_name)
            logger.info(f"✅ {pip_name} installed")
        except ImportError:
            logger.error(f"❌ {pip_name} not installed")
            missing.append(pip_name)
    
    if missing:
        logger.error(f"\nInstall missing packages:")
        logger.error(f"pip install {' '.join(missing)}")
        return False
    
    return True


def check_supabase_connection():
    """Test Supabase connection"""
    try:
        from database.supabase_client import get_supabase_client
        
        client = get_supabase_client()
        
        # Test database query
        try:
            response = client.client.table("parent_documents").select("id").limit(1).execute()
            logger.info("✅ Supabase database connection successful")
        except Exception as e:
            logger.error(f"❌ Supabase database error: {e}")
            logger.info("Make sure tables are created (run schema.sql)")
            return False
        
        # Test storage bucket
        try:
            buckets = client.storage.list_buckets()
            bucket_names = [b.name for b in buckets]
            if client.bucket_name in bucket_names:
                logger.info(f"✅ Storage bucket '{client.bucket_name}' exists")
            else:
                logger.warning(f"⚠️  Storage bucket '{client.bucket_name}' not found")
                logger.info(f"Creating bucket...")
                client.create_storage_bucket()
                logger.info("✅ Storage bucket created")
        except Exception as e:
            logger.error(f"❌ Storage bucket error: {e}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Supabase connection failed: {e}")
        return False


def check_embedding_model():
    """Test embedding model"""
    try:
        from retrieval.embeddings import get_embedding_model
        
        logger.info("Loading embedding model (first time may take a while)...")
        model = get_embedding_model()
        
        # Test embedding
        test_text = "This is a test sentence."
        embedding = model.embed_text(test_text)
        
        if len(embedding) == 384:
            logger.info("✅ Embedding model loaded successfully (384 dimensions)")
            return True
        else:
            logger.error(f"❌ Unexpected embedding dimension: {len(embedding)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Embedding model error: {e}")
        return False


def check_gemini():
    """Test Gemini API"""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from config.settings import settings
        
        llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GOOGLE_API_KEY
        )
        
        # Test simple generation
        response = llm.invoke("Say 'Hello' if you can read this.")
        
        if response.content:
            logger.info("✅ Gemini API connection successful")
            return True
        else:
            logger.error("❌ Gemini API returned empty response")
            return False
            
    except Exception as e:
        logger.error(f"❌ Gemini API error: {e}")
        logger.info("Check your GOOGLE_API_KEY in .env")
        return False


def main():
    """Run all verification checks"""
    print("\n" + "="*60)
    print("INFRASTRUCTURE RAG SYSTEM - SETUP VERIFICATION")
    print("="*60 + "\n")
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Environment Variables", check_environment),
        ("Supabase Connection", check_supabase_connection),
        ("Embedding Model", check_embedding_model),
        ("Gemini API", check_gemini),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n--- Checking {name} ---")
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 All checks passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Test ingestion with: python ingestion/pipeline.py")
        print("2. Or implement retrieval components")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
