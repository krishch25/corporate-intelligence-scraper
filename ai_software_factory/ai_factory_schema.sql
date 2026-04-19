-- =================================================================================
-- AI Software Factory Schema
-- Run this in your Supabase SQL Editor to create all required tables.
-- =================================================================================

-- Drop existing AI Factory tables if they exist
DROP TABLE IF EXISTS factory_data_snapshots CASCADE;
DROP TABLE IF EXISTS factory_classification_rules CASCADE;
DROP TABLE IF EXISTS factory_code_versions CASCADE;
DROP TABLE IF EXISTS factory_step_logs CASCADE;
DROP TABLE IF EXISTS factory_runs CASCADE;
DROP TABLE IF EXISTS factory_projects CASCADE;

-- 1. Projects: top-level grouping (e.g., "Adani Procurement Q1")
CREATE TABLE factory_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Runs: each time the pipeline executes
CREATE TABLE factory_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES factory_projects(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'running',      -- running, success, failed, max_iterations
    input_source TEXT NOT NULL,                   -- 'file_upload' or 'supabase_import'
    input_row_count INTEGER,
    output_row_count INTEGER,
    total_iterations INTEGER DEFAULT 0,
    goal_description TEXT,
    desired_schema TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- 3. Step logs: one row per agent execution
CREATE TABLE factory_step_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES factory_runs(id) ON DELETE CASCADE,
    step_name TEXT NOT NULL,          -- 'analyzer', 'coder', 'evaluator', 'executor', 'evolution', 'finale'
    iteration INTEGER DEFAULT 0,
    input_summary TEXT,               -- what went into this step
    output_summary TEXT,              -- what came out
    duration_ms INTEGER,
    status TEXT DEFAULT 'running',    -- running, completed, failed
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Code versions: every code the Coder generates is saved
CREATE TABLE factory_code_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES factory_runs(id) ON DELETE CASCADE,
    iteration INTEGER NOT NULL,
    generated_code TEXT NOT NULL,
    is_safe BOOLEAN,
    execution_success BOOLEAN,
    review_notes TEXT,
    error_log TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Classification rules: learned mappings (the "memory")
CREATE TABLE factory_classification_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES factory_projects(id) ON DELETE CASCADE,
    material_type TEXT NOT NULL,
    l0 TEXT NOT NULL,
    l1 TEXT NOT NULL,
    l2 TEXT NOT NULL,
    l3 TEXT NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    source TEXT DEFAULT 'llm',       -- 'llm' or 'manual'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, material_type)
);

-- 6. Input/output data snapshots (stored as JSONB arrays)
CREATE TABLE factory_data_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES factory_runs(id) ON DELETE CASCADE,
    snapshot_type TEXT NOT NULL,      -- 'input' or 'output'
    data JSONB NOT NULL,             -- array of row objects
    row_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Helper indexes for performance
CREATE INDEX idx_runs_project ON factory_runs(project_id);
CREATE INDEX idx_step_logs_run ON factory_step_logs(run_id);
CREATE INDEX idx_code_versions_run ON factory_code_versions(run_id);
CREATE INDEX idx_classification_rules_project ON factory_classification_rules(project_id);
CREATE INDEX idx_data_snapshots_run ON factory_data_snapshots(run_id);
