from google import genai
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_genai_image():
    print("Testing google-genai SDK for image generation...")
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'), http_options={'api_version': 'v1beta'})
    
    try:
        # Note: Using imagen-4.0-generate-001 as it's the one available in ListModels
        response = client.models.generate_image(
            model='imagen-4.0-generate-001',
            prompt='A high-tech water filtration system in a rural Indian village, sunrise background, realistic drone shot',
            config={
                'number_of_images': 1,
            }
        )
        
        for i, image in enumerate(response.generated_images):
            image.image.save(f'test_image_{i}.png')
            print(f"SUCCESS: Image saved as test_image_{i}.png")
            
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    asyncio.run(test_genai_image())
