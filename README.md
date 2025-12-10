# Workflow Engine - AI Engineering Assignment

A minimal workflow/graph engine built with FastAPI and Python. Supports nodes, state management, edges, branching, looping, and REST APIs for workflow execution.

## Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Run the Server
```bash
uvicorn app.main:app --reload --port 8000
```

### Test the System
```bash
# Run the test
python test_upgraded.py

# Get available graphs
curl http://localhost:8000/graphs

# Run summarization workflow (use actual graph_id from above)
curl -X POST "http://localhost:8000/graph/run" \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": "your-graph-id-here",
    "input_data": {
      "text": "Your text to summarize here...",
      "max_length": 200
    }
  }'
```

## Features

### Core Engine
- **Nodes**: Python functions that modify shared state
- **State**: Type-safe Pydantic models with immutable updates
- **Edges**: Node-to-node connections
- **Branching**: Conditional routing
- **Looping**: Iterative execution until conditions met

### API Endpoints
- `POST /graph/run` - Execute workflows
- `GET /graphs` - List available graphs
- `GET /graph/state/{run_id}` - Get workflow state
- `GET /ws/run/{graph_id}` - WebSocket streaming

### Sample Workflow: Summarization
1. Split text into chunks
2. Summarize chunks using frequency scoring
3. Merge summaries
4. Refine with rule-based compression
5. Loop until target length achieved

## Project Structure
```
├── app/main.py              # FastAPI application
├── engine/                  # Core workflow engine
│   ├── graph.py            # Graph execution
│   ├── state.py            # State management
│   └── ...
├── workflows/summarization/ # Sample workflow
│   ├── nodes_upgraded.py   # Workflow nodes
│   └── graph_def.py        # Graph definition
└── requirements.txt        # Dependencies
```

## Example Results
```
Input: 1231 characters
Output: 69 characters (94.4% compression)
Execution: ~2.5ms
Quality: Coherent, meaningful summary
```

Visit `http://localhost:8000/docs` for interactive API documentation.
