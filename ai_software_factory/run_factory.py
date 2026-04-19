#!/usr/bin/env python3
"""
AI Software Factory — Main Runner
Runs the LangGraph pipeline on real-world procurement data with full Supabase logging.
"""
import os
import sys
import time
import pandas as pd

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from app.core.orchestrator import app
from app.core.state import AgentState
from app.db.supabase_client import (
    create_project, create_run, save_data_snapshot,
    get_classification_rules, safe_db_call
)

console = Console() if HAS_RICH else None


def print_header():
    if HAS_RICH:
        console.print(Panel.fit(
            "[bold cyan]🏭  AI Software Factory[/bold cyan]\n"
            "[dim]Auto-Evolving Multi-Agent Data Transformation Pipeline[/dim]",
            border_style="bright_blue"
        ))
    else:
        print("=" * 60)
        print("  🏭  AI Software Factory")
        print("=" * 60)


def display_results(output_path: str, expected_path: str = None):
    """Display output summary and optionally compare with expected output."""
    if not os.path.exists(output_path):
        print("  ❌ Output file not found!")
        return

    df = pd.read_excel(output_path)

    if HAS_RICH:
        summary = Table(title="📊 Output Summary", border_style="bright_blue")
        summary.add_column("Metric", style="cyan")
        summary.add_column("Value", style="green")
        summary.add_row("Total Rows", str(len(df)))
        summary.add_row("Columns", ", ".join(df.columns))

        for col in ["L0", "L1", "L2", "L3"]:
            if col in df.columns:
                others = df[col].astype(str).str.contains("Other", case=False, na=False).sum()
                summary.add_row(f"{col} Unique", str(df[col].nunique()))
                summary.add_row(f"{col} 'Other' Count", f"{'🚫 ' + str(others) if others > 0 else '✅ 0'}")

        console.print(summary)

        for col in ["L0", "L1", "L2", "L3"]:
            if col in df.columns:
                dist = Table(title=f"📋 {col} Distribution", border_style="dim")
                dist.add_column("Value", style="cyan")
                dist.add_column("Count", style="green")
                dist.add_column("%", style="yellow")
                for val, cnt in df[col].value_counts().head(10).items():
                    dist.add_row(str(val), str(cnt), f"{cnt/len(df)*100:.1f}%")
                console.print(dist)
    else:
        print(f"\n📊 Output: {len(df)} rows, Columns: {list(df.columns)}")
        for col in ["L0", "L1", "L2", "L3"]:
            if col in df.columns:
                others = df[col].astype(str).str.contains("Other", case=False, na=False).sum()
                print(f"  {col}: {df[col].nunique()} unique, {others} 'Other'")

    # ─── Compare with expected output if provided ─────────────────
    if expected_path and os.path.exists(expected_path):
        print("\n🔍 Comparing with expected output...")
        df_exp = pd.read_excel(expected_path)

        compare_cols = ["L0", "L1", "L2", "L3"]
        for col in compare_cols:
            if col in df.columns and col in df_exp.columns:
                # Compare value distributions
                gen_vals = set(df[col].unique())
                exp_vals = set(df_exp[col].unique())
                common = gen_vals & exp_vals
                missing = exp_vals - gen_vals
                extra = gen_vals - exp_vals

                print(f"\n  {col}:")
                print(f"    Expected unique: {len(exp_vals)}, Generated unique: {len(gen_vals)}")
                print(f"    ✅ Common values: {len(common)}")
                if missing:
                    print(f"    ⚠️  Missing from output: {missing}")
                if extra:
                    print(f"    ℹ️  Extra in output: {extra}")


def main():
    print_header()

    # ─── Configuration ────────────────────────────────────────────
    input_path = "data/test_input_50k.xlsx"
    output_path = "data/pipeline_output_50k.xlsx"
    expected_path = "data/expected_output_50k.xlsx"

    if not os.path.exists(input_path):
        print(f"❌ Input file not found: {input_path}")
        print("   Run: python generate_test_data.py")
        sys.exit(1)

    df_in = pd.read_excel(input_path, nrows=5)  # Read schema only
    print(f"\n📂 Input: {input_path}")
    print(f"   Columns: {list(df_in.columns)}")

    # Full row count
    df_full = pd.read_excel(input_path)
    row_count = len(df_full)
    print(f"   Rows: {row_count}")

    # ─── Supabase Setup ──────────────────────────────────────────
    print("\n📡 Registering in Supabase...")
    project = safe_db_call(create_project, "50K E2E Test", f"{row_count}-row procurement classification test")
    project_id = project.get("id", "") if project else ""

    goal = """Transform raw procurement data into a classified report with Pareto analysis and 
intelligent hierarchical category mappings (L0, L1, L2, L3). 
The classification must be based on Material Type and Material Description.
EVERY row must be classified — the word 'Other' is FORBIDDEN in any L0/L1/L2/L3 field."""

    desired_schema = """
    OUTPUT COLUMNS: Pareto, Material Code, M Desc., Material Group Desc., MTyp, Material Type Desc., 
    M Class, PO Group, Plant Code, Plant Description, Supplier Name, Remark, Direct/Indirect, 
    L0, L1, L2, L3, Spend, For Sorting.

    MAPPING RULES:
    - Pareto = "P1" if INR Line Value > 50000 else "P2"
    - Material Code = from input "Material Code"
    - M Desc. = from input "Material Description" 
    - Material Group Desc. = Derive from Material Description (e.g., ROD, WIRE, BEARING, CAPACITOR)
    - MTyp = from input (map: "Raw materials"->"ZRAW", "Machined Material"->"ZHLB", "Subassembly"->"ZHLB")
    - Material Type Desc. = from input "Material Type"
    - M Class = "ENGG" for all engineering materials
    - PO Group = from input "PO Grp"
    - Plant Code = from input "Plnt Cd"
    - Plant Description = from input "Plant Description"
    - Supplier Name = from input
    - Direct/Indirect = "Direct Spend" if material is used in production, "Indirect Spend" if support
    - Spend = INR Line Value
    - For Sorting = cumulative spend per material code (running total)
    
    CLASSIFICATION L0-L3 (BASED ON MATERIAL DESCRIPTION):
    L0 Categories (NO "Other" ALLOWED):
      - "Direct Raw Material" = Raw materials, machined parts, subassemblies for production
      - "FG/Assemblies" = Finished goods, motors, solar panels, complete assemblies
      - "Indirect Spend" = MRO, safety, office, IT, admin items

    L1 Categories:
      - "Commodities" = base metals (copper, aluminium, steel, cast iron, plastics, rubber, chemicals)
      - "Manufactured Components" = machined parts, castings, stampings
      - "Sub Assemblies" = pump components, plastic moulded parts, control panels
      - "Bought Out Items" = bearings, seals, fasteners, electrical bought-outs
      - "Packaging" = corrugated boxes, pallets, wraps, foam
      - "FG/Assemblies" = solar, motors, drives
      - "MRO" = maintenance, safety, tools
      - "Admin & Facilities" = office supplies, IT equipment

    L2 = More specific (e.g., "Copper", "Steel", "Machined Parts", "Bearings & Seals")
    L3 = Most granular (e.g., "Copper Rod", "SS Sleeve", "Ball Bearing", "Safety Helmet")

    CRITICAL: Infer L2 and L3 from the Material Description text. For example:
      - "ROD COPPER EC GRADE" → L2: "Copper", L3: "Copper Rod"
      - "IMPELLER SS316" → L2: "Machined Parts", L3: "SS Impeller"
      - "BEARING 6205" → L2: "Bearings & Seals", L3: "Ball Bearing"
    """

    run_record = None
    run_id = ""
    if project_id:
        safe_db_call(save_data_snapshot, "", "input", df_full.head(100).to_dict(orient="records"), row_count)
        run_record = safe_db_call(create_run, project_id, "file_upload", goal, desired_schema, row_count)
        run_id = run_record.get("id", "") if run_record else ""
        if run_id:
            safe_db_call(save_data_snapshot, run_id, "input", df_full.head(100).to_dict(orient="records"), row_count)

    print(f"   Project: {project_id or 'N/A'}")
    print(f"   Run: {run_id or 'N/A'}")

    # ─── Fetch learned rules ─────────────────────────────────────
    existing_rules = ""
    if project_id:
        rules = safe_db_call(get_classification_rules, project_id)
        if rules:
            existing_rules = "Previously learned rules:\n"
            for r in rules[:20]:
                existing_rules += f"  {r['material_type']} → L0:{r['l0']} L1:{r['l1']} L2:{r['l2']} L3:{r['l3']}\n"

    # ─── Run Pipeline ────────────────────────────────────────────
    print(f"\n🚀 Running AI pipeline on {row_count} rows...")
    print("   Agents: Analyzer → Coder → Evaluator → Executor → (Evolution Loop)\n")

    # Read real sample data for the analyzer
    sample_rows = df_full.head(10).to_string(index=False)
    
    unique_descs = df_full["Material Description"].unique().tolist() if "Material Description" in df_full.columns else []
    
    initial_state = {
        "project_id": project_id,
        "run_id": run_id,
        "input_path": input_path,
        "output_path": output_path,
        "raw_data_schema": ", ".join(df_full.columns),
        "sample_data": sample_rows,
        "unique_material_descriptions": ", ".join(str(d) for d in unique_descs),
        "desired_output_schema": desired_schema,
        "goal_description": goal,
        "iteration_count": 0,
        "error_history": [],
        "is_code_safe": False,
        "execution_success": False,
        "learned_context": existing_rules
    }

    start_time = time.time()
    final_state = app.invoke(initial_state)
    total_time = time.time() - start_time

    # ─── Results ─────────────────────────────────────────────────
    status = final_state.get('final_status', 'N/A')
    print(f"\n{'='*60}")
    print(f"  Status: {status}")
    print(f"  Time: {total_time:.1f}s")
    print(f"  Iterations: {final_state.get('iteration_count', 0)}")

    if final_state.get('execution_success') and os.path.exists(output_path):
        print(f"  Output: {output_path}")
        display_results(output_path, expected_path)
    else:
        print("  ❌ Pipeline failed.")
        print("  Last Logs:")
        logs = final_state.get('execution_logs', 'No logs')
        print(logs[:3000] if logs else "No logs")

    if HAS_RICH:
        console.print(Panel.fit(
            f"[bold {'green' if status == 'success' else 'red'}]Pipeline {status}[/bold {'green' if status == 'success' else 'red'}]\n"
            f"[dim]Check Supabase for logs: factory_step_logs, factory_code_versions[/dim]",
            border_style="green" if status == "success" else "red"
        ))


if __name__ == "__main__":
    main()
