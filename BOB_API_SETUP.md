# Bob IDE API Setup Guide

This guide helps you configure Edward to communicate with Bob IDE's local API.

## Quick Start

Edward is pre-configured to use `http://localhost:8000` as the default Bob API endpoint. If Bob IDE uses a different port or configuration, follow the steps below.

## Finding Bob IDE's API Settings

### Method 1: Check Bob IDE Settings

1. Open Bob IDE
2. Go to **Settings** or **Preferences** (usually File → Preferences or Edit → Settings)
3. Look for sections like:
   - "API Settings"
   - "Server Configuration"
   - "Local API"
   - "Developer Settings"
4. Note the following:
   - **Port number** (e.g., 8000, 3000, 5000)
   - **API endpoint** (e.g., `/api/chat`, `/v1/completions`)
   - **Authentication method** (API key, token, or none)

### Method 2: Check Bob IDE Documentation

1. Look for Bob IDE's documentation or help menu
2. Search for terms like:
   - "API"
   - "Local server"
   - "Integration"
   - "Developer mode"

### Method 3: Check Running Processes

If Bob IDE is running, you can check which port it's using:

**Windows PowerShell:**
```powershell
netstat -ano | findstr "LISTENING" | findstr "8000"
netstat -ano | findstr "LISTENING" | findstr "3000"
netstat -ano | findstr "LISTENING" | findstr "5000"
```

Look for entries like:
```
TCP    127.0.0.1:8000    0.0.0.0:0    LISTENING    12345
```

### Method 4: Test Common Endpoints

Try these common configurations in your browser or with curl:

```bash
# Test if API is running
curl http://localhost:8000/health
curl http://localhost:8000/api/health
curl http://localhost:3000/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d '{"message":"test"}'
```

## Configuring Edward

Once you've found Bob IDE's API settings, update your `.env` file:

### 1. Update API URL

Edit `.env` and change the `IBM_BOB_API_URL`:

```env
# If Bob IDE runs on port 3000
IBM_BOB_API_URL=http://localhost:3000

# If Bob IDE uses a specific endpoint
IBM_BOB_API_URL=http://localhost:8000/api/v1

# If Bob IDE uses HTTPS
IBM_BOB_API_URL=https://localhost:8443
```

### 2. Update API Key (if required)

If Bob IDE requires authentication:

```env
# If Bob IDE uses an API key
IBM_BOB_API_KEY=your_actual_api_key_here

# If Bob IDE doesn't require auth for localhost
IBM_BOB_API_KEY=
```

To find your API key:
- Check Bob IDE's settings under "API Keys" or "Authentication"
- Look for "Generate API Key" or "Show API Key" buttons
- Check Bob IDE's config files (usually in `~/.bob-ide/` or similar)

### 3. Update Your Name

```env
USER_NAME=Danny
```

## Testing the Connection

### Option 1: Use Edward's Test Script

Create a test script to verify the connection:

```python
# test_bob_api.py
import httpx
import asyncio
from config import IBM_BOB_API_URL, IBM_BOB_API_KEY

async def test_connection():
    try:
        async with httpx.AsyncClient() as client:
            headers = {}
            if IBM_BOB_API_KEY:
                headers["Authorization"] = f"Bearer {IBM_BOB_API_KEY}"
            
            response = await client.get(
                f"{IBM_BOB_API_URL}/health",
                headers=headers,
                timeout=5.0
            )
            
            print(f"✓ Connected to Bob API: {IBM_BOB_API_URL}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        print(f"\nTroubleshooting:")
        print(f"1. Is Bob IDE running?")
        print(f"2. Is the API URL correct? ({IBM_BOB_API_URL})")
        print(f"3. Does Bob IDE require an API key?")

if __name__ == "__main__":
    asyncio.run(test_connection())
```

Run it:
```bash
python test_bob_api.py
```

### Option 2: Manual Testing

Use curl or PowerShell to test:

```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get

# With API key
$headers = @{
    "Authorization" = "Bearer your_api_key_here"
}
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -Headers $headers
```

## Common API Endpoint Patterns

Bob IDE might use one of these patterns:

### Pattern 1: Simple Chat
```
POST http://localhost:8000/chat
Body: {"message": "Hello", "image": "base64_string"}
```

### Pattern 2: OpenAI-Compatible
```
POST http://localhost:8000/v1/chat/completions
Body: {
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": true
}
```

### Pattern 3: Custom Format
```
POST http://localhost:8000/api/ask
Body: {
  "question": "Hello",
  "screenshot": "base64_string",
  "stream": true
}
```

## Updating api_client.py

If Bob IDE uses a different API format, you may need to update `api_client.py`:

```python
# Example: Update the ask_question method
async def ask_question(self, question: str, screenshot_base64: Optional[str] = None):
    # Adjust payload format to match Bob IDE's API
    payload = {
        "message": question,  # or "prompt", "query", etc.
        "image": screenshot_base64,  # or "screenshot", "context", etc.
    }
    
    # Adjust endpoint
    response = await self.client.post(
        f"{self.api_url}/chat",  # or "/api/ask", "/v1/completions", etc.
        json=payload,
        headers=headers
    )
```

## Troubleshooting

### Issue: Connection Refused
- **Cause**: Bob IDE's API is not running or using a different port
- **Solution**: Check if Bob IDE is running and verify the port number

### Issue: 401 Unauthorized
- **Cause**: Missing or invalid API key
- **Solution**: Check if Bob IDE requires authentication and update `IBM_BOB_API_KEY`

### Issue: 404 Not Found
- **Cause**: Wrong endpoint path
- **Solution**: Verify the correct API endpoint path in Bob IDE's documentation

### Issue: CORS Error
- **Cause**: Browser security restrictions (shouldn't affect Edward since it's a desktop app)
- **Solution**: This shouldn't be an issue for Edward, but check Bob IDE's CORS settings if needed

## Alternative: No Local API Available

If Bob IDE doesn't provide a local API, you have these options:

### Option 1: Use IBM Watson/watsonx Cloud API
1. Sign up for IBM Cloud: https://cloud.ibm.com/
2. Create a Watson Assistant or watsonx.ai instance
3. Get your API key and endpoint
4. Update `.env` with cloud credentials

### Option 2: Create a Simple Proxy Server
Create a FastAPI server that bridges Edward and Bob IDE:

```python
# bob_proxy.py
from fastapi import FastAPI
import subprocess

app = FastAPI()

@app.post("/ask")
async def ask_bob(question: str):
    # Use Bob IDE's CLI or other integration method
    result = subprocess.run(
        ["bob-cli", "ask", question],
        capture_output=True,
        text=True
    )
    return {"response": result.stdout}

# Run with: uvicorn bob_proxy:app --port 8000
```

### Option 3: Use Bob IDE's Extension API
Check if Bob IDE has an extension or plugin API that Edward can use directly.

## Need Help?

If you're still having trouble:
1. Check Bob IDE's official documentation
2. Look for Bob IDE's community forums or Discord
3. Contact Bob IDE support
4. Share error messages for more specific help

## Summary

**Current Configuration:**
- API URL: `http://localhost:8000`
- API Key: Not set (assumes no auth required for localhost)
- Endpoint: `/ask` (can be adjusted in `api_client.py`)

**Next Steps:**
1. Verify Bob IDE is running
2. Find the correct API port and endpoint
3. Update `.env` if needed
4. Run `python test_bob_api.py` to test
5. Start Edward with `python main.py`

Good luck! 🚀