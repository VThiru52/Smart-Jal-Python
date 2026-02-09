import asyncio
import logging
from unittest.mock import MagicMock, patch
from app.services.gemini_service import GeminiService

# Configure logging to see our warnings
logging.basicConfig(level=logging.WARNING)

async def test_fallback():
    print("Testing Gemini 429 Fallback...")
    
    # Initialize service
    service = GeminiService()
    
    # Mock the client to raise an exception
    mock_client = MagicMock()
    mock_models = MagicMock()
    
    # Create an exception that looks like the Google API error
    error_message = "429 RESOURCE_EXHAUSTED: Quota exceeded"
    mock_models.generate_image.side_effect = Exception(error_message)
    
    # Forcefully replace the client with a Mock, bypassing the read-only property issue
    service.client = MagicMock()
    service.client.models = mock_models
    # Ensure api_key is set to bypass the early return if it wasn't already
    service.api_key = "dummy_key"

    # Test generation
    prompt = "check dam"
    result = await service.generate_image_from_text(prompt)
    
    print(f"\nResulting URL: {result}")
    
    if "pollinations.ai" in result:
        print("SUCCESS: Fallback to Pollinations triggered.")
    else:
        print("FAILURE: Did not fallback to Pollinations.")

    if "flux" in result:
        print("SUCCESS: Enhanced model 'flux' parameter found.")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_fallback())
