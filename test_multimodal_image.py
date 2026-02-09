
import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import io

load_dotenv()

def test_multimodal_generation():
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    model_name = "models/nano-banana-pro-preview" 
    # Or 'models/gemini-3-pro-image-preview'
    
    model = genai.GenerativeModel(model_name)
    
    prompt = "Generate an image of a futuristic water conservation structure, photorealistic."
    
    print(f"Prompting {model_name} with: {prompt}")
    
    try:
        response = model.generate_content(prompt)
        print("Response received.")
        
        if response.parts:
            print(f"Number of parts: {len(response.parts)}")
            for part in response.parts:
                 print(f"Part type provided: {part}")
                 # Check if part has image
        else:
             print("No parts in response. Text: ", response.text)
             
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_multimodal_generation()
