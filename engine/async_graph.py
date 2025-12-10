"""
Async workflow graph execution with WebSocket streaming.
"""
import asyncio
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import logging
import traceback

from engine.state import WorkflowState
from engine.graph import WorkflowGraph
from engine.websocket_manager import websocket_manager
from engine.job_tracker import job_tracker

logger = logging.getLogger(__name__)


class AsyncWorkflowGraph:
    """
    Async wrapper for WorkflowGraph with WebSocket streaming support.
    """
    
    def __init__(self, workflow_graph: WorkflowGraph):
        self.workflow_graph = workflow_graph
    
    async def execute_async(self, run_id: str, initial_state: WorkflowState) -> Tuple[WorkflowState, List[Dict[str, Any]]]:
        """
        Execute workflow asynchronously with WebSocket streaming.
        
        Args:
            run_id: Unique run ID for tracking
            initial_state: Starting state for the workflow
            
        Returns:
            Tuple of (final_state, execution_log)
        """
        graph_id = "async_execution"  # Could be passed as parameter
        execution_log: List[Dict[str, Any]] = []
        
        try:
            # Update job status
            await job_tracker.update_job_progress(run_id, "starting", 0, len(self.workflow_graph.definition.nodes))
            
            # Execute the workflow with streaming
            state = initial_state
            current_node = self.workflow_graph.definition.entry_point
            iteration_count = 0
            max_iterations = 1000
            
            logger.info(f"Starting async execution {run_id} from '{current_node}'")
            
            while current_node is not None and iteration_count < max_iterations:
                iteration_count += 1
                start_time = datetime.utcnow()
                
                logger.info(f"Executing node: {current_node} (iteration {iteration_count})")
                
                # Update job progress
                await job_tracker.update_job_progress(run_id, current_node, iteration_count - 1, len(self.workflow_graph.definition.nodes))
                
                try:
                    # Execute node (run in thread pool to avoid blocking)
                    node_func = self.workflow_graph.registry.get_node(current_node)
                    state = await asyncio.get_event_loop().run_in_executor(None, node_func, state)
                    
                except Exception as e:
                    error_msg = f"Node '{current_node}' failed: {str(e)}"
                    logger.error(error_msg)
                    await job_tracker.mark_job_failed(run_id, error_msg)
                    await websocket_manager.send_error(graph_id, error_msg)
                    raise RuntimeError(error_msg)
                
                end_time = datetime.utcnow()
                duration_ms = (end_time - start_time).total_seconds() * 1000
                
                # Create log entry
                log_entry = {
                    "node": current_node,
                    "timestamp": start_time.isoformat(),
                    "duration_ms": round(duration_ms, 2),
                    "iteration": iteration_count
                }
                execution_log.append(log_entry)
                
                # Stream to WebSocket clients immediately
                await websocket_manager.send_node_executed(
                    graph_id=graph_id,
                    node=current_node,
                    iteration=iteration_count,
                    timestamp=start_time.isoformat(),
                    state_snapshot={
                        "current_length": getattr(state, 'current_length', 0),
                        "refinement_iterations": getattr(state, 'refinement_iterations', 0)
                    }
                )
                
                logger.info(f"Completed node '{current_node}' in {duration_ms:.2f}ms")
                
                # Get next node
                current_node = self.workflow_graph._get_next_node(current_node, state)
                
                # Small delay to allow WebSocket messages to be sent
                await asyncio.sleep(0.01)
            
            if iteration_count >= max_iterations:
                error_msg = f"Execution exceeded maximum iterations ({max_iterations})"
                await job_tracker.mark_job_failed(run_id, error_msg)
                await websocket_manager.send_error(graph_id, error_msg)
                raise RuntimeError(error_msg)
            
            # Mark job as completed
            await job_tracker.mark_job_completed(run_id)
            
            # Send completion message
            await websocket_manager.send_completed(graph_id, run_id)
            
            logger.info(f"Async execution {run_id} completed after {iteration_count} iterations")
            
            return state, execution_log
            
        except Exception as e:
            error_msg = f"Async execution failed: {str(e)}"
            logger.error(f"Async execution {run_id} failed: {error_msg}")
            logger.error(traceback.format_exc())
            
            await job_tracker.mark_job_failed(run_id, error_msg)
            await websocket_manager.send_error(graph_id, error_msg)
            
            raise


async def execute_workflow_async(run_id: str, graph: WorkflowGraph, initial_state: WorkflowState):
    """
    Execute workflow in background task.
    
    Args:
        run_id: Unique run ID
        graph: WorkflowGraph to execute
        initial_state: Initial state
    """
    async_graph = AsyncWorkflowGraph(graph)
    
    try:
        final_state, execution_log = await async_graph.execute_async(run_id, initial_state)
        
        # Store results (you might want to store these in a database)
        logger.info(f"Async workflow {run_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Async workflow {run_id} failed: {str(e)}")
        # Error already handled in execute_async