
import os
import asyncio
from dotenv import load_dotenv
from google import genai

load_dotenv()

def test_model():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
    
    prompt = "A futuristic water conservation structure, photorealistic"
    model = "nano-banana-pro-preview"
    
    print(f"Testing model: {model}")
    try:
        response = client.models.generate_image(
            model=model,
            prompt=prompt,
            config={'number_of_images': 1}
        )
        if response.generated_images:
            print("Success! Image generated.")
        else:
            print("Response received but no images.")
    except Exception as e:
        print(f"Error with {model}: {e}")

    # Also try gemini-3-pro-image-preview
    model2 = "gemini-3-pro-image-preview"
    print(f"\nTesting model: {model2}")
    try:
        response = client.models.generate_image(
            model=model2,
            prompt=prompt,
            config={'number_of_images': 1}
        )
        if response.generated_images:
            print("Success! Image generated.")
        else:
             print("Response received but no images.")
    except Exception as e:
        print(f"Error with {model2}: {e}")

if __name__ == "__main__":
    test_model()
