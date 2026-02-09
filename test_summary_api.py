import requests
import json

def test_summary():
    base_url = "http://127.0.0.1:8000/api/v1/pumping/summary"
    
    print("Testing summary for Krishna district (All Villages):")
    r = requests.get(base_url, params={"district": "Krishna"})
    data = r.json()
    print(f"Drinking Water: {data.get('drinking_water_m3')}")
    print(f"Total population: {data.get('total_population')}")

    print("\nTesting summary for Aswaraopalem village:")
    r = requests.get(base_url, params={"district": "Krishna", "village": "Aswaraopalem"})
    data = r.json()
    print(f"Drinking Water: {data.get('drinking_water_m3')}")
    print(f"Total population: {data.get('total_population')}")

if __name__ == "__main__":
    test_summary()
