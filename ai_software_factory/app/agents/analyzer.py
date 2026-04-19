import json
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from app.core.state import AgentState
from app.core.llm import get_llm

ANALYZER_PROMPT = """
You are the Lead Data Architect specializing in procurement spend classification.
Your job is to analyze the input data and create an EXHAUSTIVE classification mapping.

INPUT DATA SCHEMA:
{raw_data_schema}

ACTUAL SAMPLE DATA (first 10 rows):
{sample_data}

ALL UNIQUE MATERIAL DESCRIPTIONS FOUND IN DATA:
{unique_material_descriptions}

DESIRED OUTPUT SCHEMA / GOAL:
{desired_output_schema}
{goal_description}

EXISTING CLASSIFICATION RULES (from previous successful runs, use these as a starting point):
{existing_rules}

## CRITICAL RULES:
1. You MUST classify EVERY material type into specific L0, L1, L2, L3 categories.
2. The word "Other" is ABSOLUTELY FORBIDDEN in any classification level.
3. Every material type must get a meaningful, industry-standard procurement category.
4. L3 must be the most granular — combine the material type with specific detail.

## PROCUREMENT TAXONOMY REFERENCE:
L0 (Spend Type):
  - "Direct Spend" = materials that go INTO the final product (raw materials, components, sub-assemblies, packaging)
  - "Indirect Spend" = materials that SUPPORT operations but don't go into the product (IT, office, services, consumables)

L1 (Category):
  - For Direct: "Manufacturing Components", "Raw Materials & Chemicals", "Packaging Materials"
  - For Indirect: "IT & Technology", "Office & Administration", "Professional Services", "Facilities & Maintenance"

L2 (Sub-category):
  - e.g., "Metals & Alloys", "Electronic Components", "Corrugated Packaging", "Computer Hardware", "Office Consumables", "Consulting Services"

L3 (Specific Classification):
  - e.g., "Precision Machined Metal Parts", "Semiconductor Components", "Cardboard Boxes & Cartons", "Laptops & Desktops", "Pens & Stationery", "IT Consulting"

Please output a JSON response with these keys:
1. "analysis_report": A brief report of what the data contains and the transformation needed.
2. "identified_patterns": A list of strings for each pattern/rule identified.
3. "proposed_algorithm_strategy": Step-by-step pseudo-code for the transformation.
4. "classification_rules": A list of objects, one per unique Material Description:
   [{{"material_description": "...", "l0": "...", "l1": "...", "l2": "...", "l3": "..."}}]

Only return valid JSON. No markdown ticks.
"""

def analyzer_node(state: AgentState):
    print("---ANALYZING---")
    llm = get_llm()
    prompt = ChatPromptTemplate.from_template(ANALYZER_PROMPT)
    chain = prompt | llm
    
    # Read actual sample data from the input file
    sample_data_str = state.get("sample_data", "")
    unique_types_str = ""
    input_path = state.get("input_path", "")
    
    if input_path:
        try:
            df = pd.read_excel(input_path)
            sample_data_str = df.head(10).to_string(index=False)
        except Exception as e:
            print(f"  Warning: Could not read input file: {e}")
    
    response = chain.invoke({
        "sample_data": sample_data_str,
        "raw_data_schema": state.get("raw_data_schema", ""),
        "desired_output_schema": state.get("desired_output_schema", ""),
        "goal_description": state.get("goal_description", ""),
        "unique_material_descriptions": state.get("unique_material_descriptions", ""),
        "existing_rules": state.get("learned_context", "No existing rules yet.")
    })
    
    try:
        text = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        
        classification_rules = data.get("classification_rules", [])
        # Format rules as a string table for the Coder
        rules_str = "CLASSIFICATION RULES TABLE:\n"
        for r in classification_rules:
            rules_str += f"  Material Desc: {r.get('material_description', '')} -> L0: {r.get('l0', '')} | L1: {r.get('l1', '')} | L2: {r.get('l2', '')} | L3: {r.get('l3', '')}\n"
        
        strategy = data.get("proposed_algorithm_strategy", "")
        if isinstance(strategy, list):
            strategy = "\n".join(strategy)
        
        return {
            "analysis_report": data.get("analysis_report", ""),
            "identified_patterns": data.get("identified_patterns", []),
            "proposed_algorithm_strategy": strategy,
            "learned_context": rules_str  # Pass rules to the Coder via learned_context
        }
    except Exception as e:
        return {
            "analysis_report": f"Failed to parse analysis: {e}",
            "identified_patterns": [],
            "proposed_algorithm_strategy": "Fallback: Write a python script using pandas to match the goal."
        }
