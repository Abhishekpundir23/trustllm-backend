import os
from google import genai
from dotenv import load_dotenv

# 1. Load your API Key
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in .env file")
    exit()

print(f"🔑 Checking models for API Key: {api_key[:5]}...{api_key[-4:]}")

try:
    # 2. Connect to Google
    client = genai.Client(api_key=api_key)
    
    # 3. List all available models (Simple Version)
    print("\n📋 Available Models for YOU:")
    print("-" * 30)
    
    for model in client.models.list():
        # Just print the name directly
        print(f"✅ {model.name}")

except Exception as e:
    print(f"\n❌ CRITICAL ERROR: {e}")