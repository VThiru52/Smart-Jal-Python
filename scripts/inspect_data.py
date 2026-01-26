import pandas as pd
import json
import os

def inspect():
    results = {}
    master_path = 'd:/Smart Jal/backend/database/SmartJal/WaterLevels_Krishna/master data_updated.xlsx'
    if os.path.exists(master_path):
        xl = pd.ExcelFile(master_path)
        results['sheets'] = xl.sheet_names
        for sheet in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=sheet)
            # Convert columns to string labels to avoid datetime key errors in JSON
            df.columns = [str(c) for c in df.columns]
            results[f'sheet_{sheet}_cols'] = df.columns.tolist()
            results[f'sheet_{sheet}_head'] = df.head(5).astype(str).to_dict(orient='records')
    
    with open('d:/Smart Jal/backend/database/data_inspection.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

if __name__ == "__main__":
    inspect()
