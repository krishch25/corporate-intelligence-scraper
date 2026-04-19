from langchain_core.prompts import ChatPromptTemplate
from app.core.state import AgentState
from app.core.llm import get_llm

CODER_PROMPT = """
You are an Expert Python Data Engineer specializing in procurement data classification.
Write a Python script that transforms raw Excel procurement data into a fully classified output.

STRATEGY TO IMPLEMENT:
{proposed_algorithm_strategy}

IDENTIFIED PATTERNS:
{identified_patterns}

{learned_context}

ERROR HISTORY (If any, fix these!):
{error_history}

## ABSOLUTE REQUIREMENTS:
1. The script MUST contain a function: `def transform(input_path: str, output_path: str) -> None:`
2. Use `pandas` to read/write Excel files.
3. Do NOT wrap the code in markdown (no ```python). Just raw python.
4. Include all imports at the top.

## OUTPUT COLUMNS (MUST have ALL of these):
- Pareto: "P1" if INR Line Value > 50000 else "P2"
- Material Code: use "UNKNOWN" if not available in input
- Supplier Name: from input  
- Spend: = INR Line Value
- L0: Direct Spend or Indirect Spend (NEVER "Other")
- L1: Broad category (NEVER "Other")
- L2: Sub-category (NEVER "Other")
- L3: Most specific classification (NEVER "Other")

## CRITICAL VALIDATION:
After generating the output DataFrame, add this validation block before saving:
```
# Validate — NO "Other" values allowed
for col in ['L0', 'L1', 'L2', 'L3']:
    other_count = df_out[col].str.contains('Other', case=False, na=False).sum()
    if other_count > 0:
        raise ValueError(f"FORBIDDEN: {{other_count}} rows have 'Other' in {{col}}. Fix the classification logic!")
    empty_count = df_out[col].isna().sum() + (df_out[col] == '').sum()
    if empty_count > 0:
        raise ValueError(f"FORBIDDEN: {{empty_count}} rows have empty values in {{col}}. Every row must be classified!")
```

Use the CLASSIFICATION RULES TABLE in the LEARNED CONTEXT above as inspiration.
CRITICAL: You MUST create a Python dictionary in your code that maps EVERY SINGLE unique `Material Description` from the input file to its specific L0, L1, L2, and L3. 
For example:
```python
mapping = {{
    "ROD COPPER EC GRADE 8mm ROUND": {{"L0": "Direct Raw Material", "L1": "Commodities", "L2": "Copper", "L3": "Copper Rod"}},
    "SLEE SS304 S4S-1-14m³": {{"L0": "Direct Raw Material", "L1": "Manufactured Components", "L2": "Machined Parts", "L3": "SS Sleeve"}}
    # ... Create an entry for EVERY unique Material Description found in the dataset!
}}
```
If a Material Description is missing from your hardcoded dictionary, write logic to infer the closest match dynamically based on the string name — NEVER use "Other".

Write the python code now:
"""

def coder_node(state: AgentState):
    print(f"---CODING (Iteration {state.get('iteration_count', 0)})---")
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(CODER_PROMPT)
    chain = prompt | llm
    
    response = chain.invoke({
        "proposed_algorithm_strategy": state.get("proposed_algorithm_strategy", ""),
        "identified_patterns": "\n".join(state.get("identified_patterns", [])),
        "error_history": "\n---\n".join(state.get("error_history", [])),
        "learned_context": state.get("learned_context", "")
    })
    
    code = response.content.replace("```python", "").replace("```", "").strip()
    return {"generated_code": code}
