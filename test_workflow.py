#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.state import WorkflowState
from engine.registry import NodeRegistry
from workflows.summarization.graph_def import create_summarization_graph
from workflows.summarization.nodes_upgraded import (
    split_text, summarize_chunks, merge_summaries, refine_summary
)


def test_workflow_engine():
    print("Testing Workflow Engine...")
    
    registry = NodeRegistry()
    graph = create_summarization_graph(registry)
    
    initial_state = WorkflowState(
        text="Machine learning enables computers to learn from data. "
             "Deep learning uses neural networks for pattern recognition. "
             "AI is transforming healthcare and finance industries.",
        max_length=100
    )
    
    final_state, execution_log = graph.execute(initial_state)
    
    assert final_state.refined_summary, "Should have a refined summary"
    assert len(final_state.refined_summary) <= final_state.max_length, "Should respect max length"
    assert final_state.current_length > 0, "Should have positive length"
    assert len(execution_log) > 0, "Should have execution log"
    
    print(f"✅ Input: {len(initial_state.text)} chars")
    print(f"✅ Output: {final_state.current_length} chars")
    print(f"✅ Summary: {final_state.refined_summary}")
    print(f"✅ Executed {len(execution_log)} steps")
    print("✅ Workflow engine test passed!")


def test_individual_nodes():
    print("\nTesting Individual Nodes...")
    
    state = WorkflowState(text="This is a test. It has multiple sentences.", max_length=50)
    result = split_text(state)
    assert result.chunks, "Should create chunks"
    print(f"✅ Split created {len(result.chunks)} chunks")
    
    result = summarize_chunks(result)
    assert result.chunk_summaries, "Should create summaries"
    print(f"✅ Summarize created {len(result.chunk_summaries)} summaries")
    
    result = merge_summaries(result)
    assert result.merged_summary, "Should create merged summary"
    print(f"✅ Merge created {len(result.merged_summary)} char summary")
    
    result = refine_summary(result)
    assert result.refined_summary, "Should create refined summary"
    print(f"✅ Refine created {len(result.refined_summary)} char final summary")
    
    print("✅ All node tests passed!")


if __name__ == "__main__":
    try:
        test_workflow_engine()
        test_individual_nodes()
        print("\n🎉 All tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)