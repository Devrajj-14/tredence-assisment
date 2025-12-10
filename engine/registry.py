"""
Node registry for managing workflow nodes and tools.
Provides registration and lookup functionality for workflow components.
"""
from typing import Dict, Callable, Any, List
import logging

from engine.state import WorkflowState

logger = logging.getLogger(__name__)


class NodeRegistry:
    """
    Registry for workflow nodes and tools.
    
    Manages the registration and retrieval of node functions that can be
    used in workflow graphs. Each node is a callable that takes a WorkflowState
    and returns a modified WorkflowState.
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._nodes: Dict[str, Callable[[WorkflowState], WorkflowState]] = {}
        self._tools: Dict[str, Any] = {}
        logger.info("Initialized NodeRegistry")
    
    def register_node(
        self,
        name: str,
        func: Callable[[WorkflowState], WorkflowState]
    ) -> None:
        """
        Register a node function in the registry.
        
        Args:
            name: Unique identifier for the node
            func: Callable that takes WorkflowState and returns WorkflowState
            
        Raises:
            ValueError: If node name already registered
        """
        if name in self._nodes:
            raise ValueError(f"Node '{name}' is already registered")
        
        self._nodes[name] = func
        logger.info(f"Registered node: {name}")
    
    def get_node(self, name: str) -> Callable[[WorkflowState], WorkflowState]:
        """
        Retrieve a registered node function.
        
        Args:
            name: Node identifier
            
        Returns:
            Node function
            
        Raises:
            KeyError: If node not found
        """
        if name not in self._nodes:
            raise KeyError(f"Node '{name}' not found in registry")
        
        return self._nodes[name]
    
    def register_tool(self, name: str, tool: Any) -> None:
        """
        Register a tool that can be used by nodes.
        
        Args:
            name: Unique identifier for the tool
            tool: Tool object or function
            
        Raises:
            ValueError: If tool name already registered
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")
        
        self._tools[name] = tool
        logger.info(f"Registered tool: {name}")
    
    def get_tool(self, name: str) -> Any:
        """
        Retrieve a registered tool.
        
        Args:
            name: Tool identifier
            
        Returns:
            Tool object
            
        Raises:
            KeyError: If tool not found
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        
        return self._tools[name]
    
    def list_nodes(self) -> List[str]:
        """
        Get list of all registered node names.
        
        Returns:
            List of node names
        """
        return list(self._nodes.keys())
    
    def list_tools(self) -> List[str]:
        """
        Get list of all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def has_node(self, name: str) -> bool:
        """
        Check if a node is registered.
        
        Args:
            name: Node identifier
            
        Returns:
            True if node exists, False otherwise
        """
        return name in self._nodes
    
    def has_tool(self, name: str) -> bool:
        """
        Check if a tool is registered.
        
        Args:
            name: Tool identifier
            
        Returns:
            True if tool exists, False otherwise
        """
        return name in self._tools
