"""
Supabase client for the AI Software Factory.
Handles all database operations: projects, runs, step logs, code versions,
classification rules, and data snapshots.
"""
import json
import traceback
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from app.core.config import settings


def get_supabase() -> Client:
    """Returns a Supabase client instance."""
    return create_client(settings.supabase_url, settings.supabase_key)


# ─── Projects ────────────────────────────────────────────────────────────────

def create_project(name: str, description: str = "") -> dict:
    """Create a new project and return the record."""
    sb = get_supabase()
    result = sb.table("factory_projects").insert({
        "name": name,
        "description": description
    }).execute()
    return result.data[0] if result.data else {}


def get_project(project_id: str) -> dict:
    sb = get_supabase()
    result = sb.table("factory_projects").select("*").eq("id", project_id).execute()
    return result.data[0] if result.data else {}


def list_projects() -> list:
    sb = get_supabase()
    result = sb.table("factory_projects").select("*").order("created_at", desc=True).execute()
    return result.data or []


# ─── Runs ─────────────────────────────────────────────────────────────────────

def create_run(project_id: str, input_source: str, goal: str, schema: str, input_row_count: int = 0) -> dict:
    """Create a new pipeline run record."""
    sb = get_supabase()
    result = sb.table("factory_runs").insert({
        "project_id": project_id,
        "input_source": input_source,
        "goal_description": goal,
        "desired_schema": schema,
        "input_row_count": input_row_count,
        "status": "running"
    }).execute()
    return result.data[0] if result.data else {}


def update_run_status(run_id: str, status: str, output_row_count: int = None, total_iterations: int = None):
    """Update the status of a run."""
    sb = get_supabase()
    update_data = {
        "status": status,
        "completed_at": datetime.now(timezone.utc).isoformat()
    }
    if output_row_count is not None:
        update_data["output_row_count"] = output_row_count
    if total_iterations is not None:
        update_data["total_iterations"] = total_iterations
    sb.table("factory_runs").update(update_data).eq("id", run_id).execute()


def get_runs_for_project(project_id: str) -> list:
    sb = get_supabase()
    result = sb.table("factory_runs").select("*").eq("project_id", project_id).order("started_at", desc=True).execute()
    return result.data or []


# ─── Step Logs ────────────────────────────────────────────────────────────────

def log_step_start(run_id: str, step_name: str, iteration: int = 0, input_summary: str = "") -> dict:
    """Log the start of a pipeline step."""
    sb = get_supabase()
    result = sb.table("factory_step_logs").insert({
        "run_id": run_id,
        "step_name": step_name,
        "iteration": iteration,
        "input_summary": input_summary[:2000] if input_summary else "",
        "status": "running"
    }).execute()
    return result.data[0] if result.data else {}


def log_step_complete(step_log_id: str, output_summary: str = "", duration_ms: int = 0, status: str = "completed"):
    """Update a step log with completion info."""
    sb = get_supabase()
    sb.table("factory_step_logs").update({
        "output_summary": output_summary[:2000] if output_summary else "",
        "duration_ms": duration_ms,
        "status": status
    }).eq("id", step_log_id).execute()


def get_step_logs(run_id: str) -> list:
    sb = get_supabase()
    result = sb.table("factory_step_logs").select("*").eq("run_id", run_id).order("created_at").execute()
    return result.data or []


# ─── Code Versions ────────────────────────────────────────────────────────────

def save_code_version(run_id: str, iteration: int, code: str, is_safe: bool = None,
                      execution_success: bool = None, review_notes: str = "", error_log: str = "") -> dict:
    """Save a generated code version."""
    sb = get_supabase()
    record = {
        "run_id": run_id,
        "iteration": iteration,
        "generated_code": code,
        "review_notes": review_notes[:2000] if review_notes else "",
        "error_log": error_log[:2000] if error_log else ""
    }
    if is_safe is not None:
        record["is_safe"] = is_safe
    if execution_success is not None:
        record["execution_success"] = execution_success
    result = sb.table("factory_code_versions").insert(record).execute()
    return result.data[0] if result.data else {}


def update_code_version(code_version_id: str, is_safe: bool = None,
                        execution_success: bool = None, review_notes: str = None, error_log: str = None):
    """Update an existing code version with evaluation/execution results."""
    sb = get_supabase()
    update_data = {}
    if is_safe is not None:
        update_data["is_safe"] = is_safe
    if execution_success is not None:
        update_data["execution_success"] = execution_success
    if review_notes is not None:
        update_data["review_notes"] = review_notes[:2000]
    if error_log is not None:
        update_data["error_log"] = error_log[:2000]
    if update_data:
        sb.table("factory_code_versions").update(update_data).eq("id", code_version_id).execute()


# ─── Classification Rules ────────────────────────────────────────────────────

def save_classification_rules(project_id: str, rules: List[Dict[str, str]]):
    """
    Save classification rules. Each rule is a dict with:
    material_type, l0, l1, l2, l3
    Uses upsert to update existing rules.
    """
    sb = get_supabase()
    records = []
    for rule in rules:
        records.append({
            "project_id": project_id,
            "material_type": rule["material_type"],
            "l0": rule["l0"],
            "l1": rule["l1"],
            "l2": rule["l2"],
            "l3": rule["l3"],
            "confidence": rule.get("confidence", 1.0),
            "source": rule.get("source", "llm")
        })
    if records:
        sb.table("factory_classification_rules").upsert(
            records, on_conflict="project_id,material_type"
        ).execute()


def get_classification_rules(project_id: str) -> list:
    sb = get_supabase()
    result = sb.table("factory_classification_rules").select("*").eq("project_id", project_id).execute()
    return result.data or []


# ─── Data Snapshots ───────────────────────────────────────────────────────────

def save_data_snapshot(run_id: str, snapshot_type: str, data: List[Dict], row_count: int = None):
    """
    Save a data snapshot (input or output).
    data is a list of row dicts. We chunk it if too large.
    """
    sb = get_supabase()
    # Limit to first 200 rows to avoid Supabase payload limits
    capped_data = data[:200]
    sb.table("factory_data_snapshots").insert({
        "run_id": run_id,
        "snapshot_type": snapshot_type,
        "data": capped_data,
        "row_count": row_count or len(data)
    }).execute()


def get_data_snapshot(run_id: str, snapshot_type: str) -> list:
    sb = get_supabase()
    result = sb.table("factory_data_snapshots").select("*").eq("run_id", run_id).eq("snapshot_type", snapshot_type).execute()
    return result.data or []


# ─── Import from Supabase ────────────────────────────────────────────────────

def get_data_from_table(table_name: str, columns: str = "*", limit: int = 1000) -> list:
    """Fetch data from any Supabase table for use as pipeline input."""
    sb = get_supabase()
    result = sb.table(table_name).select(columns).limit(limit).execute()
    return result.data or []


# ─── Safe wrapper for DB ops ─────────────────────────────────────────────────

def safe_db_call(func, *args, **kwargs):
    """Wraps a DB function call so pipeline doesn't crash on DB errors."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"[DB WARNING] {func.__name__} failed: {e}")
        return None
