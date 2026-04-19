-- =================================================================================
-- Procurement Data Platform Schema
-- Run this script in your Supabase SQL Editor to create the necessary tables.
-- =================================================================================

-- Drop existing tables completely (as requested)
DROP TABLE IF EXISTS report_data CASCADE;
DROP TABLE IF EXISTS reports CASCADE;
DROP TABLE IF EXISTS bot_configurations CASCADE;
DROP TABLE IF EXISTS sectors CASCADE;
DROP TABLE IF EXISTS companies CASCADE;

-- 1. Companies Table
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Sectors Table (Divisions within a company)
CREATE TABLE sectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Reports Table (Upload sessions)
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sector_id UUID NOT NULL REFERENCES sectors(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'processing', -- processing, completed, failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Report Data Table (Actual row-level classified data)
CREATE TABLE report_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    raw_data JSONB NOT NULL,
    classified_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Bot Configurations Table (Code/Prompts used for classification)
CREATE TABLE bot_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sector_id UUID REFERENCES sectors(id) ON DELETE CASCADE,
    version_name TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create some default mock data so you can test immediately
INSERT INTO companies (name) VALUES ('Adani') RETURNING id;

-- Note: In your python application, you will insert the actual data.
