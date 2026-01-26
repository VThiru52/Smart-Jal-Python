# Districts Table Setup

## Overview
This migration sets up the `districts` table and inserts Krishna district data. This is **required** for the Villages Registry feature to work properly.

## Migration Files

1. **20240114_add_districts_table.sql** - Creates the districts table structure (run first)
2. **20250115_insert_krishna_district.sql** - Inserts Krishna district data (includes table creation check, safe to run standalone)

## Quick Start

### Recommended: Run the Insert Migration (Safest)

The `20250115_insert_krishna_district.sql` file includes table creation checks, so you can run it directly:

```sql
-- Copy and paste the entire contents of 20250115_insert_krishna_district.sql
-- into Supabase SQL Editor and execute
```

### Option 1: Using Supabase Dashboard (Recommended for Production)

1. Log into your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Click **New Query**
4. Copy the entire contents of `20250115_insert_krishna_district.sql`
5. Paste into the SQL Editor
6. Click **Run** or press `Ctrl+Enter`
7. Verify success message: "Krishna district inserted successfully"

### Option 2: Using psql Command Line

```bash
# Connect to your Supabase database
psql "postgresql://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres"

# Run the migration
\i backend/database/migrations/20250115_insert_krishna_district.sql

# Or copy-paste the SQL directly
```

### Option 3: Using Supabase CLI

```bash
# Navigate to your project root
cd "D:\Smart Jal"

# Run migration
supabase db execute -f backend/database/migrations/20250115_insert_krishna_district.sql
```

## Verification

After running the migration, verify the data:

```sql
-- Check if districts table exists and has data
SELECT id, name, created_at, updated_at FROM districts ORDER BY name;

-- Expected output:
-- id                                   | name    | created_at              | updated_at
-- -------------------------------------+---------+-------------------------+-------------------------
-- [uuid]                                | Krishna | 2025-01-15 10:00:00+00  | 2025-01-15 10:00:00+00
```

## Troubleshooting

### Error: "relation districts does not exist"
- **Solution**: Run `20240114_add_districts_table.sql` first, then run `20250115_insert_krishna_district.sql`

### Error: "duplicate key value violates unique constraint"
- **Solution**: This is normal if Krishna district already exists. The migration uses `ON CONFLICT` to handle this gracefully.

### No districts showing in frontend
- **Check**: Verify the districts table has data: `SELECT * FROM districts;`
- **Check**: Verify RLS policies allow read access
- **Check**: Check browser console for API errors

## Adding More Districts

To add more districts in the future, use this SQL template:

```sql
INSERT INTO districts (name, boundary, created_at, updated_at)
VALUES (
    'District Name',
    ST_SetSRID(
        ST_GeomFromText('MULTIPOLYGON(((...coordinates...)))'),
        4326
    ),
    NOW(),
    NOW()
)
ON CONFLICT (name) DO UPDATE 
SET 
    updated_at = NOW(),
    boundary = EXCLUDED.boundary;
```

## Table Structure

```sql
CREATE TABLE districts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    boundary GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Notes

- The districts table uses PostGIS for spatial data
- Row Level Security (RLS) is enabled with public read access
- The boundary geometry is optional but recommended for mapping features
- All villages in the system are currently associated with Krishna district
