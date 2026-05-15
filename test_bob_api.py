"""
Test script to verify Bob API connection
Run this to check if Edward can communicate with Bob IDE
"""

import httpx
import asyncio
import sys
from pathlib import Path

# Add current directory to path to import config
sys.path.insert(0, str(Path(__file__).parent))

from config import IBM_BOB_API_URL, IBM_BOB_API_KEY


async def test_health_endpoint():
    """Test if Bob API health endpoint is accessible"""
    print("=" * 60)
    print("Testing Bob API Connection")
    print("=" * 60)
    print(f"\nAPI URL: {IBM_BOB_API_URL}")
    print(f"API Key: {'Set' if IBM_BOB_API_KEY else 'Not set'}")
    print()
    
    # Try common health endpoints
    health_endpoints = [
        "/health",
        "/api/health",
        "/status",
        "/",
    ]
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for endpoint in health_endpoints:
            url = f"{IBM_BOB_API_URL}{endpoint}"
            print(f"Trying: {url}")
            
            try:
                headers = {}
                if IBM_BOB_API_KEY:
                    headers["Authorization"] = f"Bearer {IBM_BOB_API_KEY}"
                
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    print(f"[OK] SUCCESS! Status: {response.status_code}")
                    print(f"Response: {response.text[:200]}")
                    return True
                else:
                    print(f"[X] Status: {response.status_code}")
                    
            except httpx.ConnectError:
                print(f"[X] Connection refused - is Bob IDE running?")
            except httpx.TimeoutException:
                print(f"[X] Timeout - server not responding")
            except Exception as e:
                print(f"[X] Error: {e}")
            
            print()
    
    return False


async def test_chat_endpoint():
    """Test if Bob API chat endpoint works"""
    print("\n" + "=" * 60)
    print("Testing Chat Endpoint")
    print("=" * 60)
    print()
    
    # Try common chat endpoints
    chat_configs = [
        {
            "endpoint": "/ask",
            "payload": {"question": "Hello, this is a test from Edward", "stream": False}
        },
        {
            "endpoint": "/api/ask",
            "payload": {"question": "Hello, this is a test from Edward", "stream": False}
        },
        {
            "endpoint": "/chat",
            "payload": {"message": "Hello, this is a test from Edward"}
        },
        {
            "endpoint": "/api/chat",
            "payload": {"message": "Hello, this is a test from Edward"}
        },
        {
            "endpoint": "/v1/chat/completions",
            "payload": {
                "messages": [{"role": "user", "content": "Hello, this is a test from Edward"}],
                "stream": False
            }
        },
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for config in chat_configs:
            url = f"{IBM_BOB_API_URL}{config['endpoint']}"
            print(f"Trying: POST {url}")
            
            try:
                headers = {"Content-Type": "application/json"}
                if IBM_BOB_API_KEY:
                    headers["Authorization"] = f"Bearer {IBM_BOB_API_KEY}"
                
                response = await client.post(
                    url,
                    json=config["payload"],
                    headers=headers
                )
                
                if response.status_code in [200, 201]:
                    print(f"[OK] SUCCESS! Status: {response.status_code}")
                    print(f"Response: {response.text[:200]}")
                    return True
                else:
                    print(f"[X] Status: {response.status_code}")
                    if response.status_code == 404:
                        print(f"  (Endpoint not found)")
                    elif response.status_code == 401:
                        print(f"  (Unauthorized - check API key)")
                    
            except httpx.ConnectError:
                print(f"[X] Connection refused")
            except httpx.TimeoutException:
                print(f"[X] Timeout")
            except Exception as e:
                print(f"[X] Error: {e}")
            
            print()
    
    return False


async def main():
    """Main test function"""
    print("\nEdward - Bob API Connection Test\n")
    
    # Test health endpoint
    health_ok = await test_health_endpoint()
    
    # Test chat endpoint
    chat_ok = await test_chat_endpoint()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    if health_ok:
        print("[OK] Health endpoint: WORKING")
    else:
        print("[X] Health endpoint: NOT FOUND")
    
    if chat_ok:
        print("[OK] Chat endpoint: WORKING")
    else:
        print("[X] Chat endpoint: NOT FOUND")
    
    print()
    
    if not health_ok and not chat_ok:
        print("[!] Troubleshooting Steps:")
        print("1. Make sure Bob IDE is running")
        print("2. Check if Bob IDE uses a different port")
        print("3. Verify API settings in Bob IDE preferences")
        print("4. Check BOB_API_SETUP.md for detailed instructions")
        print(f"\nCurrent configuration:")
        print(f"  URL: {IBM_BOB_API_URL}")
        print(f"  API Key: {'Set' if IBM_BOB_API_KEY else 'Not set'}")
    else:
        print("[OK] Connection successful! Edward should work with Bob API.")
        print("\nNext steps:")
        print("1. Update api_client.py if needed to match the working endpoint")
        print("2. Run 'python main.py' to start Edward")
        print("3. Press Win+Shift+E to test the full integration")
    
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()

# Made with Bob
