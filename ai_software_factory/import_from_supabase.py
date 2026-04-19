#!/usr/bin/env python3
"""
Import data from a Supabase table and run the AI Software Factory pipeline on it.

Usage:
    python import_from_supabase.py --table report_data --project "My Analysis"
    python import_from_supabase.py --table report_data --columns "raw_data" --limit 500
"""
import os
import sys
import json
import argparse
import pandas as pd
import time

from app.core.orchestrator import app
from app.db.supabase_client import (
    get_data_from_table, create_project, create_run, 
    save_data_snapshot, safe_db_call
)

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def main():
    parser = argparse.ArgumentParser(description="Import data from Supabase and run the AI pipeline")
    parser.add_argument("--table", required=True, help="Supabase table name to import from")
    parser.add_argument("--columns", default="*", help="Columns to select (comma-separated or '*')")
    parser.add_argument("--limit", type=int, default=1000, help="Max rows to import")
    parser.add_argument("--project", default="Supabase Import", help="Project name for this run")
    args = parser.parse_args()
    
    if HAS_RICH:
        console.print(Panel.fit(
            "[bold cyan]🏭  AI Software Factory — Supabase Import Mode[/bold cyan]",
            border_style="bright_blue"
        ))
    else:
        print("🏭  AI Software Factory — Supabase Import Mode")
    
    # 1. Fetch data from Supabase
    print(f"\n📥 Fetching data from table '{args.table}' (limit: {args.limit})...")
    data = safe_db_call(get_data_from_table, args.table, args.columns, args.limit)
    
    if not data:
        print("❌ No data returned from Supabase. Check table name and credentials.")
        sys.exit(1)
    
    print(f"  ✅ Fetched {len(data)} rows")
    
    # 2. Handle JSONB columns (flatten if needed)
    if len(data) > 0 and "raw_data" in data[0]:
        # Flatten the raw_data JSONB column
        flat_data = []
        for row in data:
            if isinstance(row.get("raw_data"), dict):
                flat_data.append(row["raw_data"])
            elif isinstance(row.get("raw_data"), str):
                flat_data.append(json.loads(row["raw_data"]))
            else:
                flat_data.append(row)
        data = flat_data
    
    # 3. Write to temporary Excel file
    df = pd.DataFrame(data)
    input_path = "data/supabase_import.xlsx"
    output_path = "data/supabase_output.xlsx"
    os.makedirs("data", exist_ok=True)
    df.to_excel(input_path, index=False)
    print(f"  ✅ Saved to {input_path}")
    print(f"  Columns: {list(df.columns)}")
    
    # 4. Create project and run in Supabase
    project = safe_db_call(create_project, args.project, f"Imported from table: {args.table}")
    project_id = project.get("id", "") if project else ""
    
    goal = "Transform imported procurement data with intelligent L0-L3 classification. No 'Other' values allowed."
    schema = "Auto-detect columns and classify into Pareto, Material Code, Supplier Name, Spend, L0, L1, L2, L3"
    
    run_record = safe_db_call(create_run, project_id, "supabase_import", goal, schema, len(df)) if project_id else None
    run_id = run_record.get("id", "") if run_record else ""
    
    if run_id:
        safe_db_call(save_data_snapshot, run_id, "input", data[:200], len(data))
    
    # 5. Run pipeline
    print(f"\n🚀 Running pipeline on {len(df)} rows...")
    
    initial_state = {
        "project_id": project_id,
        "run_id": run_id,
        "input_path": input_path,
        "output_path": output_path,
        "raw_data_schema": ", ".join(df.columns),
        "sample_data": "",
        "desired_output_schema": schema,
        "goal_description": goal,
        "iteration_count": 0,
        "error_history": [],
        "is_code_safe": False,
        "execution_success": False,
        "learned_context": ""
    }
    
    start = time.time()
    final_state = app.invoke(initial_state)
    elapsed = time.time() - start
    
    # 6. Display results
    print(f"\n{'='*50}")
    print(f"Status: {final_state.get('final_status', 'N/A')}")
    print(f"Time: {elapsed:.1f}s")
    
    if final_state.get("execution_success") and os.path.exists(output_path):
        df_out = pd.read_excel(output_path)
        print(f"Output: {output_path} ({len(df_out)} rows)")
        for col in ["L0", "L1", "L2", "L3"]:
            if col in df_out.columns:
                print(f"  {col}: {df_out[col].nunique()} unique values")
    else:
        print("❌ Pipeline failed.")
        print(final_state.get("execution_logs", ""))


if __name__ == "__main__":
    main()
