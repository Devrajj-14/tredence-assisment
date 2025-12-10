from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from uuid import uuid4
import logging
import asyncio
from datetime import datetime

from engine.graph import WorkflowGraph, GraphDefinition
from engine.state import WorkflowState
from engine.registry import NodeRegistry
from engine.websocket_manager import websocket_manager
from engine.job_tracker import job_tracker, JobStatus
from engine.async_graph import execute_workflow_async
from workflows.summarization.graph_def import create_summarization_graph

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Workflow Engine",
    description="Production-grade workflow engine with summarization pipeline",
    version="1.0.0"
)

graphs_store: Dict[str, WorkflowGraph] = {}
runs_store: Dict[str, Dict[str, Any]] = {}
node_registry = NodeRegistry()


class CreateGraphRequest(BaseModel):
    nodes: List[str] = Field(..., description="List of node names in execution order")
    edges: Dict[str, List[str]] = Field(..., description="Adjacency list of node connections")
    entry_point: str = Field(..., description="Starting node name")


class CreateGraphResponse(BaseModel):
    graph_id: str
    message: str
    nodes_count: int


class RunGraphRequest(BaseModel):
    graph_id: str = Field(..., description="UUID of the graph to execute")
    input_data: Dict[str, Any] = Field(..., description="Initial state data")


class RunGraphResponse(BaseModel):
    run_id: str
    graph_id: str
    final_state: Dict[str, Any]
    execution_log: List[Dict[str, Any]]
    status: str


class StateResponse(BaseModel):
    run_id: str
    graph_id: str
    state: Dict[str, Any]
    execution_log: List[Dict[str, Any]]
    timestamp: str


class RunAsyncRequest(BaseModel):
    graph_id: str = Field(..., description="UUID of the graph to execute")
    input_data: Dict[str, Any] = Field(..., description="Initial state data")


class RunAsyncResponse(BaseModel):
    run_id: str
    status: str


class JobStatusResponse(BaseModel):
    run_id: str
    graph_id: str
    status: str
    progress_percent: int
    last_node: str
    error_message: str = ""
    start_time: str
    end_time: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    logger.info("Starting AI Workflow Engine...")
    graph_id = str(uuid4())
    graph = create_summarization_graph(node_registry)
    graphs_store[graph_id] = graph
    logger.info(f"Pre-registered summarization workflow with graph_id: {graph_id}")
    logger.info(f"Available nodes: {list(node_registry.list_nodes())}")


@app.get("/")
async def root():
    return {
        "status": "running",
        "service": "AI Workflow Engine",
        "version": "1.0.0",
        "registered_graphs": len(graphs_store),
        "completed_runs": len(runs_store)
    }


@app.post("/graph/create", response_model=CreateGraphResponse)
async def create_graph(request: CreateGraphRequest):
    try:
        graph_id = str(uuid4())
        graph_def = GraphDefinition(
            nodes=request.nodes,
            edges=request.edges,
            entry_point=request.entry_point
        )
        graph = WorkflowGraph(graph_def, node_registry)
        graphs_store[graph_id] = graph
        logger.info(f"Created graph {graph_id} with {len(request.nodes)} nodes")
        return CreateGraphResponse(
            graph_id=graph_id,
            message="Graph created successfully",
            nodes_count=len(request.nodes)
        )
    except Exception as e:
        logger.error(f"Failed to create graph: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Graph creation failed: {str(e)}")


@app.post("/graph/run", response_model=RunGraphResponse)
async def run_graph(request: RunGraphRequest):
    try:
        if request.graph_id not in graphs_store:
            raise HTTPException(
                status_code=404,
                detail=f"Graph {request.graph_id} not found"
            )
        
        graph = graphs_store[request.graph_id]
        run_id = str(uuid4())
        logger.info(f"Starting execution run_id={run_id} for graph_id={request.graph_id}")
        
        initial_state = WorkflowState(**request.input_data)
        final_state, execution_log = graph.execute(initial_state)
        
        runs_store[run_id] = {
            "run_id": run_id,
            "graph_id": request.graph_id,
            "state": final_state.model_dump(),
            "execution_log": execution_log,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed"
        }
        
        logger.info(f"Completed run_id={run_id} with {len(execution_log)} steps")
        
        return RunGraphResponse(
            run_id=run_id,
            graph_id=request.graph_id,
            final_state=final_state.model_dump(),
            execution_log=execution_log,
            status="completed"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Graph execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")


@app.get("/graph/state/{run_id}", response_model=StateResponse)
async def get_state(run_id: str):
    if run_id not in runs_store:
        raise HTTPException(
            status_code=404,
            detail=f"Run {run_id} not found"
        )
    
    run_data = runs_store[run_id]
    
    return StateResponse(
        run_id=run_data["run_id"],
        graph_id=run_data["graph_id"],
        state=run_data["state"],
        execution_log=run_data["execution_log"],
        timestamp=run_data["timestamp"]
    )


@app.get("/graphs")
async def list_graphs():
    return {
        "graphs": [
            {
                "graph_id": gid,
                "nodes": list(graph.definition.nodes),
                "entry_point": graph.definition.entry_point
            }
            for gid, graph in graphs_store.items()
        ]
    }


@app.get("/runs")
async def list_runs():
    return {
        "runs": [
            {
                "run_id": run_data["run_id"],
                "graph_id": run_data["graph_id"],
                "timestamp": run_data["timestamp"],
                "status": run_data["status"]
            }
            for run_data in runs_store.values()
        ]
    }


@app.websocket("/ws/run/{graph_id}")
async def websocket_endpoint(websocket: WebSocket, graph_id: str):
    if graph_id not in graphs_store:
        await websocket.accept()
        await websocket.send_json({
            "event": "ERROR",
            "message": "Graph not found"
        })
        await websocket.close()
        return
    
    await websocket_manager.connect(websocket, graph_id)
    
    try:
        while True:
            try:
                data = await websocket.receive_text()
                logger.debug(f"Received WebSocket message: {data}")
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect(websocket, graph_id)


@app.post("/run_async", response_model=RunAsyncResponse)
async def run_async(request: RunAsyncRequest, background_tasks: BackgroundTasks):
    if request.graph_id not in graphs_store:
        raise HTTPException(
            status_code=404,
            detail=f"Graph {request.graph_id} not found"
        )
    
    graph = graphs_store[request.graph_id]
    run_id = str(uuid4())
    
    await job_tracker.create_job(run_id, request.graph_id)
    initial_state = WorkflowState(**request.input_data)
    
    background_tasks.add_task(
        execute_workflow_async,
        run_id,
        graph,
        initial_state
    )
    
    logger.info(f"Started async execution {run_id} for graph {request.graph_id}")
    
    return RunAsyncResponse(
        run_id=run_id,
        status="started"
    )


@app.get("/run_status/{run_id}", response_model=JobStatusResponse)
async def get_run_status(run_id: str):
    job = await job_tracker.get_job(run_id)
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Run {run_id} not found"
        )
    
    job_dict = job.to_dict()
    
    return JobStatusResponse(
        run_id=job_dict["run_id"],
        graph_id=job_dict["graph_id"],
        status=job_dict["status"],
        progress_percent=job_dict["progress_percent"],
        last_node=job_dict["last_node"],
        error_message=job_dict["error_message"],
        start_time=job_dict["start_time"],
        end_time=job_dict["end_time"]
    )
