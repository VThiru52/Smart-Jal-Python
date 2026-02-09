
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_KEY')}"}

def query(payload):
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.content

def test_huggingface_image():
    print("Testing Hugging Face Image Generation...")
    print(f"Key present: {bool(os.getenv('HUGGINGFACE_API_KEY'))}")
    
    prompt = "A futuristic water conservation structure in a rural Indian village, drone view, photorealistic, 8k"
    image_bytes = query({
        "inputs": prompt,
    })
    
    if len(image_bytes) > 1000: # Assuming valid image is large
        print("Success! Image generated.")
        with open("test_hf_image.png", "wb") as f:
            f.write(image_bytes)
        print("Saved to test_hf_image.png")
    else:
        print(f"Failed. Response: {image_bytes}")

if __name__ == "__main__":
    test_huggingface_image()
