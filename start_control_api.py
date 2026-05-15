"""
Startup script for Edward Computer Control API
Starts the FastAPI server with proper configuration
"""

import sys
import subprocess
import time
import httpx
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    
    required = ['fastapi', 'uvicorn', 'pyautogui', 'httpx']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("\nInstall them with:")
        print("  pip install -r requirements.txt")
        return False
    
    print("✓ All dependencies installed\n")
    return True


def check_port_available(port: int = 8002) -> bool:
    """Check if port is available"""
    try:
        response = httpx.get(f"http://127.0.0.1:{port}/health", timeout=1.0)
        print(f"⚠️  Port {port} is already in use (API may already be running)")
        return False
    except (httpx.ConnectError, httpx.TimeoutException):
        return True
    except Exception:
        return True


def start_api(port: int = 8002, reload: bool = False):
    """Start the Computer Control API"""
    print(f"Starting Edward Computer Control API on port {port}...")
    print(f"API URL: http://127.0.0.1:{port}")
    print(f"Documentation: http://127.0.0.1:{port}/docs")
    print("\nPress Ctrl+C to stop the server\n")
    print("=" * 60)
    
    try:
        # Start uvicorn server
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "computer_control_api:app",
            "--host", "127.0.0.1",
            "--port", str(port),
            "--log-level", "info"
        ]
        
        if reload:
            cmd.append("--reload")
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n\nShutting down API server...")
    except Exception as e:
        print(f"\n✗ Error starting API: {e}")
        return False
    
    return True


def main():
    """Main entry point"""
    print("=" * 60)
    print("Edward Computer Control API - Startup")
    print("=" * 60)
    print()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check if port is available
    port = 8002
    if not check_port_available(port):
        response = input("\nTry to start anyway? (y/n): ").lower()
        if response != 'y':
            print("Exiting...")
            sys.exit(0)
    
    # Parse command line arguments
    reload = "--reload" in sys.argv or "-r" in sys.argv
    
    if reload:
        print("🔄 Auto-reload enabled (for development)\n")
    
    # Start the API
    success = start_api(port=port, reload=reload)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

# Made with Bob