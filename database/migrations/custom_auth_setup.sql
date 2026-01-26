-- Create a custom users table in the public schema to bypass broken auth schema
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS public.app_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    designation TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert Admin User (Password: Admin@123)
-- We will verify using pgcrypto's crypt() function in the login query, or just store it here.
-- Using pgcrypto for storage:
INSERT INTO public.app_users (email, password_hash, full_name, designation)
VALUES (
    'admin@smartjal.gov.in',
    crypt('Admin@123', gen_salt('bf')),
    'District Administrator',
    'Joint Director'
) ON CONFLICT (email) DO NOTHING;
