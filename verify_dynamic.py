import requests

def test():
    base = "http://127.0.0.1:8000/api/v1/pumping/summary"
    villages = [
        {"name": "Anigandlapadu", "type": "Small (<2k)"},
        {"name": "Aswaraopalem", "type": "Medium (2k-10k)"},
        {"name": "China Yerukapadu", "type": "Large (>10k)"}
    ]
    
    for v in villages:
        r = requests.get(base, params={"district": "Krishna", "village": v['name']})
        data = r.json()
        total = data.get('drinking_water_m3') + data.get('household_needs_m3') + data.get('industrial_usage_m3')
        h_pct = data.get('household_needs_m3') / total * 100
        print(f"Village: {v['name']} ({v['type']}), Population: {data.get('total_population')}, Household %: {h_pct:.1f}%")

if __name__ == "__main__":
    test()
