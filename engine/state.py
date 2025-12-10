"""
Workflow state management using Pydantic models.
Defines the state structure that flows through the workflow graph.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict


class WorkflowState(BaseModel):
    """
    Pydantic model representing the state of a workflow execution.
    
    This state is passed between nodes and modified during execution.
    All workflow data must be stored in this state object.
    """
    
    # Input fields
    text: str = Field(default="", description="Original input text to process")
    max_length: int = Field(default=100, description="Maximum allowed summary length")
    chunk_size: int = Field(default=50, description="Size of text chunks for splitting")
    
    # Processing fields
    chunks: List[str] = Field(default_factory=list, description="Text split into chunks")
    chunk_summaries: List[str] = Field(default_factory=list, description="Summary for each chunk")
    merged_summary: str = Field(default="", description="Combined summary from all chunks")
    refined_summary: str = Field(default="", description="Final refined summary")
    
    # Control flow fields
    current_length: int = Field(default=0, description="Current summary length")
    refinement_iterations: int = Field(default=0, description="Number of refinement loops executed")
    max_refinement_iterations: int = Field(default=5, description="Maximum allowed refinement loops")
    
    # Metadata
    execution_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata collected during execution"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "text": "This is a long document that needs to be summarized...",
                "max_length": 100,
                "chunk_size": 50,
                "chunks": [],
                "chunk_summaries": [],
                "merged_summary": "",
                "refined_summary": "",
                "current_length": 0,
                "refinement_iterations": 0,
                "max_refinement_iterations": 5
            }
        }
    
    def copy_with_updates(self, **updates) -> "WorkflowState":
        """
        Create a new state instance with specified field updates.
        
        Args:
            **updates: Fields to update in the new state
            
        Returns:
            New WorkflowState instance with updates applied
        """
        current_data = self.model_dump()
        current_data.update(updates)
        return WorkflowState(**current_data)
