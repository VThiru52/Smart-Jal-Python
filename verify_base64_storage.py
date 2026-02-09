import requests
import json

def verify_base64_response():
    base_url = "https://smart-jal-8dc060caa7ef.herokuapp.com/api/v1"
    village_id = "9dafe5ec-a568-49ca-85b7-364ab00fc286" # Ithavaram
    # Use a unique title to force generation or at least ensure we hit the detail logic
    title = f"AI Water Interventions"
    
    url = f"{base_url}/drought/recommendations/{village_id}/{title}"
    print(f"Requesting: {url}")
    
    try:
        response = requests.get(url, timeout=120)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            hero = data.get("hero", {})
            image = hero.get("image", "")
            
            if image.startswith("data:image"):
                print("SUCCESS: Received Base64 encoded image!")
                print(f"Image length: {len(image)} characters")
                print(f"Image prefix: {image[:50]}...")
            elif image.startswith("http"):
                print("INFO: Received external image URL (fallback or external).")
                print(f"URL: {image}")
            else:
                print(f"FAILURE: Unexpected image format: {image[:100]}")
        else:
            print(f"FAILURE: API returned error: {response.text}")
            
    except Exception as e:
        print(f"FAILURE: Request error: {e}")

if __name__ == "__main__":
    verify_base64_response()
