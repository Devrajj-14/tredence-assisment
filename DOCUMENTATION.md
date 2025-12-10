# AI Workflow Engine - Complete Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [API Endpoints](#api-endpoints)
4. [Core Components](#core-components)
5. [Workflow Implementation](#workflow-implementation)
6. [Usage Examples](#usage-examples)
7. [Development Guide](#development-guide)

## Project Overview

The AI Workflow Engine is a production-ready system for executing complex workflows through a graph-based approach. It supports state management, conditional branching, looping, and real-time monitoring.

### Key Features
- **Graph-based execution** - Define workflows as nodes and edges
- **State management** - Type-safe state passing between nodes
- **Conditional logic** - Branch execution based on state values
- **Loop support** - Iterative processing until conditions are met
- **Real-time monitoring** - WebSocket streaming of execution events
- **Async execution** - Background processing with job tracking
- **REST API** - Complete HTTP interface for workflow management

## Architecture

### System Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │  Workflow Graph │    │   Node Registry │
│                 │    │                 │    │                 │
│ • REST Endpoints│────│ • Graph Executor│────│ • Function Store│
│ • WebSocket     │    │ • State Manager │    │ • Node Lookup   │
│ • Background    │    │ • Loop Handler  │    │ • Validation    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Job Tracker   │    │  WebSocket Mgr  │    │   Workflows     │
│                 │    │                 │    │                 │
│ • Run Status    │    │ • Live Streaming│    │ • Summarization │
│ • Progress      │    │ • Event Broadcast│   │ • Node Functions│
│ • Persistence   │    │ • Client Mgmt   │    │ • Graph Def     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow
1. **Request** → FastAPI receives workflow execution request
2. **Validation** → Graph and input data validation
3. **Execution** → WorkflowGraph executes nodes sequentially
4. **State Management** → State flows between nodes immutably
5. **Monitoring** → Real-time events streamed via WebSocket
6. **Response** → Final state and execution log returned

## API Endpoints

### Core Workflow Endpoints

#### `GET /`
**Health Check**
- **Purpose**: Verify service status
- **Response**: Service information and statistics
```json
{
  "status": "running",
  "service": "AI Workflow Engine",
  "version": "1.0.0",
  "registered_graphs": 1,
  "completed_runs": 5
}
```

#### `POST /graph/create`
**Create New Workflow Graph**
- **Purpose**: Register a new workflow definition
- **Request Body**:
```json
{
  "nodes": ["split_text", "summarize_chunks", "merge_summaries"],
  "edges": {
    "split_text": ["summarize_chunks"],
    "summarize_chunks": ["merge_summaries"]
  },
  "entry_point": "split_text"
}
```
- **Response**:
```json
{
  "graph_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Graph created successfully",
  "nodes_count": 3
}
```

#### `POST /graph/run`
**Execute Workflow (Synchronous)**
- **Purpose**: Run a workflow and wait for completion
- **Request Body**:
```json
{
  "graph_id": "550e8400-e29b-41d4-a716-446655440000",
  "input_data": {
    "text": "Your text to process...",
    "max_length": 200,
    "chunk_size": 100
  }
}
```
- **Response**:
```json
{
  "run_id": "123e4567-e89b-12d3-a456-426614174000",
  "graph_id": "550e8400-e29b-41d4-a716-446655440000",
  "final_state": {
    "text": "Your text to process...",
    "refined_summary": "Processed summary text.",
    "current_length": 25,
    "refinement_iterations": 1
  },
  "execution_log": [
    {
      "node": "split_text",
      "timestamp": "2025-12-10T10:30:00.000Z",
      "duration_ms": 2.5,
      "iteration": 1
    }
  ],
  "status": "completed"
}
```

#### `GET /graph/state/{run_id}`
**Get Workflow State**
- **Purpose**: Retrieve stored execution results
- **Parameters**: `run_id` - UUID of the execution run
- **Response**:
```json
{
  "run_id": "123e4567-e89b-12d3-a456-426614174000",
  "graph_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": { /* final workflow state */ },
  "execution_log": [ /* execution steps */ ],
  "timestamp": "2025-12-10T10:30:00.000Z"
}
```

### Management Endpoints

#### `GET /graphs`
**List All Graphs**
- **Purpose**: Get all registered workflow graphs
- **Response**:
```json
{
  "graphs": [
    {
      "graph_id": "550e8400-e29b-41d4-a716-446655440000",
      "nodes": ["split_text", "summarize_chunks", "merge_summaries"],
      "entry_point": "split_text"
    }
  ]
}
```

#### `GET /runs`
**List All Runs**
- **Purpose**: Get all completed workflow executions
- **Response**:
```json
{
  "runs": [
    {
      "run_id": "123e4567-e89b-12d3-a456-426614174000",
      "graph_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2025-12-10T10:30:00.000Z",
      "status": "completed"
    }
  ]
}
```

### Advanced Endpoints

#### `POST /run_async`
**Execute Workflow (Asynchronous)**
- **Purpose**: Start workflow in background, return immediately
- **Request Body**: Same as `/graph/run`
- **Response**:
```json
{
  "run_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "started"
}
```

#### `GET /run_status/{run_id}`
**Get Async Run Status**
- **Purpose**: Check progress of background execution
- **Response**:
```json
{
  "run_id": "123e4567-e89b-12d3-a456-426614174000",
  "graph_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "progress_percent": 60,
  "last_node": "refine_summary",
  "error_message": "",
  "start_time": "2025-12-10T10:30:00.000Z",
  "end_time": null
}
```

#### `WebSocket /ws/run/{graph_id}`
**Real-time Execution Streaming**
- **Purpose**: Stream live execution events
- **Connection**: WebSocket upgrade
- **Events Received**:
```json
{
  "event": "NODE_START",
  "node": "split_text",
  "timestamp": "2025-12-10T10:30:00.000Z",
  "run_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

## Core Components

### WorkflowState
**Type-safe state container**
```python
@dataclass
class WorkflowState:
    text: str
    max_length: int
    current_length: int = 0
    chunks: List[str] = field(default_factory=list)
    chunk_summaries: List[str] = field(default_factory=list)
    merged_summary: str = ""
    refined_summary: str = ""
    refinement_iterations: int = 0
    max_refinement_iterations: int = 5
    chunk_size: int = 50
    execution_metadata: Dict[str, Any] = field(default_factory=dict)
```

### WorkflowGraph
**Graph execution engine**
```python
class WorkflowGraph:
    def __init__(self, definition: GraphDefinition, registry: NodeRegistry)
    def execute(self, initial_state: WorkflowState) -> Tuple[WorkflowState, List[Dict]]
    def _get_next_node(self, current_node: str, state: WorkflowState) -> Optional[str]
    def _handle_loop_condition(self, next_nodes: List[str], state: WorkflowState) -> Optional[str]
```

### NodeRegistry
**Function registry and lookup**
```python
class NodeRegistry:
    def register_node(self, name: str, func: Callable)
    def get_node(self, name: str) -> Callable
    def has_node(self, name: str) -> bool
    def list_nodes(self) -> List[str]
```

## Workflow Implementation

### Summarization Pipeline
**Complete text summarization workflow with iterative refinement**

#### Workflow Nodes:

1. **split_text**
   - **Purpose**: Break input text into manageable chunks
   - **Input**: `text`, `chunk_size`
   - **Output**: `chunks` list
   - **Logic**: Word-boundary splitting to avoid breaking sentences

2. **summarize_chunks**
   - **Purpose**: Generate summary for each chunk using frequency scoring
   - **Input**: `chunks`
   - **Output**: `chunk_summaries`
   - **Algorithm**: 
     - Extract sentences from chunk
     - Calculate word frequencies (excluding stopwords)
     - Score sentences by frequency sum
     - Select highest scoring sentence
     - Compress to ~16 words

3. **merge_summaries**
   - **Purpose**: Combine all chunk summaries into single document
   - **Input**: `chunk_summaries`
   - **Output**: `merged_summary`, `current_length`
   - **Logic**: Join summaries with periods, track length

4. **refine_summary**
   - **Purpose**: Apply rule-based compression to meet length requirements
   - **Input**: `merged_summary`, `max_length`
   - **Output**: `refined_summary`, `current_length`
   - **Algorithm**:
     - Normalize spacing and fix periods
     - Filter out short/noisy fragments (< 4 words)
     - Build summary incrementally within length limit
     - Apply hard trim fallback if needed

5. **check_length_loop**
   - **Purpose**: Evaluate loop condition for iterative refinement
   - **Input**: `current_length`, `max_length`, `refinement_iterations`
   - **Output**: Loop decision (continue or exit)
   - **Logic**: Loop if length > max_length AND iterations < max_iterations

#### Workflow Graph:
```
split_text → summarize_chunks → merge_summaries → refine_summary → check_length_loop
                                                        ↑                    ↓
                                                        └────────────────────┘
                                                              (if loop condition met)
```

## Usage Examples

### Basic Workflow Execution
```bash
# Start the server
uvicorn app.main:app --reload --port 8000

# Get available graphs
curl http://localhost:8000/graphs

# Execute summarization
curl -X POST "http://localhost:8000/graph/run" \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": "your-graph-id-here",
    "input_data": {
      "text": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It uses algorithms to analyze data, identify patterns, and make predictions or decisions.",
      "max_length": 100
    }
  }'
```

### Async Execution with Monitoring
```bash
# Start async execution
curl -X POST "http://localhost:8000/run_async" \
  -H "Content-Type: application/json" \
  -d '{
    "graph_id": "your-graph-id-here",
    "input_data": {
      "text": "Your long text here...",
      "max_length": 200
    }
  }'

# Check status
curl "http://localhost:8000/run_status/your-run-id-here"
```

### WebSocket Monitoring
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/run/your-graph-id-here');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Execution event:', data);
};
```

### Python Client Usage
```python
from engine.state import WorkflowState
from engine.registry import NodeRegistry
from workflows.summarization.graph_def import create_summarization_graph

# Create workflow
registry = NodeRegistry()
graph = create_summarization_graph(registry)

# Execute
initial_state = WorkflowState(
    text="Your text here...",
    max_length=150
)
final_state, execution_log = graph.execute(initial_state)

print(f"Summary: {final_state.refined_summary}")
print(f"Length: {final_state.current_length}")
```

## Development Guide

### Adding New Workflows

1. **Create workflow nodes**:
```python
def my_custom_node(state: WorkflowState) -> WorkflowState:
    # Process state
    return state.copy_with_updates(
        # updated fields
    )
```

2. **Register nodes**:
```python
registry.register_node("my_custom_node", my_custom_node)
```

3. **Define graph structure**:
```python
graph_def = GraphDefinition(
    nodes=["node1", "node2", "node3"],
    edges={
        "node1": ["node2"],
        "node2": ["node3"]
    },
    entry_point="node1"
)
```

### Testing
```bash
# Unit tests (no server needed)
python test_workflow.py

# API integration tests
python test_api.py

# Manual API testing
./test_curl_examples.sh
```

### Error Handling
- **Validation errors**: 400 Bad Request with details
- **Not found errors**: 404 Not Found
- **Execution errors**: 500 Internal Server Error with stack trace
- **Timeout errors**: Automatic cleanup after max iterations

### Performance Considerations
- **Memory**: Immutable state updates prevent memory leaks
- **CPU**: Efficient graph traversal with loop detection
- **I/O**: Async execution prevents blocking
- **Scalability**: Stateless design supports horizontal scaling

### Security
- **Input validation**: Pydantic models validate all inputs
- **Error sanitization**: Stack traces logged but not exposed
- **Resource limits**: Max iteration limits prevent infinite loops
- **CORS**: Configurable for cross-origin requests