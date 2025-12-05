"""
Script to initialize and vectorize roles
Run this after deploying stakeholder_schema.sql to Supabase
"""
import sys
import logging
from stakeholder.manager import get_role_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def vectorize_existing_roles():
    """
    Vectorize all existing roles in the database
    Run this after deploying the schema with sample data
    """
    logger.info("Starting role vectorization...")
    
    try:
        manager = get_role_manager()
        
        # Get all roles
        roles = manager.list_roles(active_only=False)
        
        if not roles:
            logger.warning("No roles found in database")
            logger.info("Deploy stakeholder_schema.sql first to create sample data")
            return
        
        logger.info(f"Found {len(roles)} roles to vectorize")
        
        # Vectorize each role
        for role in roles:
            try:
                logger.info(f"Vectorizing: {role.role_name} ({role.department})")
                manager._vectorize_responsibilities(
                    role_id=role.id,
                    responsibilities=role.responsibilities
                )
                logger.info(f"✅ Vectorized: {role.role_name}")
            except Exception as e:
                logger.error(f"❌ Failed to vectorize {role.role_name}: {e}")
                continue
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ VECTORIZATION COMPLETE!")
        logger.info(f"   Total roles: {len(roles)}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Error during vectorization: {e}")
        sys.exit(1)


def test_routing():
    """
    Test document routing with sample queries
    """
    logger.info("\nTesting document routing...")
    
    manager = get_role_manager()
    
    test_cases = [
        "Invoice for 50 tons of cement from supplier XYZ",
        "Safety incident report - worker fell from scaffolding",
        "Blueprint approval needed for structural beam design",
        "Project timeline update for Phase 2 construction",
        "Concrete strength test results failing quality standards"
    ]
    
    logger.info("\n" + "=" * 70)
    logger.info("ROUTING TEST RESULTS")
    logger.info("=" * 70)
    
    for test_doc in test_cases:
        logger.info(f"\n📄 Document: {test_doc}")
        
        result = manager.route_document(
            document_summary=test_doc,
            top_k=3,
            threshold=0.6
        )
        
        if result['best_match']:
            match = result['best_match']
            logger.info(f"✅ Routed to: {match.role_name} ({match.department})")
            logger.info(f"   Similarity: {match.similarity:.2%}")
            logger.info(f"   Confidence: {match.confidence}")
            
            if result['fallback_used']:
                logger.warning("   ⚠️ Fallback to manager was used")
        else:
            logger.warning("❌ No match found (no manager available)")
    
    logger.info("\n" + "=" * 70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize and test role-based routing")
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run routing tests after vectorization'
    )
    
    args = parser.parse_args()
    
    # Vectorize existing roles
    vectorize_existing_roles()
    
    # Optionally run tests
    if args.test:
        test_routing()
