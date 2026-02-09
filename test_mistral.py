
import asyncio
import os
from mistralai import Mistral
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_mistral():
    api_key = os.getenv("MISTRAL_API_KEY")
    print(f"Testing Mistral AI with key: {api_key[:5]}...")
    
    if not api_key:
        print("Error: MISTRAL_API_KEY not found.")
        return

    try:
        client = Mistral(api_key=api_key)
        response = await client.chat.complete_async(
            model='mistral-large-latest',
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"Mistral Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mistral())
