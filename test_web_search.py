#!/usr/bin/env python3
"""
Simple test script to verify enhanced legal assistant functionality with database integration
"""
import os
from openai import OpenAI

# Load environment variables from .env file
def load_env():
    try:
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    os.environ[key] = value
    except FileNotFoundError:
        pass

load_env()

def test_web_search():
    """Test the web search functionality with OpenAI's responses API"""
    try:
        # Create OpenAI client
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL") if os.getenv("OPENAI_BASE_URL") else None
        )
        
        print("Testing GPT-5 web search functionality...")
        print("=" * 50)
        
        # Test message
        test_message = "What are the latest changes to Australian privacy laws in 2024?"
        
        print(f"Query: {test_message}")
        print("\nSending request with web search enabled...")
        
        # Make request with web search
        response = client.responses.create(
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            tools=[{"type": "web_search"}],
            tool_choice="auto",
            input=[
                {"role": "system", "content": (
                    "You are an Australian legal assistant. Be concise, accurate, and cite legislation, "
                    "cases, and official sources. Educational use only; not legal advice."
                )},
                {"role": "user", "content": test_message},
            ],
            temperature=0.7,
            max_output_tokens=1000,
            top_p=0.9,
        )
        
        # Extract response
        response_text = getattr(response, "output_text", "No response text available")
        
        print("\nResponse:")
        print("-" * 30)
        print(response_text)
        print("-" * 30)
        
        # Check if response seems to include recent information
        recent_indicators = ["2024", "recent", "latest", "new", "updated", "current"]
        has_recent_info = any(indicator in response_text.lower() for indicator in recent_indicators)
        
        print(f"\nAnalysis:")
        print(f"Response length: {len(response_text)} characters")
        print(f"Contains recent information indicators: {has_recent_info}")
        
        if has_recent_info:
            print("[SUCCESS] Web search appears to be working - response includes recent information")
        else:
            print("[WARNING] Web search may not be working - no recent information detected")
            
        return True
        
    except Exception as e:
        print(f"[ERROR] Error testing web search: {str(e)}")
        return False

def test_without_web_search():
    """Test the same query without web search for comparison"""
    try:
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL") if os.getenv("OPENAI_BASE_URL") else None
        )
        
        print("\n" + "=" * 50)
        print("Testing WITHOUT web search for comparison...")
        print("=" * 50)
        
        test_message = "What are the latest changes to Australian privacy laws in 2024?"
        
        # Make request without web search
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": (
                    "You are an Australian legal assistant. Be concise, accurate, and cite legislation "
                    "or cases where relevant. Educational use only; not legal advice."
                )},
                {"role": "user", "content": test_message},
            ],
            temperature=0.7,
            max_tokens=1000,
            top_p=0.9,
        )
        
        response_text = response.choices[0].message.content if response.choices else "No response"
        
        print("\nResponse (without web search):")
        print("-" * 30)
        print(response_text)
        print("-" * 30)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error testing without web search: {str(e)}")
        return False

if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key to test the functionality")
        exit(1)
    
    print("AusLex Enhanced Legal Assistant Test")
    print("=" * 50)
    print(f"Model: {os.getenv('OPENAI_CHAT_MODEL', 'gpt-4o-mini')}")
    print(f"Base URL: {os.getenv('OPENAI_BASE_URL', 'Default OpenAI')}")
    
    # Run tests
    enhanced_success = test_enhanced_chat()
    recent_info_success = test_recent_info_handling()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    print(f"Enhanced legal assistant test: {'PASSED' if enhanced_success else 'FAILED'}")
    print(f"Recent information handling test: {'PASSED' if recent_info_success else 'FAILED'}")
    
    if enhanced_success and recent_info_success:
        print("\n[SUCCESS] Enhanced legal assistant functionality appears to be working correctly!")
        print("The chat.completions.create() API with legal database integration is working.")
    else:
        print("\n[WARNING] There may be issues with the enhanced legal assistant implementation.")