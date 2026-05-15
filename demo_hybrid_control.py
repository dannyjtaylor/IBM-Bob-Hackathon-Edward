"""
Demo: Hybrid Autonomous Computer Control
Uses separate vision and text models for better performance
"""

import asyncio
import os
from dotenv import load_dotenv
import requests

from ollama_hybrid_client import OllamaHybridClient
from ollama_control_processor import OllamaControlProcessor, OllamaAutonomousLoop
from control_client import get_control_client
from logger import setup_logger

# Setup logging
logger = setup_logger(__name__, log_file='logs/hybrid_control.log')

# Load environment variables
load_dotenv()


async def main():
    """Main demo function."""
    
    print("=" * 70)
    print("Edward Hybrid Autonomous Computer Control Demo")
    print("Vision Model + Text Model = Faster & More Efficient!")
    print("=" * 70)
    print()
    
    # Configuration
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    vision_model = os.getenv("OLLAMA_VISION_MODEL", "llava:7b")
    text_model = os.getenv("OLLAMA_TEXT_MODEL", "llama3.2:3b")
    control_api_url = os.getenv("CONTROL_API_URL", "http://127.0.0.1:8001")
    screenshot_interval = float(os.getenv("SCREENSHOT_INTERVAL", "2.0"))
    auto_execute = os.getenv("AUTO_EXECUTE_ACTIONS", "false").lower() == "true"
    
    print("🔧 Configuration:")
    print(f"  Ollama URL: {ollama_url}")
    print(f"  Vision Model: {vision_model} (analyzes screenshots)")
    print(f"  Text Model: {text_model} (generates actions)")
    print(f"  Screenshot Interval: {screenshot_interval}s")
    print(f"  Auto-Execute: {auto_execute}")
    print()
    
    # Check Ollama and models
    print("🔍 Checking Ollama setup...")
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            # Check vision model
            vision_ok = vision_model in model_names
            if vision_ok:
                print(f"✅ Vision model '{vision_model}' available")
            else:
                print(f"❌ Vision model '{vision_model}' not found!")
                print(f"   Run: ollama pull {vision_model}")
            
            # Check text model
            text_ok = text_model in model_names
            if text_ok:
                print(f"✅ Text model '{text_model}' available")
            else:
                print(f"❌ Text model '{text_model}' not found!")
                print(f"   Run: ollama pull {text_model}")
            
            if not (vision_ok and text_ok):
                print()
                print("📥 Download missing models:")
                if not vision_ok:
                    print(f"   ollama pull {vision_model}")
                if not text_ok:
                    print(f"   ollama pull {text_model}")
                return
        else:
            print("❌ Ollama is not responding")
            return
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print()
        print("Make sure Ollama is installed and running:")
        print("  1. Download from: https://ollama.ai")
        print("  2. Install and start Ollama")
        return
    
    print()
    
    # Show model sizes
    print("📊 Model Information:")
    print(f"  {vision_model}: ~4.7GB (vision analysis)")
    print(f"  {text_model}: ~2GB (action generation)")
    print(f"  Total: ~6.7GB (vs 7.4GB for llava:13b alone)")
    print()
    
    # Get task from user
    print("What would you like the AI to help you with?")
    print()
    print("📝 Example tasks:")
    print("  - Open Notepad and type 'Hello World'")
    print("  - Open Calculator and calculate 25 * 4")
    print("  - Search for 'Python tutorials' in my browser")
    print()
    
    task = input("Enter task description: ").strip()
    
    if not task:
        task = "Observe the screen and assist with any tasks"
    
    print()
    print(f"🎯 Task: {task}")
    print()
    
    if not auto_execute:
        print("⚠️  Auto-execute is disabled. Actions will be logged but not executed.")
        print("   Set AUTO_EXECUTE_ACTIONS=true in .env to enable execution.")
        print()
    
    # Create hybrid client
    try:
        hybrid_client = OllamaHybridClient(
            base_url=ollama_url,
            vision_model=vision_model,
            text_model=text_model
        )
        
        control_client = get_control_client(base_url=control_api_url)
        
        # Create processor with hybrid client
        processor = OllamaControlProcessor(
            ollama_client=hybrid_client,
            control_client=control_client,
            task_description=task,
            auto_execute=auto_execute
        )
        
        print("✅ Hybrid autonomous control initialized")
        print()
        print("How it works:")
        print(f"  1. 📸 Capture screenshot every {screenshot_interval}s")
        print(f"  2. 👁️  {vision_model} analyzes what's on screen")
        print(f"  3. 🧠 {text_model} decides what action to take")
        print(f"  4. 🎮 Execute the action")
        print()
        print("Starting in 3 seconds...")
        print("Press Ctrl+C to stop")
        print()
        
        await asyncio.sleep(3)
        
        # Initialize processor
        await processor.initialize()
        
        # Start screenshot service
        from screenshot_service import get_screenshot_service
        screenshot_service = get_screenshot_service(interval=screenshot_interval)
        await screenshot_service.start(processor.process_screenshot)
        
        print("🤖 Hybrid AI is now controlling your computer!")
        print("   Two-stage analysis for better performance...")
        print()
        print("📊 Action Log:")
        print("-" * 70)
        
        # Run until interrupted
        try:
            while True:
                await asyncio.sleep(1)
                
                # Show recent actions
                history = processor.get_action_history(limit=1)
                if history:
                    last_action = history[-1]
                    action_type = last_action["action"].get("action_type")
                    reasoning = last_action["action"].get("reasoning", "N/A")
                    timestamp = last_action["timestamp"]
                    
                    print(f"[{timestamp}] {action_type}")
                    print(f"  Reasoning: {reasoning}")
                    print("-" * 70)
        
        except KeyboardInterrupt:
            print()
            print("🛑 Stopping hybrid autonomous control...")
            await screenshot_service.stop()
            print("✅ Stopped")
            print()
            
            # Show summary
            history = processor.get_action_history(limit=100)
            print(f"📈 Summary: {len(history)} actions executed")
    
    except Exception as e:
        logger.error(f"Demo error: {e}")
        print(f"❌ Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Make sure Computer Control API is running:")
        print("     python start_control_api.py")
        print("  2. Check both models are downloaded")
        print("  3. Check logs in logs/hybrid_control.log")


def run_demo():
    """Run the demo."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")


if __name__ == "__main__":
    run_demo()


# Made with Bob