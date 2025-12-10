"""
Job tracker for async workflow execution with status monitoring.
"""
import asyncio
from typing import Dict, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution status."""
    STARTED = "started"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobInfo:
    """Information about a running job."""
    
    def __init__(self, run_id: str, graph_id: str):
        self.run_id = run_id
        self.graph_id = graph_id
        self.status = JobStatus.STARTED
        self.progress_percent = 0
        self.last_node = ""
        self.error_message = ""
        self.start_time = datetime.utcnow()
        self.end_time = None
        self.total_nodes = 0
        self.completed_nodes = 0
    
    def update_progress(self, node: str, completed_nodes: int, total_nodes: int):
        """Update job progress."""
        self.last_node = node
        self.completed_nodes = completed_nodes
        self.total_nodes = total_nodes
        self.progress_percent = int((completed_nodes / total_nodes) * 100) if total_nodes > 0 else 0
        self.status = JobStatus.RUNNING
    
    def mark_completed(self):
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.progress_percent = 100
        self.end_time = datetime.utcnow()
    
    def mark_failed(self, error_message: str):
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.end_time = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "run_id": self.run_id,
            "graph_id": self.graph_id,
            "status": self.status.value,
            "progress_percent": self.progress_percent,
            "last_node": self.last_node,
            "error_message": self.error_message,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None
        }


class JobTracker:
    """
    Tracks async workflow execution jobs.
    """
    
    def __init__(self):
        self.jobs: Dict[str, JobInfo] = {}
        self.lock = asyncio.Lock()
    
    async def create_job(self, run_id: str, graph_id: str) -> JobInfo:
        """
        Create a new job entry.
        
        Args:
            run_id: Unique run ID
            graph_id: Graph ID being executed
            
        Returns:
            JobInfo instance
        """
        async with self.lock:
            job = JobInfo(run_id, graph_id)
            self.jobs[run_id] = job
            logger.info(f"Created job {run_id} for graph {graph_id}")
            return job
    
    async def get_job(self, run_id: str) -> Optional[JobInfo]:
        """
        Get job information.
        
        Args:
            run_id: Run ID to look up
            
        Returns:
            JobInfo if found, None otherwise
        """
        async with self.lock:
            return self.jobs.get(run_id)
    
    async def update_job_progress(self, run_id: str, node: str, completed_nodes: int, total_nodes: int):
        """
        Update job progress.
        
        Args:
            run_id: Run ID
            node: Current node being executed
            completed_nodes: Number of completed nodes
            total_nodes: Total number of nodes
        """
        async with self.lock:
            if run_id in self.jobs:
                self.jobs[run_id].update_progress(node, completed_nodes, total_nodes)
                logger.debug(f"Job {run_id} progress: {completed_nodes}/{total_nodes} nodes")
    
    async def mark_job_completed(self, run_id: str):
        """
        Mark job as completed.
        
        Args:
            run_id: Run ID
        """
        async with self.lock:
            if run_id in self.jobs:
                self.jobs[run_id].mark_completed()
                logger.info(f"Job {run_id} completed")
    
    async def mark_job_failed(self, run_id: str, error_message: str):
        """
        Mark job as failed.
        
        Args:
            run_id: Run ID
            error_message: Error message
        """
        async with self.lock:
            if run_id in self.jobs:
                self.jobs[run_id].mark_failed(error_message)
                logger.error(f"Job {run_id} failed: {error_message}")
    
    async def cleanup_old_jobs(self, max_age_hours: int = 24):
        """
        Clean up old completed/failed jobs.
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        async with self.lock:
            to_remove = []
            for run_id, job in self.jobs.items():
                if job.end_time and job.end_time.timestamp() < cutoff_time:
                    to_remove.append(run_id)
            
            for run_id in to_remove:
                del self.jobs[run_id]
                logger.info(f"Cleaned up old job {run_id}")


# Global job tracker instance
job_tracker = JobTracker()