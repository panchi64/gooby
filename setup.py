#!/usr/bin/env python3
"""
Gooby Bot Setup Script
Run this to set up Gooby for the first time!
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a shell command with error handling"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    print("🫘 Welcome to Gooby Bot Setup! 🫘")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("bot.py").exists():
        print("❌ Please run this script from the gooby project directory!")
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required!")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Create virtual environment
    if not Path("gooby-env").exists():
        if not run_command("python3 -m venv gooby-env", "Creating virtual environment"):
            sys.exit(1)
    else:
        print("✅ Virtual environment already exists")
    
    # Install dependencies
    if not run_command("gooby-env/bin/pip install -r requirements.txt", "Installing dependencies"):
        sys.exit(1)
    
    # Create .env if it doesn't exist
    if not Path(".env").exists():
        if Path(".env.example").exists():
            if not run_command("cp .env.example .env", "Creating .env file"):
                sys.exit(1)
            print("\n⚠️  IMPORTANT: Edit .env file with your Discord token and server ID!")
        else:
            print("❌ .env.example file not found!")
    else:
        print("✅ .env file already exists")
    
    # Create data directory
    Path("data").mkdir(exist_ok=True)
    print("✅ Data directory created")
    
    print("\n" + "=" * 50)
    print("🎉 Gooby setup complete! 🎉")
    print("\nNext steps:")
    print("1. Edit .env file with your Discord token and server ID")
    print("2. Start LM Studio and load a model")
    print("3. Run: source gooby-env/bin/activate && python bot.py")
    print("\nGooby says: 'Thanks for setting me up, you wonderful goober!' 🫘")

if __name__ == "__main__":
    main()