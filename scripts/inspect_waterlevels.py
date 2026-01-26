import pandas as pd
import os

file_path = r'd:/Smart Jal/backend/database/SmartJal/WaterLevels_Krishna/master data_updated.xlsx'

print(f"Reading {file_path}...")
try:
    # Read just header and first few rows
    df = pd.read_excel(file_path, nrows=5)
    with open('columns.txt', 'w', encoding='utf-8') as f:
        f.write("Columns found:\n")
        for col in df.columns:
            f.write(f"{col}\n")
        f.write("\nFirst row sample:\n")
        f.write(str(df.iloc[0]))
    print("Done writing columns.txt")
except Exception as e:
    print(f"Error: {e}")
