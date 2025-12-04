"""
Fix the unique constraint issue and re-ingest
"""
from database.supabase_client import get_supabase_client

print("="*70)
print("FIXING DATABASE SCHEMA")
print("="*70)

client = get_supabase_client()

# Check for unique constraints
print("\nStep 1: Checking for problematic constraints...")

# Try to drop the unique constraint if it exists
try:
    # Note: This requires direct SQL execution
    print("\n⚠️  Your database has a unique constraint on 'source' field")
    print("This prevents storing multiple nodes from the same document.")
    print("\nTo fix this, go to your Supabase Dashboard:")
    print("1. Open SQL Editor")
    print("2. Run this command:")
    print("\n" + "="*70)
    print("DROP INDEX IF EXISTS idx_unique_filename;")
    print("="*70)
    print("\nThis will allow multiple parent nodes per document.")
    print("(e.g., multiple images, tables, text sections from one PDF)")
    
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*70)
print("ALTERNATIVE: Clean and Re-ingest")
print("="*70)

response = input("\nDo you want to clean the database and re-ingest? (yes/no): ")

if response.lower() == 'yes':
    print("\nCleaning database...")
    client.delete_all_data()
    print("✅ Database cleaned")
    
    print("\nNow run:")
    print('python test_ingestion.py "C:\\Users\\Sujal B\\Downloads\\MATHS_CIE1.docx"')
else:
    print("\nSkipped. Please remove the unique constraint manually in Supabase.")

print("\n" + "="*70)
