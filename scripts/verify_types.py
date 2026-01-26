import pandas as pd
import numpy as np
import json

def test_numpy_serialization():
    print("Testing Numpy serialization fix...")
    
    # Create a dummy dataframe with numpy types
    data = {
        'crop_type': ['Rice', 'Rice', 'Cotton', 'Cotton'],
        'season': ['Kharif', 'Rabi', 'Kharif', 'Rabi'],
        'area_acres': [10.5, 12.5, 5.0, 7.5]
    }
    df = pd.DataFrame(data)
    
    print("\nData Types:")
    print(df.dtypes)
    
    try:
        # 1. Unsafe way (which was failing)
        unsafe_dict = df.groupby('crop_type')['area_acres'].sum().to_dict()
        print("\nUnsafe Result (Direct to_dict):", unsafe_dict)
        
        # Check types
        for k, v in unsafe_dict.items():
            print(f"Key: {k} ({type(k)}), Value: {v} ({type(v)})")
            
        # Try to serialize
        try:
            json.dumps(unsafe_dict)
            print("Unsafe dict serialized OK (native types might be returned by simple aggregation)")
        except TypeError as e:
            print(f"Unsafe dict FAILED serialization: {e}")

        # 2. Safe way (my fix)
        safe_dict = {str(k): float(v) for k, v in df.groupby('crop_type')['area_acres'].sum().to_dict().items()}
        print("\nSafe Result (Explicit cast):", safe_dict)
        
        # Check types
        for k, v in safe_dict.items():
            print(f"Key: {k} ({type(k)}), Value: {v} ({type(v)})")
            
        json.dumps(safe_dict)
        print("Safe dict serialized SUCCESSFULLY.")
        
    except Exception as e:
        print(f"Test Failed: {e}")

if __name__ == "__main__":
    test_numpy_serialization()
