-- Run this SQL in your Supabase SQL Editor to add the required caching column
ALTER TABLE villages 
ADD COLUMN IF NOT EXISTS recommendations_cache JSONB;

-- Add a comment for clarity
COMMENT ON COLUMN villages.recommendations_cache IS 'Stores AI-generated water conservation recommendations and image URLs to prevent regeneration costs.';
