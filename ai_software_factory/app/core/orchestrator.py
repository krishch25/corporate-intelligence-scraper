import os
import time
import pandas as pd
from langgraph.graph import StateGraph, END
from app.core.state import AgentState
from app.agents.analyzer import analyzer_node
from app.agents.coder import coder_node
from app.agents.evaluator import evaluator_node
from app.agents.evolution import evolution_node
from app.execution.sandbox import run_transform
from app.db.supabase_client import (
    log_step_start, log_step_complete, save_code_version,
    update_code_version, save_classification_rules,
    save_data_snapshot, update_run_status, safe_db_call
)


# ─── Wrapped Agent Nodes (with DB logging) ────────────────────────────────────

def _wrap_node(node_func, step_name):
    """Wraps an agent node function to add Supabase step logging."""
    def wrapped(state: AgentState):
        run_id = state.get("run_id", "")
        iteration = state.get("iteration_count", 0)
        
        # Log step start
        step_log = None
        if run_id:
            step_log = safe_db_call(
                log_step_start, run_id, step_name, iteration,
                input_summary=f"Iteration {iteration}"
            )
        
        start_time = time.time()
        result = node_func(state)
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log step completion
        if step_log and step_log.get("id"):
            output_summary = ""
            if step_name == "analyzer":
                output_summary = result.get("analysis_report", "")[:500]
            elif step_name == "coder":
                output_summary = f"Generated {len(result.get('generated_code', ''))} chars of code"
            elif step_name == "evaluator":
                output_summary = f"Safe: {result.get('is_code_safe')} | {result.get('code_review_notes', '')[:200]}"
            elif step_name == "evolution":
                output_summary = f"Updated strategy for iteration {iteration + 1}"
            
            safe_db_call(log_step_complete, step_log["id"], output_summary, duration_ms)
        
        # Save code version after coder
        if step_name == "coder" and run_id:
            safe_db_call(save_code_version, run_id, iteration, result.get("generated_code", ""))
        
        return result
    
    return wrapped


# ─── Execution Node ───────────────────────────────────────────────────────────

def execution_node(state: AgentState):
    print(f"---EXECUTING IN SANDBOX (Iteration {state.get('iteration_count', 0)})---")
    
    input_path = state.get("input_path", "data/input_sample.xlsx")
    output_path = state.get("output_path", "data/output_result.xlsx")
    run_id = state.get("run_id", "")
    iteration = state.get("iteration_count", 0)
    
    os.makedirs(os.path.dirname(input_path) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    # Log step start
    step_log = None
    if run_id:
        step_log = safe_db_call(log_step_start, run_id, "executor", iteration)
    
    start_time = time.time()
    result = run_transform(
        generated_code=state["generated_code"],
        input_path=input_path,
        output_path=output_path
    )
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Log step completion
    if step_log and step_log.get("id"):
        safe_db_call(
            log_step_complete, step_log["id"],
            f"Success: {result['success']} | {result['logs'][:300]}",
            duration_ms,
            "completed" if result["success"] else "failed"
        )
    
    return {
        "execution_success": result["success"],
        "execution_logs": result["logs"],
        "execution_result": result["output_path"]
    }


# ─── Conditional Edges ────────────────────────────────────────────────────────

def route_evaluation(state: AgentState):
    if state["is_code_safe"]:
        return "execute"
    return "coder"

def route_execution(state: AgentState):
    if state["execution_success"]:
        return "finale"
    if state.get("iteration_count", 0) >= 5:
        return "finale"
    return "evolve"


# ─── Finale Node ──────────────────────────────────────────────────────────────

def finale_node(state: AgentState):
    print("---PIPELINE FINISHED---")
    run_id = state.get("run_id", "")
    project_id = state.get("project_id", "")
    output_path = state.get("output_path", "")
    
    if state.get("execution_success"):
        status = "success"
        
        # Save output data snapshot
        if run_id and output_path and os.path.exists(output_path):
            try:
                df_out = pd.read_excel(output_path)
                rows = df_out.to_dict(orient="records")
                safe_db_call(save_data_snapshot, run_id, "output", rows, len(rows))
                
                # Extract and save classification rules
                if project_id and "L0" in df_out.columns:
                    rules = []
                    if "Material Type" in df_out.columns:
                        # Group by material type to extract rules
                        for mt in df_out["Material Type"].unique():
                            row = df_out[df_out["Material Type"] == mt].iloc[0]
                            rules.append({
                                "material_type": mt,
                                "l0": str(row.get("L0", "")),
                                "l1": str(row.get("L1", "")),
                                "l2": str(row.get("L2", "")),
                                "l3": str(row.get("L3", ""))
                            })
                    if rules:
                        safe_db_call(save_classification_rules, project_id, rules)
                
                # Update run
                safe_db_call(
                    update_run_status, run_id, "success",
                    output_row_count=len(df_out),
                    total_iterations=state.get("iteration_count", 0)
                )
            except Exception as e:
                print(f"  Warning: Could not save output snapshot: {e}")
                safe_db_call(update_run_status, run_id, "success")
        
        return {"final_status": "success"}
    
    elif state.get("iteration_count", 0) >= 5:
        if run_id:
            safe_db_call(
                update_run_status, run_id, "max_iterations",
                total_iterations=state.get("iteration_count", 0)
            )
        return {"final_status": "max_iterations_reached"}
    else:
        if run_id:
            safe_db_call(update_run_status, run_id, "failed")
        return {"final_status": "failed"}


# ─── Build the Graph ──────────────────────────────────────────────────────────

def build_factory_graph():
    workflow = StateGraph(AgentState)
    
    # Define Nodes (wrapped with DB logging)
    workflow.add_node("analyzer", _wrap_node(analyzer_node, "analyzer"))
    workflow.add_node("coder", _wrap_node(coder_node, "coder"))
    workflow.add_node("evaluator", _wrap_node(evaluator_node, "evaluator"))
    workflow.add_node("executor", execution_node)
    workflow.add_node("evolution", _wrap_node(evolution_node, "evolution"))
    workflow.add_node("finale", finale_node)
    
    # Define Edges
    workflow.set_entry_point("analyzer")
    workflow.add_edge("analyzer", "coder")
    workflow.add_edge("coder", "evaluator")
    
    workflow.add_conditional_edges(
        "evaluator", route_evaluation,
        {"execute": "executor", "coder": "coder"}
    )
    
    workflow.add_conditional_edges(
        "executor", route_execution,
        {"finale": "finale", "evolve": "evolution"}
    )
    
    workflow.add_edge("finale", END)
    workflow.add_edge("evolution", "coder")
    
    return workflow.compile()


# The global app singleton
app = build_factory_graph()
