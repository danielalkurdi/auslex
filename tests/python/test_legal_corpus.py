#!/usr/bin/env python3
"""
Test script for the comprehensive Australian Legal Corpus integration
"""

import os
import sys
import time
from pathlib import Path

# Add the project root api directory to the path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'api'))

def test_corpus_initialization():
    """Test corpus initialization"""
    print("=" * 60)
    print("TESTING LEGAL CORPUS INITIALIZATION")
    print("=" * 60)
    
    try:
        from legal_corpus import legal_corpus, get_corpus_stats
        
        print("Initializing legal corpus...")
        legal_corpus.initialize()
        
        stats = get_corpus_stats()
        print(f"Corpus Status: {stats['status']}")
        print(f"Document Count: {stats['document_count']}")
        print(f"Cache Available: {stats['cache_available']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Corpus initialization failed: {e}")
        return False

def test_corpus_search():
    """Test corpus search functionality"""
    print("\n" + "=" * 60)
    print("TESTING CORPUS SEARCH FUNCTIONALITY")
    print("=" * 60)
    
    try:
        from legal_corpus import search_legal_provisions
        
        test_queries = [
            "Migration Act section 359A",
            "character test visa",
            "unfair dismissal Fair Work Act",
            "procedural fairness tribunal",
            "directors duties corporations"
        ]
        
        for query in test_queries:
            print(f"\nQuery: '{query}'")
            results = search_legal_provisions(query, top_k=3)
            
            if results:
                print(f"Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result['citation']} (score: {result.get('relevance_score', 0):.3f})")
                    print(f"     Type: {result.get('type', 'Unknown')}")
                    print(f"     Jurisdiction: {result.get('jurisdiction', 'Unknown')}")
            else:
                print("  No results found")
        
        return True
        
    except Exception as e:
        print(f"❌ Corpus search failed: {e}")
        return False

def test_specific_provision_lookup():
    """Test specific provision lookup"""
    print("\n" + "=" * 60)
    print("TESTING SPECIFIC PROVISION LOOKUP")
    print("=" * 60)
    
    try:
        from legal_corpus import find_specific_legal_provision
        
        test_cases = [
            ("Migration Act", "359A", "Commonwealth"),
            ("Migration Act", "501", "Commonwealth"),
            ("Fair Work Act", "382", "Commonwealth"),
            ("Corporations Act", "181", "Commonwealth")
        ]
        
        for act_name, section, jurisdiction in test_cases:
            print(f"\nLooking up: {act_name} s {section} ({jurisdiction})")
            
            result = find_specific_legal_provision(act_name, section, jurisdiction)
            
            if result:
                print(f"✅ Found: {result['metadata']['title']}")
                print(f"   Source: {result['source']}")
                print(f"   Text length: {len(result['provision_text'])} characters")
                if result['full_act_url']:
                    print(f"   URL: {result['full_act_url']}")
            else:
                print("❌ Not found in corpus")
        
        return True
        
    except Exception as e:
        print(f"❌ Specific provision lookup failed: {e}")
        return False

def test_api_integration():
    """Test API integration with corpus"""
    print("\n" + "=" * 60)
    print("TESTING API INTEGRATION")
    print("=" * 60)
    
    try:
        # Import the updated search function
        sys.path.insert(0, 'api')
        from index import _search_legal_database
        
        test_query = "Migration Act section 359A procedural fairness"
        print(f"Testing API search with query: '{test_query}'")
        
        results = _search_legal_database(test_query)
        
        if results:
            print(f"✅ API search returned {len(results)} results:")
            for i, result in enumerate(results, 1):
                title = result['data']['metadata'].get('title', 'Unknown')
                score = result.get('score', 0)
                print(f"  {i}. {title} (score: {score:.1f})")
        else:
            print("❌ No results from API search")
        
        return True
        
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
        return False

def test_fallback_behavior():
    """Test fallback to mock database when corpus fails"""
    print("\n" + "=" * 60)
    print("TESTING FALLBACK BEHAVIOR")
    print("=" * 60)
    
    try:
        sys.path.insert(0, 'api')
        from index import _search_mock_database_fallback
        
        test_query = "character test migration"
        print(f"Testing fallback search with query: '{test_query}'")
        
        results = _search_mock_database_fallback(test_query)
        
        if results:
            print(f"✅ Fallback search returned {len(results)} results:")
            for i, result in enumerate(results, 1):
                title = result['data']['metadata'].get('title', 'Unknown')
                score = result.get('score', 0)
                print(f"  {i}. {title} (score: {score:.1f})")
        else:
            print("❌ No results from fallback search")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback behavior test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("COMPREHENSIVE LEGAL CORPUS TEST SUITE")
    print("=" * 60)
    
    start_time = time.time()
    
    tests = [
        ("Corpus Initialization", test_corpus_initialization),
        ("Corpus Search", test_corpus_search),
        ("Specific Provision Lookup", test_specific_provision_lookup),
        ("API Integration", test_api_integration),
        ("Fallback Behavior", test_fallback_behavior)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[TEST] {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print(f"Duration: {duration:.2f} seconds")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Legal corpus integration is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    print("\nNOTE: The first run may take longer as the corpus downloads and caches.")
    print("Subsequent runs should be much faster using cached data.")

if __name__ == "__main__":
    main()
