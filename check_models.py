import os
from dotenv import load_dotenv
from google import genai
from openai import OpenAI
from anthropic import Anthropic

# Load environment variables
load_dotenv()

def check_gemini():
    print("\n--- Checking Google Gemini ---")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found.")
        return

    try:
        client = genai.Client(api_key=api_key)
        # Using the specific model we set in the backend
        response = client.models.generate_content(
            model='gemini-2.0-flash', 
            contents='Say hello!'
        )
        print(f"✅ Gemini Success: {response.text}")
    except Exception as e:
        print(f"❌ Gemini Failed: {e}")

def check_openai():
    print("\n--- Checking OpenAI (GPT-4) ---")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found.")
        return

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": "Say hello!"}]
        )
        print(f"✅ OpenAI Success: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ OpenAI Failed: {e}")

def check_anthropic():
    print("\n--- Checking Anthropic (Claude 3) ---")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found.")
        return

    try:
        client = Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=100,
            messages=[{"role": "user", "content": "Say hello!"}]
        )
        print(f"✅ Anthropic Success: {message.content[0].text}")
    except Exception as e:
        print(f"❌ Anthropic Failed: {e}")

if __name__ == "__main__":
    print("🔍 Starting Model Access Check...")
    check_gemini()
    check_openai()
    check_anthropic()
    print("\nDone.")