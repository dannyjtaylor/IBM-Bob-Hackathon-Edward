"""
Demo: Autonomous Computer Control with Local Ollama AI
Shows how to use AI-driven computer control with local LLaVA models
"""

import asyncio
import os
from dotenv import load_dotenv

from ollama_control_processor import OllamaAutonomousLoop
from logger import setup_logger

# Setup logging
logger = setup_logger(__name__, log_file='logs/ollama_control.log')

# Load environment variables
load_dotenv()


async def main():
    """Main demo function."""
    
    print("=" * 60)
    print("Edward Autonomous Computer Control Demo")
    print("Powered by Local Ollama AI (LLaVA)")
    print("=" * 60)
    print()
    
    # Configuration
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llava:13b")
    screenshot_interval = float(os.getenv("SCREENSHOT_INTERVAL", "2.0"))
    auto_execute = os.getenv("AUTO_EXECUTE_ACTIONS", "false").lower() == "true"
    
    print("🔧 Configuration:")
    print(f"  Ollama URL: {ollama_url}")
    print(f"  Model: {ollama_model}")
    print(f"  Screenshot Interval: {screenshot_interval}s")
    print(f"  Auto-Execute: {auto_execute}")
    print()
    
    # Check if Ollama is running
    print("🔍 Checking Ollama...")
    import requests
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            if ollama_model in model_names:
                print(f"✅ Model '{ollama_model}' is available")
            else:
                print(f"❌ Model '{ollama_model}' not found!")
                print(f"   Available models: {', '.join(model_names) if model_names else 'None'}")
                print()
                print(f"📥 To download the model, run:")
                print(f"   ollama pull {ollama_model}")
                print()
                
                # Suggest alternatives
                if "llava:7b" in model_names:
                    print("💡 You have 'llava:7b' available. Use that instead? (y/n)")
                    choice = input().strip().lower()
                    if choice == 'y':
                        ollama_model = "llava:7b"
                    else:
                        return
                else:
                    return
        else:
            print("❌ Ollama is not responding correctly")
            return
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        print()
        print("Make sure Ollama is installed and running:")
        print("  1. Download from: https://ollama.ai")
        print("  2. Install and start Ollama")
        print(f"  3. Run: ollama pull {ollama_model}")
        return
    
    print()
    
    # Get task from user
    print("What would you like the AI to help you with?")
    print()
    print("📝 Example tasks:")
    print("  - Open Notepad and type 'Hello World'")
    print("  - Open Calculator and calculate 25 * 4")
    print("  - Search for 'Python tutorials' in my browser")
    print("  - Navigate to a specific website")
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
    
    # Create control loop
    try:
        control_loop = OllamaAutonomousLoop(
            task_description=task,
            screenshot_interval=screenshot_interval,
            ollama_url=ollama_url,
            ollama_model=ollama_model,
            auto_execute=auto_execute
        )
        
        print("✅ Autonomous control initialized")
        print()
        print("Starting in 3 seconds...")
        print("Press Ctrl+C to stop")
        print()
        
        await asyncio.sleep(3)
        
        # Start the control loop
        await control_loop.start()
        
        print("🤖 AI is now controlling your computer!")
        print("   Watching screen and making decisions...")
        print()
        print("📊 Action Log:")
        print("-" * 60)
        
        # Run until interrupted
        try:
            while True:
                await asyncio.sleep(1)
                
                # Show recent actions
                history = control_loop.processor.get_action_history(limit=1)
                if history:
                    last_action = history[-1]
                    action_type = last_action["action"].get("action_type")
                    reasoning = last_action["action"].get("reasoning", "N/A")
                    timestamp = last_action["timestamp"]
                    
                    print(f"[{timestamp}] {action_type}")
                    print(f"  Reasoning: {reasoning}")
                    print("-" * 60)
        
        except KeyboardInterrupt:
            print()
            print("🛑 Stopping autonomous control...")
            await control_loop.stop()
            print("✅ Stopped")
            print()
            
            # Show summary
            history = control_loop.processor.get_action_history(limit=100)
            print(f"📈 Summary: {len(history)} actions executed")
    
    except Exception as e:
        logger.error(f"Demo error: {e}")
        print(f"❌ Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Make sure Computer Control API is running:")
        print("     python start_control_api.py")
        print("  2. Check Ollama is running and model is downloaded")
        print("  3. Check logs in logs/ollama_control.log")


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