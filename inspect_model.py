import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def inspect_model():
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    target_models = ["models/nano-banana-pro-preview", "models/gemini-3-pro-image-preview"]
    
    print("Inspecting models...")
    for m in genai.list_models():
        if m.name in target_models:
             print(f"Name: {m.name}")
             print(f"Methods: {m.supported_generation_methods}")
             print("-" * 20)

if __name__ == "__main__":
    inspect_model()
