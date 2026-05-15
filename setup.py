"""
Edward Setup Script
Helps with initial configuration and setup
"""

import os
import sys
from pathlib import Path
import shutil


def create_directories():
    """Create necessary directories"""
    directories = ['data', 'logs', 'assets']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")


def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if env_file.exists():
        print("✓ .env file already exists")
        return
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✓ Created .env file from template")
        print("⚠ Please edit .env and add your API keys")
    else:
        print("✗ .env.example not found")


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    
    if version.major == 3 and version.minor >= 11:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    else:
        print(f"✗ Python 3.11+ required, found {version.major}.{version.minor}.{version.micro}")
        return False


def install_dependencies():
    """Install Python dependencies"""
    print("\nInstalling dependencies...")
    print("This may take a few minutes...\n")
    
    os.system(f"{sys.executable} -m pip install --upgrade pip")
    os.system(f"{sys.executable} -m pip install -r requirements.txt")
    
    print("\n✓ Dependencies installed")


def main():
    """Main setup function"""
    print("=" * 60)
    print("Edward Setup")
    print("=" * 60)
    print()
    
    # Check Python version
    if not check_python_version():
        print("\nPlease install Python 3.11 or higher")
        sys.exit(1)
    
    # Create directories
    print("\nCreating directories...")
    create_directories()
    
    # Create .env file
    print("\nSetting up configuration...")
    create_env_file()
    
    # Ask if user wants to install dependencies
    print("\n" + "=" * 60)
    response = input("Install Python dependencies? (y/n): ").lower().strip()
    
    if response == 'y':
        install_dependencies()
    else:
        print("\nSkipping dependency installation")
        print("Run 'pip install -r requirements.txt' manually when ready")
    
    # Final instructions
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Edit .env file and add your API keys:")
    print("   - ELEVENLABS_API_KEY")
    print("   - ELEVENLABS_VOICE_ID")
    print("   - IBM_BOB_API_URL")
    print("   - IBM_BOB_API_KEY")
    print("   - USER_NAME (your name)")
    print("\n2. Run Edward:")
    print("   python main.py")
    print("\n3. Press Win+Shift+E to activate Edward")
    print("\nEnjoy your AI assistant!")
    print()


if __name__ == "__main__":
    main()

# Made with Bob
