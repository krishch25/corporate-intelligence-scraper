from langchain_core.prompts import ChatPromptTemplate
from app.core.state import AgentState
from app.core.llm import get_llm

EVOLUTION_PROMPT = """
You are the Evolution and Refinement Engine.
The previously generated code was executed and FAILED or produced incorrect results.

EXECUTION LOGS / ERRORS:
{execution_logs}

PREVIOUS CODE:
{generated_code}

STRATEGY:
{proposed_algorithm_strategy}

Your job is to analyze the error logs, figure out what went wrong in the code, and output a NEW strategy/instructions for the Coder to fix it.

OUTPUT YOUR INSTRUCTIONS FOR THE CODER:
"""

def evolution_node(state: AgentState):
    print("---EVOLUTION ENGINE (LEARNING FROM FAILURE)---")
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(EVOLUTION_PROMPT)
    chain = prompt | llm
    
    response = chain.invoke({
        "execution_logs": state.get("execution_logs", ""),
        "generated_code": state.get("generated_code", ""),
        "proposed_algorithm_strategy": state.get("proposed_algorithm_strategy", "")
    })
    
    # Store the error to prevent repeating
    errors = state.get("error_history", [])
    errors.append(f"Iteration Execute Error: {state.get('execution_logs', '')}")
    
    return {
        "iteration_count": state.get("iteration_count", 0) + 1,
        "proposed_algorithm_strategy": f"UPDATED INSTRUCTIONS:\n{response.content}",
        "error_history": errors,
        "is_code_safe": False, # Reset safety
        "execution_success": False # Reset success
    }
