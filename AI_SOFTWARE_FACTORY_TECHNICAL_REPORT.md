# AI Software Factory - Technical Report

## Executive Summary

This report provides a comprehensive analysis of the **AI Software Factory**, an intelligent automation system that automatically transforms raw procurement data into categorized, classified outputs using artificial intelligence. Think of it as a highly skilled team of AI workers that analyze data problems, write solutions, test them, and learn from mistakes - all automatically.

---

## Table of Contents

1. [What Does This System Do?](#1-what-does-this-system-do)
2. [How the System Works - Simple Explanation](#2-how-the-system-works---simple-explanation)
3. [The Team of AI Agents](#3-the-team-of-ai-agents)
4. [Step-by-Step Workflow](#4-step-by-step-workflow)
5. [Real-World Example](#5-real-world-example)
6. [Technical Architecture](#6-technical-architecture)
7. [Data Flow](#7-data-flow)
8. [Security & Safety](#8-security--safety)
9. [Learning & Memory](#9-learning--memory)
10. [Database Structure](#10-database-structure)
11. [Glossary](#11-glossary)

---

## 1. What Does This System Do?

### The Problem It Solves

Imagine you have a massive spreadsheet with 50,000 rows of procurement data (things a company buys - raw materials, components, services). The data contains:
- Material descriptions (e.g., "ROD COPPER EC GRADE 8mm ROUND")
- Supplier names
- Prices
- Quantities

**The Challenge:** You need to categorize every single item into a hierarchical classification system:
0**: Is- **L it Direct Spend (goes into products) or Indirect Spend (supports operations)?
- **L1**: What broad category does it belong to? (e.g., "Commodities", "Manufactured Components")
- **L2**: What sub-category? (e.g., "Copper", "Steel", "Machined Parts")
- **L3**: What specific item? (e.g., "Copper Rod", "SS Sleeve", "Ball Bearing")

**The Challenge:** No "Other" is allowed - every item must have a meaningful classification!

### The Solution

The AI Software Factory takes raw Excel data and automatically:
1. Analyzes the data structure
2. Creates intelligent classification rules
3. Writes Python code to transform the data
4. Tests the code in a safe environment
5. If it fails, learns from the error and tries again (up to 5 times)
6. Saves successful classification rules for future use

---

## 2. How the System Works - Simple Explanation

### The Factory Analogy

Think of this system as an **automated factory** with multiple specialized workers on an assembly line:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   ANALYZER  │───▶│   CODER     │───▶│  EVALUATOR  │───▶│  EXECUTOR   │
│ (Architect) │    │(Programmer) │    │(QA Reviewer)│    │ (Test Lab)  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                   │
                           If Failed:                              │
                           ┌───────────────┐                       │
                           │   EVOLUTION   │◀──────────────────────┘
                           │  (Debug Team) │
                           └───────────────┘
```

**Each worker has a specific job:**
1. **Analyzer**: Studies the data and creates a plan
2. **Coder**: Writes the actual code to do the transformation
3. **Evaluator**: Checks if the code is safe and correct
4. **Executor**: Runs the code in a safe sandbox
5. **Evolution**: If something fails, analyzes the error and suggests fixes

---

## 3. The Team of AI Agents

### 3.1 Analyzer Agent - The Lead Data Architect

**Role:** Studies the input data and creates a transformation strategy

**What it does:**
- Receives the raw data schema (column names, data types)
- Analyzes sample rows to understand the data
- Looks at all unique material descriptions
- Creates classification rules for each unique material type

**Input Example:**
```
Input: Material Description = "ROD COPPER EC GRADE 8mm ROUND"
Output Classification:
- L0: Direct Raw Material
- L1: Commodities
- L2: Copper
- L3: Copper Rod
```

**Output:** A detailed analysis report and step-by-step strategy for transformation

---

### 3.2 Coder Agent - The Python Data Engineer

**Role:** Converts the strategy into actual executable Python code

**What it does:**
- Takes the analyzer's strategy
- Writes a complete Python script with:
  - Data loading from Excel
  - Classification logic
  - Output formatting
  - Validation checks (no "Other" allowed!)

**Key Requirement:** The code MUST contain a function called `transform(input_path, output_path)`

**Example Code Fragment:**
```python
def transform(input_path: str, output_path: str) -> None:
    # Read input Excel file
    df = pd.read_excel(input_path)
    
    # Classification mapping
    mapping = {
        "ROD COPPER EC GRADE": {
            "L0": "Direct Raw Material",
            "L1": "Commodities",
            "L2": "Copper",
            "L3": "Copper Rod"
        }
    }
    
    # Apply classification to each row
    # ... transformation logic ...
    
    # Validate - NO "Other" values allowed
    for col in ['L0', 'L1', 'L2', 'L3']:
        if df[col].str.contains('Other').any():
            raise ValueError("FORBIDDEN: 'Other' found!")
    
    # Save output
    df.to_excel(output_path)
```

---

### 3.3 Evaluator Agent - The Security & QA Reviewer

**Role:** Reviews the generated code for safety and correctness before execution

**What it checks:**
1. **Security:** No malicious commands (no file deletion, no system commands)
2. **Syntax:** Code must be valid Python
3. **Requirements:** Must have the required `transform()` function
4. **Output Columns:** Must create all required columns (Pareto, Material Code, L0-L3, etc.)
5. **No "Other":** Classification cannot use "Other" as a fallback

**Decision:** Returns `is_code_safe: true` or `is_code_safe: false` with notes

---

### 3.4 Executor Agent - The Sandbox Test Lab

**Role:** Runs the generated code in a safe, isolated environment

**What it does:**
- Takes the code and executes it
- Uses a strict timeout (120 seconds) to prevent infinite loops
- Captures all output and errors
- Returns success/failure status with logs

**Safety Features:**
- Code runs in a subprocess (isolated from the main system)
- Strict timeout prevents runaway code
- Only reads input file and writes output file

---

### 3.5 Evolution Agent - The Debug & Learning Engine

**Role:** When code fails, analyzes the error and creates fixes

**What it does:**
1. Reads the execution error logs
2. Analyzes the failing code
3. Creates new instructions for the Coder to fix the issue
4. Stores the error in history to avoid repeating mistakes

**Example Error Scenario:**
```
Error: "KeyError: 'Material Description' not found in columns"
Evolution Output:
"Fix: The input file uses 'M Desc.' instead of 'Material Description'. 
Update the code to use df['M Desc.'] instead."
```

---

## 4. Step-by-Step Workflow

### The Complete Pipeline

```
Step 1: START
User provides:
- Input Excel file (e.g., 50,000 rows of procurement data)
- Goal description (what transformation is needed)
- Desired output schema (what columns should be in result)

        ↓

Step 2: ANALYZER
- Reads sample data
- Identifies all unique material descriptions
- Creates classification rules
- Output: Strategy document + rules table

        ↓

Step 3: CODER (Iteration 1)
- Takes strategy + existing rules
- Writes Python transformation code
- Output: Generated Python code

        ↓

Step 4: EVALUATOR
- Reviews code for safety
- If unsafe →回到 Step 3 (Coder)
- If safe → Continue to Step 5

        ↓

Step 5: EXECUTOR
- Runs code in sandbox
- If success → Step 7 (Finalize)
- If failure → Step 6 (Evolution)

        ↓

Step 6: EVOLUTION (If failed)
- Analyzes error logs
- Creates fix instructions
- Increment iteration count
- If iterations < 5 → Back to Step 3 (Coder)
- If iterations >= 5 → Stop (max retries reached)

        ↓

Step 7: FINALE
- Save output file
- Save classification rules to database
- Log final status (success/failed/max_iterations)
```

### The Feedback Loop

This is the most powerful feature - the system can retry up to 5 times:

```
┌─────────────────────────────────────────────────────────────┐
│                    ITERATION LOOP                           │
│                                                             │
│  Code Runs ──▶ Fails? ──▶ Yes ──▶ Evolution Analyzes Error  │
│      │                           │                          │
│      │                           │                          │
│      No                          Yes                        │
│      │                           │                          │
│      ▼                           ▼                          │
│  SUCCESS              Coder Gets New Instructions            │
│                       (with error analysis)                  │
│                              │                              │
│                              ▼                              │
│                      Try Again (Max 5 times)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Real-World Example

### Scenario: Classifying Procurement Data

#### Input Data (Excel Spreadsheet)

| Material Code | Material Description | Supplier Name | INR Line Value |
|--------------|---------------------|---------------|----------------|
| MC001 | ROD COPPER EC GRADE 8mm ROUND | Copper Corp | 75,000 |
| MC002 | SLEE SS304 S4S-1-14m³ | Steel Ltd | 45,000 |
| MC003 | BEARING 6205 ZZ NSK | Bearing Co | 12,000 |
| MC004 | OFFICECHAIR ERGONOMIC | Furniture Inc | 8,000 |
| MC005 | LAPTOP DELL XPS 15 | Tech Supplies | 65,000 |

#### Expected Output

| Material Desc | Supplier | Spend | L0 | L1 | L2 | L3 | Pareto |
|--------------|----------|-------|-----|-----|-----|-----|--------|
| ROD COPPER... | Copper Corp | 75,000 | Direct Raw Material | Commodities | Copper | Copper Rod | P1 |
| SLEE SS304... | Steel Ltd | 45,000 | Direct Raw Material | Manufactured Components | Machined Parts | SS Sleeve | P2 |
| BEARING 6205... | Bearing Co | 12,000 | Direct Raw Material | Bought Out Items | Bearings & Seals | Ball Bearing | P2 |
| OFFICECHAIR... | Furniture Inc | 8,000 | Indirect Spend | Admin & Facilities | Office Furniture | Ergonomic Chair | P2 |
| LAPTOP DELL... | Tech Supplies | 65,000 | Indirect Spend | IT & Technology | Computer Hardware | Laptops & Desktops | P1 |

### How the System Processes This

1. **Analyzer** reads the data, sees 5 unique material descriptions
2. **Analyzer** creates classification rules for each
3. **Coder** writes code that maps each description to L0-L3
4. **Evaluator** checks the code is safe
5. **Executor** runs the code on the 50,000-row file
6. **Success!** - All rows classified, no "Other" used

---

## 6. Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI SOFTWARE FACTORY                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ORCHESTRATOR (LangGraph)                   │   │
│  │    Manages the workflow, state, and routing             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐  │
│  │  ANALYZER  │ │   CODER    │ │  EVALUATOR │ │ EXECUTOR │  │
│  │   Agent    │ │   Agent    │ │   Agent    │ │  Agent   │  │
│  └────────────┘ └────────────┘ └────────────┘ └──────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  SANDBOX EXECUTION                       │   │
│  │     Isolated Python process with timeout (120s)        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              SUPABASE DATABASE                           │   │
│  │  - Projects & Runs tracking                             │   │
│  │  - Step logs (audit trail)                              │   │
│  │  - Code versions (history)                               │   │
│  │  - Classification rules (memory)                        │   │
│  │  - Data snapshots                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Orchestration | LangGraph | Manage multi-agent workflow |
| AI Models | OpenAI / Azure OpenAI | Power the AI agents |
| Database | Supabase (PostgreSQL) | Store runs, logs, rules |
| Code Execution | Python subprocess | Safe code execution |
| Data Processing | Pandas | Excel reading/writing |
| API Framework | FastAPI | (Future) REST endpoints |

### File Structure

```
ai_software_factory/
├── run_factory.py              # Main entry point
├── app/
│   ├── agents/
│   │   ├── analyzer.py        # Analyzer agent
│   │   ├── coder.py           # Coder agent
│   │   ├── evaluator.py       # Evaluator agent
│   │   └── evolution.py      # Evolution agent
│   ├── core/
│   │   ├── state.py           # Data state definition
│   │   ├── orchestrator.py   # Workflow orchestration
│   │   ├── llm.py             # AI model client
│   │   └── config.py          # Configuration
│   ├── execution/
│   │   └── sandbox.py         # Safe code execution
│   ├── db/
│   │   └── supabase_client.py # Database operations
│   └── api/
│       └── (future endpoints)
├── data/
│   ├── input_sample.xlsx       # Sample input
│   └── output_result.xlsx      # Generated output
└── requirements.txt            # Python dependencies
```

---

## 7. Data Flow

### State Throughout the Pipeline

As data moves through the system, it accumulates more information:

```
┌──────────────────────────────────────────────────────────────────┐
│                     AGENT STATE (Flow)                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INITIAL STATE:                                                 │
│  ├── input_path: "data/test_input_50k.xlsx"                   │
│  ├── output_path: "data/pipeline_output_50k.xlsx"             │
│  ├── raw_data_schema: "Material Code, Material Description..." │
│  ├── goal_description: "Transform raw data into classified..."│
│  └── iteration_count: 0                                        │
│                                                                  │
│  AFTER ANALYZER:                                                │
│  ├── analysis_report: "Data contains 50,000 rows..."          │
│  ├── identified_patterns: ["Copper items", "Steel items"...]  │
│  ├── proposed_algorithm_strategy: "Step 1: Read Excel..."     │
│  └── learned_context: "Rules table with 500+ entries"         │
│                                                                  │
│  AFTER CODER:                                                   │
│  ├── generated_code: "def transform(input_path, output_path)"│
│                                                                  │
│  AFTER EVALUATOR:                                               │
│  ├── is_code_safe: true                                        │
│  └── code_review_notes: "Code looks good"                      │
│                                                                  │
│  AFTER EXECUTOR:                                                │
│  ├── execution_success: true                                   │
│  ├── execution_logs: "Processed 50000 rows in 45s"           │
│  └── execution_result: "data/pipeline_output_50k.xlsx"        │
│                                                                  │
│  (If failed, add: error_history, iteration_count increments)  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 8. Security & Safety

### Why Safety Matters

This system generates and executes code automatically. Without safety measures, it could:
- Delete files on your computer
- Run malicious commands
- Execute infinite loops

### Safety Measures Implemented

| Measure | Description |
|---------|-------------|
| **Code Review** | Evaluator agent checks for dangerous commands |
| **Process Isolation** | Code runs in a subprocess, not directly |
| **Timeout** | 120-second limit prevents infinite loops |
| **No "Other" Validation** | Ensures meaningful classifications |
| **Input/Output Only** | Can only read input and write output files |

### Security Checks in Evaluator

The Evaluator rejects code containing:
```python
# BLOCKED:
os.system("rm -rf /")     # System commands
subprocess.run(["rm", ...])  # File deletion
shutil.rmtree(...)        # Directory removal
eval("...")              # Dynamic code execution
exec("...")              # Dynamic code execution
```

---

## 9. Learning & Memory

### The Memory System

The system learns from successful runs and stores classification rules:

```
┌─────────────────────────────────────────────────────────────┐
│              CLASSIFICATION RULES MEMORY                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Material Type → L0, L1, L2, L3                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ ROD COPPER EC GRADE                                 │  │
│  │   → Direct Raw Material | Commodities | Copper     │  │
│  │   → Copper Rod                                       │  │
│  ├─────────────────────────────────────────────────────┤  │
│  │ BEARING 6205 ZZ                                     │  │
│  │   → Direct Raw Material | Bought Out Items         │  │
│  │   → Bearings & Seals | Ball Bearing                 │  │
│  ├─────────────────────────────────────────────────────┤  │
│  │ LAPTOP DELL XPS                                     │  │
│  │   → Indirect Spend | IT & Technology                │  │
│  │   → Computer Hardware | Laptops & Desktops         │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  These rules are saved to the database and used in        │
│  future runs to speed up classification!                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Benefits of Learning

1. **Faster Processing**: Future runs can use pre-learned rules
2. **Consistency**: Same materials get same classifications
3. **Knowledge Reuse**: Rules can be shared across projects

---

## 10. Database Structure

### Tables in Supabase

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE SCHEMA                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  factory_projects                                              │
│  ├── id (UUID)                                                 │
│  ├── name                                                      │
│  ├── description                                               │
│  └── created_at                                                 │
│                                                                 │
│  factory_runs                                                  │
│  ├── id (UUID)                                                 │
│  ├── project_id → factory_projects                             │
│  ├── status (running/success/failed/max_iterations)           │
│  ├── input_row_count                                           │
│  ├── output_row_count                                          │
│  ├── total_iterations                                          │
│  └── started_at / completed_at                                 │
│                                                                 │
│  factory_step_logs                                            │
│  ├── id (UUID)                                                 │
│  ├── run_id → factory_runs                                     │
│  ├── step_name (analyzer/coder/evaluator/executor/evolution)  │
│  ├── iteration                                                 │
│  ├── input_summary                                             │
│  ├── output_summary                                            │
│  ├── duration_ms                                               │
│  └── status                                                    │
│                                                                 │
│  factory_code_versions                                        │
│  ├── id (UUID)                                                 │
│  ├── run_id → factory_runs                                     │
│  ├── iteration                                                 │
│  ├── generated_code                                            │
│  ├── is_safe                                                   │
│  ├── execution_success                                         │
│  └── review_notes                                              │
│                                                                 │
│  factory_classification_rules                                  │
│  ├── id (UUID)                                                 │
│  ├── project_id → factory_projects                             │
│  ├── material_type                                             │
│  ├── l0, l1, l2, l3                                            │
│  ├── confidence                                                │
│  └── source (llm/manual)                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. Glossary

| Term | Definition |
|------|------------|
| **Agent** | An AI component that performs a specific task (analyze, code, evaluate, etc.) |
| **LangGraph** | A framework for building multi-agent workflows with state management |
| **Sandbox** | An isolated environment where code runs safely without affecting the main system |
| **Iteration** | One attempt at generating and running code (max 5 allowed) |
| **L0/L1/L2/L3** | Hierarchical classification levels (most broad to most specific) |
| **Direct Spend** | Materials that go into the final product |
| **Indirect Spend** | Materials that support operations but don't go into products |
| **Schema** | The structure of data (column names, types, format) |
| **Supabase** | A cloud database service (PostgreSQL-based) |
| **Pandas** | A Python library for data manipulation |

---

## Summary

The **AI Software Factory** is a sophisticated but elegant system that automates the entire process of data transformation:

1. **Analyzes** your raw data
2. **Creates** intelligent classification rules
3. **Generates** executable code automatically
4. **Tests** the code safely
5. **Learns** from any mistakes
6. **Produces** correctly classified output

Think of it as having a team of expert data engineers working 24/7, learning from each job they complete, and getting better over time. The system is designed to be safe, auditable, and self-improving.

---

*Report Generated: March 2026*
*Project: AI Software Factory - Procurement Data Classification*
