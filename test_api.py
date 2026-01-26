
from fastapi.testclient import TestClient
from app.main import app
import sys
import os

sys.path.append(os.path.abspath("d:/Smart Jal/backend"))

client = TestClient(app)

def test_districts_endpoint():
    print("Testing /api/v1/village/districts endpoint...")
    try:
        response = client.get("/api/v1/village/districts")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Test Execution Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_districts_endpoint()
