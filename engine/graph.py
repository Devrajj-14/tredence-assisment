from typing import Dict, List, Tuple, Any, Optional, Callable
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from engine.state import WorkflowState
from engine.registry import NodeRegistry

logger = logging.getLogger(__name__)


class GraphDefinition(BaseModel):
    nodes: List[str] = Field(..., description="List of node names")
    edges: Dict[str, List[str]] = Field(..., description="Adjacency list of connections")
    entry_point: str = Field(..., description="Starting node")
    
    def validate_structure(self) -> None:
        if self.entry_point not in self.nodes:
            raise ValueError(f"Entry point '{self.entry_point}' not in nodes list")
        
        for source in self.edges.keys():
            if source not in self.nodes:
                raise ValueError(f"Edge source '{source}' not in nodes list")
        
        for targets in self.edges.values():
            for target in targets:
                if target not in self.nodes:
                    raise ValueError(f"Edge target '{target}' not in nodes list")


class WorkflowGraph:
    def __init__(self, definition: GraphDefinition, registry: NodeRegistry):
        definition.validate_structure()
        self.definition = definition
        self.registry = registry
        
        for node_name in definition.nodes:
            if not registry.has_node(node_name):
                raise ValueError(f"Node '{node_name}' not found in registry")
        
        logger.info(f"Initialized WorkflowGraph with {len(definition.nodes)} nodes")
    
    def execute(
        self,
        initial_state: WorkflowState
    ) -> Tuple[WorkflowState, List[Dict[str, Any]]]:
        state = initial_state
        execution_log: List[Dict[str, Any]] = []
        current_node = self.definition.entry_point
        visited_sequence: List[str] = []
        max_iterations = 1000
        iteration_count = 0
        
        logger.info(f"Starting graph execution from '{current_node}'")
        
        while current_node is not None:
            iteration_count += 1
            
            if iteration_count > max_iterations:
                raise RuntimeError(
                    f"Execution exceeded maximum iterations ({max_iterations}). "
                    f"Possible infinite loop detected."
                )
            
            start_time = datetime.utcnow()
            logger.info(f"Executing node: {current_node} (iteration {iteration_count})")
            
            try:
                node_func = self.registry.get_node(current_node)
                state = node_func(state)
                
            except Exception as e:
                logger.error(f"Node '{current_node}' execution failed: {str(e)}")
                raise RuntimeError(f"Node '{current_node}' failed: {str(e)}")
            
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            log_entry = {
                "node": current_node,
                "timestamp": start_time.isoformat(),
                "duration_ms": round(duration_ms, 2),
                "iteration": iteration_count
            }
            execution_log.append(log_entry)
            visited_sequence.append(current_node)
            
            logger.info(
                f"Completed node '{current_node}' in {duration_ms:.2f}ms"
            )
            
            current_node = self._get_next_node(current_node, state)
        
        logger.info(
            f"Graph execution completed after {iteration_count} iterations. "
            f"Path: {' -> '.join(visited_sequence)}"
        )
        
        return state, execution_log
    
    def _get_next_node(
        self,
        current_node: str,
        state: WorkflowState
    ) -> Optional[str]:
        if current_node not in self.definition.edges:
            logger.info(f"Node '{current_node}' has no outgoing edges. Workflow complete.")
            return None
        
        next_nodes = self.definition.edges[current_node]
        
        if not next_nodes:
            logger.info(f"Node '{current_node}' has empty edge list. Workflow complete.")
            return None
        
        if current_node == "check_length_loop":
            return self._handle_loop_condition(next_nodes, state)
        
        next_node = next_nodes[0]
        logger.debug(f"Next node: {next_node}")
        return next_node
    
    def _handle_loop_condition(
        self,
        next_nodes: List[str],
        state: WorkflowState
    ) -> Optional[str]:
        should_loop = (
            state.current_length > state.max_length and
            state.refinement_iterations < state.max_refinement_iterations
        )
        
        if should_loop:
            if "refine_summary" in next_nodes:
                logger.info(
                    f"Loop condition met: length={state.current_length} > "
                    f"max={state.max_length}, iteration={state.refinement_iterations}. "
                    f"Looping to refine_summary."
                )
                return "refine_summary"
        
        logger.info(
            f"Loop condition not met: length={state.current_length}, "
            f"max={state.max_length}, iterations={state.refinement_iterations}. "
            f"Exiting loop."
        )
        
        return None
