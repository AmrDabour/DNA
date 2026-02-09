"""
Production monitoring utilities for LangSmith
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import statistics
import logging

logger = logging.getLogger(__name__)

# Lazy import for optional LangSmith dependency
try:
    from langsmith import Client
    _langsmith_available = True
except ImportError:
    Client = None
    _langsmith_available = False

from .config import config


@dataclass
class AgentMetrics:
    """Aggregated metrics for the DNA Agent"""
    
    # Run counts
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    
    # Latency metrics (in milliseconds)
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    
    # Token usage
    total_tokens: int
    avg_tokens_per_run: float
    
    # Tool metrics
    total_tool_calls: int
    tool_success_rate: float
    top_tools: List[Dict[str, Any]]
    
    # Error metrics
    error_breakdown: Dict[str, int]
    
    # Time period
    time_period: str
    start_time: str
    end_time: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MonitoringService:
    """Service for monitoring DNA Agent performance"""
    
    def __init__(self):
        self.client = None
        if _langsmith_available and config.is_langsmith_enabled():
            try:
                self.client = Client(
                    api_key=config.LANGSMITH_API_KEY,
                    api_url=config.LANGSMITH_ENDPOINT
                )
            except Exception as e:
                logger.error(f"Failed to initialize LangSmith client for monitoring: {e}")
    
    def is_available(self) -> bool:
        """Check if monitoring is available"""
        return self.client is not None
    
    def get_metrics(
        self,
        hours: int = 24,
        project_name: Optional[str] = None
    ) -> Optional[AgentMetrics]:
        """
        Get aggregated metrics for the specified time period
        
        Args:
            hours: Number of hours to look back
            project_name: LangSmith project name
        
        Returns:
            AgentMetrics object with aggregated data
        """
        if not self.client:
            logger.warning("LangSmith client not available for monitoring")
            return None
        
        project = project_name or config.LANGSMITH_PROJECT
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        try:
            runs = list(self.client.list_runs(
                project_name=project,
                start_time=start_time,
                limit=10000  # Reasonable limit
            ))
        except Exception as e:
            logger.error(f"Failed to fetch runs from LangSmith: {e}")
            return None
        
        if not runs:
            logger.info(f"No runs found in the last {hours} hours")
            return self._empty_metrics(hours, start_time, end_time)
        
        # Separate successful and failed runs
        successful = [r for r in runs if not r.error]
        failed = [r for r in runs if r.error]
        
        # Calculate latencies
        latencies = []
        for r in runs:
            if r.start_time and r.end_time:
                latency = (r.end_time - r.start_time).total_seconds() * 1000
                latencies.append(latency)
        
        # Tool usage analysis
        tool_counts = {}
        tool_successes = {}
        total_tool_calls = 0
        
        for r in runs:
            if r.outputs and isinstance(r.outputs, dict):
                tools_used = r.outputs.get("tools_used", [])
                tool_results = r.outputs.get("tool_results", [])
                
                for tool in tools_used:
                    tool_counts[tool] = tool_counts.get(tool, 0) + 1
                    total_tool_calls += 1
                
                for tr in tool_results:
                    if isinstance(tr, dict):
                        tool_name = tr.get("tool", "")
                        if tr.get("success", False):
                            tool_successes[tool_name] = tool_successes.get(tool_name, 0) + 1
        
        # Error breakdown
        error_types = {}
        for r in failed:
            if r.error:
                error_str = str(r.error)
                # Extract error type
                if ":" in error_str:
                    error_type = error_str.split(":")[0].strip()
                else:
                    error_type = error_str[:50]
                error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Calculate tool success rate
        total_tool_successes = sum(tool_successes.values())
        tool_success_rate = total_tool_successes / total_tool_calls if total_tool_calls > 0 else 1.0
        
        return AgentMetrics(
            total_runs=len(runs),
            successful_runs=len(successful),
            failed_runs=len(failed),
            success_rate=len(successful) / len(runs) if runs else 0,
            
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            min_latency_ms=min(latencies) if latencies else 0,
            max_latency_ms=max(latencies) if latencies else 0,
            p50_latency_ms=self._percentile(latencies, 50) if latencies else 0,
            p95_latency_ms=self._percentile(latencies, 95) if latencies else 0,
            p99_latency_ms=self._percentile(latencies, 99) if latencies else 0,
            
            total_tokens=0,  # Would need specific token tracking
            avg_tokens_per_run=0,
            
            total_tool_calls=total_tool_calls,
            tool_success_rate=tool_success_rate,
            top_tools=sorted(
                [{"name": k, "count": v} for k, v in tool_counts.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:10],
            
            error_breakdown=error_types,
            
            time_period=f"Last {hours} hours",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat()
        )
    
    def _empty_metrics(
        self,
        hours: int,
        start_time: datetime,
        end_time: datetime
    ) -> AgentMetrics:
        """Return empty metrics when no data is available"""
        return AgentMetrics(
            total_runs=0,
            successful_runs=0,
            failed_runs=0,
            success_rate=0,
            avg_latency_ms=0,
            min_latency_ms=0,
            max_latency_ms=0,
            p50_latency_ms=0,
            p95_latency_ms=0,
            p99_latency_ms=0,
            total_tokens=0,
            avg_tokens_per_run=0,
            total_tool_calls=0,
            tool_success_rate=0,
            top_tools=[],
            error_breakdown={},
            time_period=f"Last {hours} hours",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat()
        )
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def get_recent_errors(
        self,
        hours: int = 24,
        limit: int = 50,
        project_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent error traces for debugging
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of errors to return
            project_name: LangSmith project name
        
        Returns:
            List of error details
        """
        if not self.client:
            return []
        
        project = project_name or config.LANGSMITH_PROJECT
        start_time = datetime.now() - timedelta(hours=hours)
        
        try:
            runs = list(self.client.list_runs(
                project_name=project,
                start_time=start_time,
                error=True,  # Only error runs
                limit=limit
            ))
        except Exception as e:
            logger.error(f"Failed to fetch error runs: {e}")
            return []
        
        errors = []
        for r in runs:
            errors.append({
                "run_id": str(r.id),
                "error": str(r.error),
                "timestamp": r.start_time.isoformat() if r.start_time else None,
                "inputs": r.inputs,
                "tags": r.tags,
                "url": f"https://smith.langchain.com/o/default/projects/p/{project}/r/{r.id}"
            })
        
        return errors
    
    def get_slow_runs(
        self,
        hours: int = 24,
        threshold_ms: float = 10000,
        limit: int = 50,
        project_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get runs that exceeded latency threshold
        
        Args:
            hours: Number of hours to look back
            threshold_ms: Latency threshold in milliseconds
            limit: Maximum number of runs to return
            project_name: LangSmith project name
        
        Returns:
            List of slow run details
        """
        if not self.client:
            return []
        
        project = project_name or config.LANGSMITH_PROJECT
        start_time = datetime.now() - timedelta(hours=hours)
        
        try:
            runs = list(self.client.list_runs(
                project_name=project,
                start_time=start_time,
                limit=1000
            ))
        except Exception as e:
            logger.error(f"Failed to fetch runs: {e}")
            return []
        
        slow_runs = []
        for r in runs:
            if r.start_time and r.end_time:
                latency_ms = (r.end_time - r.start_time).total_seconds() * 1000
                if latency_ms > threshold_ms:
                    slow_runs.append({
                        "run_id": str(r.id),
                        "latency_ms": latency_ms,
                        "timestamp": r.start_time.isoformat(),
                        "inputs": r.inputs,
                        "url": f"https://smith.langchain.com/o/default/projects/p/{project}/r/{r.id}"
                    })
        
        # Sort by latency descending
        slow_runs.sort(key=lambda x: x["latency_ms"], reverse=True)
        
        return slow_runs[:limit]


# Singleton instance
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Get or create monitoring service singleton"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service






