from langchain_core.prompts import ChatPromptTemplate
from app.core.state import AgentState
from app.core.llm import get_llm
import json

EVALUATOR_PROMPT = """
You are a Senior Security & Quality Assurance Reviewer. 
Review the following Python code before it gets executed in our Sandbox.

CODE TO REVIEW:
{generated_code}

YOUR TASKS:
1. Ensure the code does not contain malicious OS commands (os.system, subprocess, shutil.rmtree outside of generic temp folders).
2. Ensure there are no obvious syntax errors.
3. Ensure it contains the required signature: `def transform(input_path: str, output_path: str) -> None:`
4. Ensure the code creates ALL required output columns: Pareto, Material Code, Supplier Name, Spend, L0, L1, L2, L3.
5. Ensure NO classification column is hardcoded to "Other" — every value must be meaningful.
6. Ensure the code has validation that rejects "Other" values before saving.

Output a JSON response:
{{
  "is_code_safe": true/false,
  "code_review_notes": "Your notes here. If false, explain why so the Coder can fix it."
}}
"""

def evaluator_node(state: AgentState):
    print("---STATIC EVALUATION---")
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(EVALUATOR_PROMPT)
    chain = prompt | llm
    
    response = chain.invoke({
        "generated_code": state.get("generated_code", "")
    })
    
    try:
        text = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        
        is_safe = data.get("is_code_safe", False)
        notes = data.get("code_review_notes", "Evaluation failed parsing.")
        
        errors = state.get("error_history", [])
        if not is_safe:
            errors.append(f"Evaluator rejected code: {notes}")
            
        return {
            "is_code_safe": is_safe,
            "code_review_notes": notes,
            "error_history": errors
        }
    except Exception as e:
        return {
             "is_code_safe": False,
             "code_review_notes": f"Parser error in static evaluation: {e}",
             "error_history": state.get("error_history", []) + [f"Evaluator Parse Error: {e}"]
        }
