import pandas as pd
import math

def generate_sql():
    master_path = 'd:/Smart Jal/backend/database/master data_updated.xlsx'
    output_path = 'd:/Smart Jal/backend/database/generated_data_import.sql'
    
    # 1. Load Data
    xl = pd.ExcelFile(master_path)
    df_meta = pd.read_excel(xl, 'meta-historical')
    
    sql_statements = []
    
    # Enable PostGIS if not enabled
    sql_statements.append("-- Enable PostGIS\nCREATE EXTENSION IF NOT EXISTS postgis;\n")

    # 2. Process Villages
    # Get unique Mandal/Village combinations
    villages = df_meta[['Mandal Name', 'Village Name', 'District']].drop_duplicates()
    
    sql_statements.append("-- Ingest Villages")
    for _, row in villages.iterrows():
        mandal = str(row['Mandal Name']).replace("'", "''")
        village = str(row['Village Name']).replace("'", "''")
        district = str(row['District']).replace("'", "''")
        
        sql = f"INSERT INTO villages (name, district, sub_district) " \
              f"VALUES ('{village}', '{district}', '{mandal}') " \
              f"ON CONFLICT DO NOTHING;"
        sql_statements.append(sql)

    # 3. Process Piezometers
    sql_statements.append("\n-- Ingest Piezometers")
    for _, row in df_meta.iterrows():
        station_code = str(row['ID']).replace("'", "''")
        location = str(row['Location\n(Premises)']).replace("'", "''").strip()
        
        # Fallback for empty location name to satisfy NOT NULL constraint
        if location == 'nan' or not location:
            location_val = f"'Station {station_code}'"
        else:
            location_val = f"'{location}'"
        
        lat = row['Latitude \n(Decimal Degrees)']
        lon = row['Longitude \n(Decimal Degrees)']
        depth = row['Total \nDepth \nin m']
        v_name = str(row['Village Name']).replace("'", "''")
        
        if pd.isna(lat) or pd.isna(lon):
            continue

        # Handle NaN for depth
        depth_val = "NULL" if pd.isna(depth) else depth

        # Subquery to find village_id
        village_subquery = f"(SELECT id FROM villages WHERE name = '{v_name}' LIMIT 1)"
        
        sql = f"INSERT INTO piezometers (station_code, location_name, village_id, depth_m, geom) " \
              f"VALUES ('{station_code}', {location_val}, {village_subquery}, {depth_val}, ST_SetSRID(ST_Point({lon}, {lat}), 4326)) " \
              f"ON CONFLICT (station_code) DO UPDATE SET depth_m = EXCLUDED.depth_m, geom = EXCLUDED.geom;"
        sql_statements.append(sql)

    # 4. Process Stratification (Lithology)
    sql_statements.append("\n-- Create Strata table if not exists")
    sql_statements.append("CREATE TABLE IF NOT EXISTS piezometer_strata ("
                          "id UUID PRIMARY KEY DEFAULT gen_random_uuid(),"
                          "piezometer_id TEXT REFERENCES piezometers(station_code) ON DELETE CASCADE,"
                          "strata_order INT,"
                          "depth_from FLOAT,"
                          "depth_to FLOAT,"
                          "lithology TEXT,"
                          "created_at TIMESTAMPTZ DEFAULT NOW());")

    sql_statements.append("\n-- Ingest Stratification Data")
    df_strat = pd.read_excel(xl, 'stratification')
    
    # Create a mapping from SNo to Station ID using df_meta
    sno_to_id = dict(zip(df_meta['SNo'], df_meta['ID']))
    
    for _, row in df_strat.iterrows():
        sno = row.get('SNo')
        station_id = sno_to_id.get(sno)
        
        if not station_id:
            # Try to find Station ID in columns as fallback
            station_id = str(row.get('ID') or row.get('Station ID') or '')
        
        if station_id and station_id != 'nan':
            order = row.get('Strata Order (Top to Bottom)', 1)
            # Use positional indexing for depths if names are complex
            d_from = row.iloc[2] if len(row) > 2 else 0
            d_to = row.iloc[3] if len(row) > 3 else 0
            
            d_from_val = "NULL" if pd.isna(d_from) else d_from
            d_to_val = "NULL" if pd.isna(d_to) else d_to
            
            litho = str(row.iloc[4]).replace("'", "''") if len(row) > 4 else 'Unknown'
            if litho == 'nan': litho = 'NULL'
            else: litho = f"'{litho}'"

            sql = f"INSERT INTO piezometer_strata (piezometer_id, strata_order, depth_from, depth_to, lithology) " \
                  f"VALUES ('{station_id}', {order}, {d_from_val}, {d_to_val}, {litho});"
            sql_statements.append(sql)
        else:
            if not pd.isna(sno):
                print(f"⚠️ Warning: Could not find Station ID for SNo {sno} in stratification sheet.")

    # 5. Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(sql_statements))
    
    print(f"✅ Generated {len(sql_statements)} SQL statements in {output_path}")

if __name__ == "__main__":
    generate_sql()
