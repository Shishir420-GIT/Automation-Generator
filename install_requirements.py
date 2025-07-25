#!/usr/bin/env python3
"""
Installation script for Automation Generator requirements
Run this if you're having import issues
"""

import subprocess
import sys

def install_requirements():
    """Install all required packages"""
    print("🔄 Installing Automation Generator requirements...")
    
    try:
        # Install from requirements.txt
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All requirements installed successfully!")
        
        # Test imports
        print("\n🧪 Testing imports...")
        
        try:
            import PyPDF2
            print(f"✅ PyPDF2 version {PyPDF2.__version__}")
        except ImportError:
            print("❌ PyPDF2 import failed")
            
        try:
            import streamlit
            print(f"✅ Streamlit version {streamlit.__version__}")
        except ImportError:
            print("❌ Streamlit import failed")
            
        try:
            import google.generativeai
            print("✅ Google Generative AI")
        except ImportError:
            print("❌ Google Generative AI import failed")
            
        try:
            import pymongo
            print("✅ PyMongo")
        except ImportError:
            print("❌ PyMongo import failed")
            
        print("\n🎉 Installation complete! You can now run:")
        print("   streamlit run app.py")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        print("\n💡 Try manually installing:")
        print("   pip install PyPDF2==3.0.1 streamlit>=1.28.0 google-generativeai pymongo tenacity")

if __name__ == "__main__":
    install_requirements()