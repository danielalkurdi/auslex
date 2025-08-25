#!/usr/bin/env python3
"""
Test script specifically for section 359A functionality
"""

import os
import sys
from pathlib import Path

# Add the project root api directory to the path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'api'))

def test_section_359a_search():
    """Test searching for section 359A"""
    print("Testing section 359A search...")
    
    try:
        from legal_corpus_lite import search_legal_provisions
        
        queries = [
            "What is s 359A of the Migration Act",
            "Migration Act section 359A",
            "section 359A procedural fairness",
            "359A tribunal information"
        ]
        
        for query in queries:
            print(f"\nQuery: '{query}'")
            results = search_legal_provisions(query, top_k=3)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result['citation']} (score: {result.get('relevance_score', 0):.3f})")
                    if '359a' in result['citation'].lower():
                        print(f"     SUCCESS: Found section 359A!")
                        return True
            else:
                print("  No results found")
        
        return False
        
    except Exception as e:
        print(f"Search test failed: {e}")
        return False

def test_specific_359a_lookup():
    """Test specific lookup for section 359A"""
    print("Testing specific 359A lookup...")
    
    try:
        from legal_corpus_lite import find_specific_legal_provision
        
        result = find_specific_legal_provision("Migration Act", "359A", "Commonwealth")
        
        if result:
            print("SUCCESS: Found section 359A via specific lookup")
            print(f"Title: {result['metadata']['title']}")
            print(f"Text length: {len(result['provision_text'])} characters")
            print(f"Contains 'procedural fairness': {'procedural fairness' in result['provision_text'].lower()}")
            print(f"Contains 'tribunal': {'tribunal' in result['provision_text'].lower()}")
            return True
        else:
            print("FAIL: Section 359A not found in specific lookup")
            return False
            
    except Exception as e:
        print(f"Specific lookup test failed: {e}")
        return False

def test_api_integration_359a():
    """Test the full API integration with section 359A"""
    print("Testing API integration for 359A...")
    
    try:
        from index import _search_legal_database
        
        query = "What is s 359A of the Migration Act"
        results = _search_legal_database(query)
        
        if results:
            print(f"API returned {len(results)} results:")
            for i, result in enumerate(results, 1):
                title = result['data']['metadata'].get('title', 'Unknown')
                score = result.get('score', 0)
                print(f"  {i}. {title} (score: {score:.1f})")
                
                # Check if we found 359A
                if '359a' in title.lower():
                    print("SUCCESS: API found section 359A!")
                    return True
        
        print("FAIL: API did not find section 359A")
        return False
        
    except Exception as e:
        print(f"API integration test failed: {e}")
        return False

def main():
    """Run 359A-specific tests"""
    print("SECTION 359A FUNCTIONALITY TEST")
    print("=" * 50)
    
    tests = [
        ("Search for 359A", test_section_359a_search),
        ("Specific 359A Lookup", test_specific_359a_lookup),
        ("API Integration 359A", test_api_integration_359a)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n[TEST] {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"PASS: {test_name}")
            else:
                print(f"FAIL: {test_name}")
        except Exception as e:
            print(f"ERROR: {test_name} - {e}")
    
    print(f"\nSUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS: Section 359A is now working correctly!")
        print("The AI should now be able to answer questions about section 359A.")
    else:
        print("WARNING: Section 359A functionality needs debugging.")
    
    return passed == total

if __name__ == "__main__":
    main()
