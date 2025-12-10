"""
Summarization workflow graph definition.
Defines the complete summarization + refinement workflow with looping.
"""
import logging

from engine.graph import WorkflowGraph, GraphDefinition
from engine.registry import NodeRegistry
from workflows.summarization.nodes_upgraded import (
    split_text,
    summarize_chunks,
    merge_summaries,
    refine_summary,
    check_length_loop
)

logger = logging.getLogger(__name__)


def create_summarization_graph(registry: NodeRegistry) -> WorkflowGraph:
    """
    Create and configure the complete summarization workflow graph.
    
    Workflow structure:
    1. split_text: Split input into chunks
    2. summarize_chunks: Generate summary per chunk
    3. merge_summaries: Combine all summaries
    4. refine_summary: Improve quality and reduce length
    5. check_length_loop: Check if refinement needed (loops back to 4 if needed)
    
    Args:
        registry: NodeRegistry to register nodes in
        
    Returns:
        Configured WorkflowGraph ready for execution
    """
    # Register all nodes
    registry.register_node("split_text", split_text)
    registry.register_node("summarize_chunks", summarize_chunks)
    registry.register_node("merge_summaries", merge_summaries)
    registry.register_node("refine_summary", refine_summary)
    registry.register_node("check_length_loop", check_length_loop)
    
    logger.info("Registered all summarization nodes")
    
    # Define graph structure with loop
    graph_def = GraphDefinition(
        nodes=[
            "split_text",
            "summarize_chunks",
            "merge_summaries",
            "refine_summary",
            "check_length_loop"
        ],
        edges={
            "split_text": ["summarize_chunks"],
            "summarize_chunks": ["merge_summaries"],
            "merge_summaries": ["refine_summary"],
            "refine_summary": ["check_length_loop"],
            "check_length_loop": ["refine_summary"]  # Loop back or exit
        },
        entry_point="split_text"
    )
    
    # Create and return the graph
    graph = WorkflowGraph(graph_def, registry)
    
    logger.info("Created summarization workflow graph with loop support")
    
    return graph
