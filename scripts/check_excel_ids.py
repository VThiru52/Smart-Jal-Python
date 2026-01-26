
import pandas as pd
import os

def check_excel_ids():
    excel_path = 'd:/Smart Jal/backend/database/SmartJal/WaterLevels_Krishna/master data_updated.xlsx'
    df = pd.read_excel(excel_path)
    print(f"Sample IDs: {df['ID'].head().tolist()}")
    print(f"Sample Village names: {df['Village Name'].head().tolist()}")

if __name__ == "__main__":
    check_excel_ids():
