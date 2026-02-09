import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def test_imagen4_models():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
    
    # Potential model names based on the user's description
    potential_models = [
        "imagen-4-fast-generate",
        "imagen-4.0-fast-generate",
        "imagen-4-fast-001",
        "imagen-4.0-fast-generate-001",
        "gemini-2.0-flash-exp-image-generation"  # From the earlier list
    ]
    
    prompt = "A water conservation structure in a rural village, photorealistic"
    
    for model in potential_models:
        print(f"\nTesting: {model}")
        try:
            response = client.models.generate_image(
                model=model,
                prompt=prompt,
                config={'number_of_images': 1}
            )
            if response.generated_images:
                print(f"[SUCCESS] {model} works!")
                return model
        except Exception as e:
            error_str = str(e)
            if "404" in error_str:
                print(f"[SKIP] Not found")
            else:
                print(f"[ERROR] {e}")
    
    print("\nNone of the tested models worked.")
    return None

if __name__ == "__main__":
    working_model = test_imagen4_models()
    if working_model:
        print(f"\n{'='*50}")
        print(f"RECOMMENDED MODEL: {working_model}")
        print(f"{'='*50}")
