
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

def list_models():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ No API key found in .env")
        return

    client = genai.Client(api_key=api_key)
    print("📡 Fetching available models...")
    try:
        for model in client.models.list():
            print(f"- {model.name}")
    except Exception as e:
        print(f"❌ Failed to list models: {e}")

if __name__ == "__main__":
    list_models()
