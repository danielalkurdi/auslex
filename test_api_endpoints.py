#!/usr/bin/env python3
"""
Simple test script to verify API endpoints are working correctly
Run this script to test the deployed API endpoints
"""

import requests
import json
import sys
from typing import Dict, Any

def test_endpoint(url: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test an API endpoint and return the response"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        return {
            "status_code": response.status_code,
            "success": response.status_code < 400,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "headers": dict(response.headers)
        }
    except Exception as e:
        return {"error": str(e), "success": False}

def main():
    """Run API tests"""
    # Get base URL from command line or use localhost
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    if not base_url.startswith("http"):
        base_url = f"https://{base_url}"
    
    print(f"Testing API endpoints at: {base_url}")
    print("=" * 50)
    
    # Test endpoints
    tests = [
        {
            "name": "API Root",
            "url": f"{base_url}/api",
            "method": "GET"
        },
        {
            "name": "Health Check",
            "url": f"{base_url}/api/health",
            "method": "GET"
        },
        {
            "name": "Chat Endpoint (Demo Mode)",
            "url": f"{base_url}/api/chat",
            "method": "POST",
            "data": {
                "message": "What is the Migration Act?",
                "max_tokens": 1000,
                "temperature": 0.7,
                "top_p": 0.9
            }
        },
        {
            "name": "Chat Endpoint (Citation Test)",
            "url": f"{base_url}/api/chat",
            "method": "POST",
            "data": {
                "message": "test citation",
                "max_tokens": 1000,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
    ]
    
    results = []
    for test in tests:
        print(f"\nTesting {test['name']}...")
        result = test_endpoint(
            test['url'], 
            test.get('method', 'GET'), 
            test.get('data')
        )
        results.append({**test, **result})
        
        if result['success']:
            print(f"✅ SUCCESS (Status: {result['status_code']})")
        else:
            print(f"❌ FAILED (Status: {result.get('status_code', 'N/A')})")
            if 'error' in result:
                print(f"   Error: {result['error']}")
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    print(f"Successful tests: {successful}/{total}")
    
    if successful == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)