"""
WebSocket manager for live log streaming during workflow execution.
"""
import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for live workflow log streaming.
    """
    
    def __init__(self):
        # Active connections per graph_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, graph_id: str):
        """
        Accept WebSocket connection and add to active connections.
        
        Args:
            websocket: WebSocket connection
            graph_id: Graph ID to subscribe to
        """
        await websocket.accept()
        
        async with self.connection_lock:
            if graph_id not in self.active_connections:
                self.active_connections[graph_id] = set()
            self.active_connections[graph_id].add(websocket)
        
        logger.info(f"WebSocket connected for graph {graph_id}")
    
    async def disconnect(self, websocket: WebSocket, graph_id: str):
        """
        Remove WebSocket connection from active connections.
        
        Args:
            websocket: WebSocket connection
            graph_id: Graph ID to unsubscribe from
        """
        async with self.connection_lock:
            if graph_id in self.active_connections:
                self.active_connections[graph_id].discard(websocket)
                if not self.active_connections[graph_id]:
                    del self.active_connections[graph_id]
        
        logger.info(f"WebSocket disconnected for graph {graph_id}")
    
    async def broadcast_to_graph(self, graph_id: str, message: dict):
        """
        Broadcast message to all WebSocket connections for a specific graph.
        
        Args:
            graph_id: Graph ID to broadcast to
            message: Message dictionary to send
        """
        if graph_id not in self.active_connections:
            return
        
        message_json = json.dumps(message)
        disconnected = set()
        
        # Send to all active connections for this graph
        for websocket in self.active_connections[graph_id].copy():
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected websockets
        if disconnected:
            async with self.connection_lock:
                self.active_connections[graph_id] -= disconnected
                if not self.active_connections[graph_id]:
                    del self.active_connections[graph_id]
    
    async def send_node_executed(self, graph_id: str, node: str, iteration: int, 
                                timestamp: str, state_snapshot: dict = None):
        """
        Send NODE_EXECUTED event to WebSocket clients.
        
        Args:
            graph_id: Graph ID
            node: Node name that was executed
            iteration: Iteration count
            timestamp: ISO timestamp
            state_snapshot: Optional state snapshot
        """
        message = {
            "event": "NODE_EXECUTED",
            "node": node,
            "iteration": iteration,
            "timestamp": timestamp
        }
        
        if state_snapshot:
            message["state_snapshot"] = state_snapshot
        
        await self.broadcast_to_graph(graph_id, message)
    
    async def send_completed(self, graph_id: str, run_id: str):
        """
        Send COMPLETED event to WebSocket clients.
        
        Args:
            graph_id: Graph ID
            run_id: Run ID that completed
        """
        message = {
            "event": "COMPLETED",
            "run_id": run_id,
            "graph_id": graph_id
        }
        
        await self.broadcast_to_graph(graph_id, message)
    
    async def send_error(self, graph_id: str, error_message: str):
        """
        Send ERROR event to WebSocket clients.
        
        Args:
            graph_id: Graph ID
            error_message: Error message
        """
        message = {
            "event": "ERROR",
            "message": error_message
        }
        
        await self.broadcast_to_graph(graph_id, message)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()