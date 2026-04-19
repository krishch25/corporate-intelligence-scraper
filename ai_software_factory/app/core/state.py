from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    """
    State representing the entire cycle of the auto-evolving agent pipeline.
    """
    # 0. Pipeline Tracking
    project_id: str
    run_id: str
    input_path: str
    output_path: str
    
    # 1. Inputs
    raw_data_schema: str
    sample_data: str
    desired_output_schema: str
    goal_description: str
    
    # 2. Planning Phase
    analysis_report: str
    identified_patterns: List[str]
    proposed_algorithm_strategy: str
    
    # 3. Generation Phase
    generated_code: str
    
    # 4. Evaluation Phase
    code_review_notes: str
    is_code_safe: bool
    
    # 5. Execution Phase (Sandbox)
    execution_success: bool
    execution_logs: str
    execution_result: Optional[str]
    
    # 6. Evolution Phase
    iteration_count: int
    error_history: List[str]
    learned_context: str
    
    # 7. Final Output
    final_status: str  # "success", "failed", "max_iterations_reached"
