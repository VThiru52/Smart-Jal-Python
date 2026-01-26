
import os
import sys
# Add the backend directory to the python path
sys.path.append("d:/Smart Jal/backend")

from app.core.supabase import get_supabase_admin

def debug_insert():
    s = get_supabase_admin()
    
    # 1. Test Risk Level
    print("\n--- Testing Risk Level ---")
    try: 
        s.table('villages').insert({'name':'TestRisk_LOW', 'district':'Krishna', 'risk_level':'LOW'}).execute()
        print('✅ Risk LOW Success')
    except Exception as e: 
        print(f'❌ Risk LOW Failed: {e}')
        
    try: 
        s.table('villages').insert({'name':'TestRisk_Low', 'district':'Krishna', 'risk_level':'Low'}).execute()
        print('✅ Risk Title Case Success')
    except Exception as e: 
        print(f'❌ Risk Title Case Failed: {e}')

    # 2. Test Latitude
    print("\n--- Testing Latitude ---")
    try: 
        s.table('villages').insert({'name':'TestLat', 'district':'Krishna', 'latitude': 16.5}).execute()
        print('✅ Latitude 16.5 Success')
    except Exception as e: 
        print(f'❌ Latitude 16.5 Failed: {e}')

    # 3. Test Population
    print("\n--- Testing Population ---")
    try: 
        s.table('villages').insert({'name':'TestPop', 'district':'Krishna', 'population': 1000}).execute()
        print('✅ Population 1000 Success')
    except Exception as e: 
        print(f'❌ Population 1000 Failed: {e}')

    # 4. Test Mandal
    print("\n--- Testing Mandal ---")
    try: 
        s.table('villages').insert({'name':'TestMandal', 'district':'Krishna', 'mandal': 'Movva'}).execute()
        print('✅ Mandal Movva Success')
    except Exception as e: 
        print(f'❌ Mandal Movva Failed: {e}')

    # 5. Test Total Area
    print("\n--- Testing Total Area ---")
    try: 
        s.table('villages').insert({'name':'TestArea', 'district':'Krishna', 'total_area_ha': 500.5}).execute()
        print('✅ Area 500.5 Success')
    except Exception as e: 
        print(f'❌ Area 500.5 Failed: {e}')

    # 6. Test FULL Record
    print("\n--- Testing FULL Record ---")
    try: 
        payload = {
            "name": "FullRecordTest",
            "district": "Krishna",
            "mandal": "Movva",
            "population": 5000,
            "total_area_ha": 500.5,
            "risk_level": "Low",
            "latitude": 16.5,
            "longitude": 81.0
        }
        s.table('villages').insert(payload).execute()
        print('✅ FULL Record Success')
    except Exception as e: 
        print(f'❌ FULL Record Failed: {e}')

if __name__ == "__main__":
    debug_insert()
