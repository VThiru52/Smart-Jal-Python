import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def list_models():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        return

    genai.configure(api_key=api_key)
    
    print("Listing available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
             print(m.name)
    
if __name__ == "__main__":
    list_models()
