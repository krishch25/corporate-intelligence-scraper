# AI Software Factory

An auto-evolving multi-agent system built with LangGraph that analyzes raw data, generates Python algorithms to transform it into desired outputs, tests the code in a Docker sandbox, and iterates based on success/failure to formulate permanent, accurate classification rules.

## Core Features
- **LangGraph Orchestration**: State-driven cyclic workflow for self-updating agents.
- **Docker Sandbox execution**: Safe execution of generated code.
- **Accuracy & Evolution via Memory**: Learns from past successes and errors, saving correct patterns to a Vector DB.

## Architecture Structure
- `app/agents/`: Analyzer, Coder, Evaluator, Evolution agents.
- `app/core/`: Configuration, LangGraph node/edge definitions, state models.
- `app/db/`: Database models and connection logic (Supabase).
- `app/execution/`: Docker abstraction for safely running generated code.
- `app/api/`: FastAPI endpoints.
