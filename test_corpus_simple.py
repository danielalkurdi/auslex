#!/usr/bin/env python3
"""
Simple test for legal corpus integration - tests the basic structure
"""

import os
import sys

# Add the api directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

def test_import():
    """Test that we can import the legal corpus module"""
    print("Testing legal corpus import...")
    
    try:
        from legal_corpus_lite import search_legal_provisions, get_corpus_stats
        print("Successfully imported legal corpus lite modules")
        return True
    except Exception as e:
        print(f"Failed to import legal corpus: {e}")
        return False

def test_api_integration():
    """Test that the API can import the legal corpus functions"""
    print("Testing API integration...")
    
    try:
        from index import get_corpus_stats
        stats = get_corpus_stats()
        print(f"API integration working. Corpus status: {stats}")
        return True
    except Exception as e:
        print(f"API integration failed: {e}")
        return False

def test_search_function_structure():
    """Test that the search function has the right structure"""
    print("Testing search function structure...")
    
    try:
        from index import _search_legal_database
        
        # Test with a simple query - should not crash
        results = _search_legal_database("test query")
        print(f"Search function works. Returned {len(results)} results")
        
        # Check result structure
        if results and len(results) > 0:
            result = results[0]
            required_keys = ['key', 'data', 'score']
            if all(key in result for key in required_keys):
                print("Result structure is correct")
                return True
            else:
                print(f"Missing keys in result: {[k for k in required_keys if k not in result]}")
                return False
        else:
            print("Search completed (no results for test query)")
            return True
            
    except Exception as e:
        print(f"Search function test failed: {e}")
        return False

def main():
    """Run simple tests"""
    print("SIMPLE LEGAL CORPUS INTEGRATION TEST")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_import),
        ("API Integration", test_api_integration),
        ("Search Function", test_search_function_structure)
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
        print("SUCCESS: Basic integration tests passed!")
        print("The legal corpus integration structure is working.")
        print("Full functionality will be available once dependencies are installed.")
    else:
        print("WARNING: Some basic tests failed.")
    
    return passed == total

if __name__ == "__main__":
    main()