"""
Demo: Autonomous Computer Control with IBM Watsonx
Shows how to use AI-driven computer control with periodic screenshots
"""

import asyncio
import os
from dotenv import load_dotenv

from ai_control_processor import AutonomousControlLoop
from logger import setup_logger

# Setup logging
logger = setup_logger(__name__, log_file='logs/autonomous_control.log')

# Load environment variables
load_dotenv()


async def main():
    """Main demo function."""
    
    print("=" * 60)
    print("Edward Autonomous Computer Control Demo")
    print("Powered by IBM Watsonx Vision AI")
    print("=" * 60)
    print()
    
    # Get credentials from environment
    watsonx_api_key = os.getenv("WATSONX_API_KEY")
    watsonx_project_id = os.getenv("WATSONX_PROJECT_ID")
    watsonx_url = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    
    if not watsonx_api_key or not watsonx_project_id:
        print("❌ Error: Missing Watsonx credentials!")
        print("Please set WATSONX_API_KEY and WATSONX_PROJECT_ID in your .env file")
        return
    
    # Get task from user
    print("What would you like the AI to help you with?")
    print("Examples:")
    print("  - Open Notepad and type 'Hello World'")
    print("  - Search for 'Python tutorials' in my browser")
    print("  - Navigate to a specific website")
    print()
    
    task = input("Enter task description: ").strip()
    
    if not task:
        task = "Observe the screen and assist with any tasks"
    
    print()
    print(f"Task: {task}")
    print()
    
    # Configuration
    screenshot_interval = float(os.getenv("SCREENSHOT_INTERVAL", "2.0"))
    auto_execute = os.getenv("AUTO_EXECUTE_ACTIONS", "false").lower() == "true"
    
    print("Configuration:")
    print(f"  Screenshot Interval: {screenshot_interval}s")
    print(f"  Auto-Execute Actions: {auto_execute}")
    print()
    
    if not auto_execute:
        print("⚠️  Auto-execute is disabled. Actions will be logged but not executed.")
        print("   Set AUTO_EXECUTE_ACTIONS=true in .env to enable execution.")
        print()
    
    # Create control loop
    try:
        control_loop = AutonomousControlLoop(
            watsonx_api_key=watsonx_api_key,
            watsonx_project_id=watsonx_project_id,
            task_description=task,
            screenshot_interval=screenshot_interval,
            watsonx_url=watsonx_url,
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
                    
                    print(f"Last Action: {action_type}")
                    print(f"Reasoning: {reasoning}")
                    print("-" * 60)
        
        except KeyboardInterrupt:
            print()
            print("Stopping autonomous control...")
            await control_loop.stop()
            print("✅ Stopped")
    
    except Exception as e:
        logger.error(f"Demo error: {e}")
        print(f"❌ Error: {e}")
        print()
        print("Make sure:")
        print("  1. Computer Control API is running (python start_control_api.py)")
        print("  2. Watsonx credentials are correct")
        print("  3. You have internet connection")


def run_demo():
    """Run the demo."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")


if __name__ == "__main__":
    run_demo()


# Made with Bob