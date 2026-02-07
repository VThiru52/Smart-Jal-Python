
import asyncio
import os
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

async def test_async_mistral():
    api_key = os.getenv("MISTRAL_API_KEY")
    client = Mistral(api_key=api_key)
    
    print("Testing chat.complete_async...")
    try:
        response = await client.chat.complete_async(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": "Say hello in JSON format"}],
            response_format={"type": "json_object"}
        )
        print("Success!")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_async_mistral())
