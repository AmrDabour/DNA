"""
LangSmith Utilities - Tracing, callbacks, and monitoring helpers
"""
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from functools import wraps
import logging
import uuid

logger = logging.getLogger(__name__)

# Lazy imports for optional LangSmith dependency
_langsmith_available = False
try:
    from langsmith import Client
    from langsmith.run_trees import RunTree
    from langchain_core.callbacks import BaseCallbackHandler
    from langchain_core.tracers import LangChainTracer
    _langsmith_available = True
except ImportError:
    logger.warning("LangSmith not installed. Tracing features will be disabled.")
    Client = None
    RunTree = None
    BaseCallbackHandler = object
    LangChainTracer = None

from .config import config


# ============================================================
# LangSmith Client Singleton
# ============================================================

_langsmith_client: Optional["Client"] = None


def is_langsmith_available() -> bool:
    """Check if LangSmith is installed and configured"""
    return _langsmith_available and config.is_langsmith_enabled()


def get_langsmith_client() -> Optional["Client"]:
    """Get or create LangSmith client singleton"""
    global _langsmith_client
    
    if not is_langsmith_available():
        return None
    
    if _langsmith_client is None:
        try:
            _langsmith_client = Client(
                api_key=config.LANGSMITH_API_KEY,
                api_url=config.LANGSMITH_ENDPOINT
            )
            logger.info("LangSmith client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LangSmith client: {e}")
            return None
    
    return _langsmith_client


def get_tracer(
    project_name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional["LangChainTracer"]:
    """
    Get a LangChain tracer configured for LangSmith
    
    Args:
        project_name: Override default project name
        tags: Custom tags for filtering traces
        metadata: Additional metadata to attach to traces
    
    Returns:
        LangChainTracer if LangSmith is enabled, None otherwise
    """
    if not is_langsmith_available():
        return None
    
    try:
        tracer = LangChainTracer(
            project_name=project_name or config.LANGSMITH_PROJECT
        )
        return tracer
    except Exception as e:
        logger.error(f"Failed to create LangSmith tracer: {e}")
        return None


# ============================================================
# Custom Callback Handler
# ============================================================

class DNAAgentCallbackHandler(BaseCallbackHandler):
    """
    Custom callback handler for DNA Agent with rich metadata
    """
    
    def __init__(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        if _langsmith_available:
            super().__init__()
        self.session_id = session_id
        self.user_id = user_id
        self.metadata = metadata or {}
        self.run_start_time: Optional[datetime] = None
        self.tool_calls: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.llm_calls: int = 0
        self.total_tokens: int = 0
    
    @property
    def always_verbose(self) -> bool:
        return True
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        """Called when LLM starts"""
        self.run_start_time = datetime.now()
        self.llm_calls += 1
        logger.debug(f"[LangSmith] LLM started for session {self.session_id}")
    
    def on_llm_end(self, response, **kwargs):
        """Called when LLM completes"""
        duration = (datetime.now() - self.run_start_time).total_seconds() if self.run_start_time else 0
        
        # Try to extract token usage
        if hasattr(response, 'llm_output') and response.llm_output:
            token_usage = response.llm_output.get('token_usage', {})
            self.total_tokens += token_usage.get('total_tokens', 0)
        
        logger.debug(f"[LangSmith] LLM completed in {duration:.2f}s for session {self.session_id}")
    
    def on_llm_error(self, error: Exception, **kwargs):
        """Called when LLM errors"""
        self.errors.append(f"LLM Error: {str(error)}")
        logger.error(f"[LangSmith] LLM error for session {self.session_id}: {error}")
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs):
        """Called when tool starts"""
        tool_name = serialized.get("name", "unknown")
        self.tool_calls.append({
            "name": tool_name,
            "start_time": datetime.now().isoformat(),
            "input": input_str[:500] if input_str else ""  # Truncate long inputs
        })
        logger.debug(f"[LangSmith] Tool '{tool_name}' started")
    
    def on_tool_end(self, output: str, **kwargs):
        """Called when tool completes"""
        if self.tool_calls:
            self.tool_calls[-1]["end_time"] = datetime.now().isoformat()
            self.tool_calls[-1]["success"] = True
            self.tool_calls[-1]["output_length"] = len(str(output)) if output else 0
    
    def on_tool_error(self, error: Exception, **kwargs):
        """Called when tool errors"""
        if self.tool_calls:
            self.tool_calls[-1]["error"] = str(error)
            self.tool_calls[-1]["success"] = False
        self.errors.append(f"Tool error: {error}")
        logger.error(f"[LangSmith] Tool error: {error}")
    
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs):
        """Called when chain starts"""
        logger.debug(f"[LangSmith] Chain started for session {self.session_id}")
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs):
        """Called when chain completes"""
        logger.debug(f"[LangSmith] Chain completed for session {self.session_id}")
    
    def on_chain_error(self, error: Exception, **kwargs):
        """Called when chain errors"""
        self.errors.append(f"Chain error: {str(error)}")
        logger.error(f"[LangSmith] Chain error for session {self.session_id}: {error}")
    
    def get_run_metadata(self) -> Dict[str, Any]:
        """Get aggregated metadata for the run"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "llm_calls": self.llm_calls,
            "total_tokens": self.total_tokens,
            "tool_calls_count": len(self.tool_calls),
            "tool_calls": self.tool_calls,
            "errors_count": len(self.errors),
            "errors": self.errors,
            "custom_metadata": self.metadata
        }


# ============================================================
# Tracing Decorator
# ============================================================

def trace_agent_run(
    name: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Decorator to trace agent functions with LangSmith
    
    Usage:
        @trace_agent_run(name="analyze_sample", tags=["analysis"])
        def my_function(sample_file: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not is_langsmith_available():
                return func(*args, **kwargs)
            
            client = get_langsmith_client()
            if not client:
                return func(*args, **kwargs)
            
            run_name = name or func.__name__
            run_tags = tags or []
            run_metadata = metadata or {}
            
            # Add function info to metadata
            run_metadata.update({
                "function_name": func.__name__,
                "timestamp": datetime.now().isoformat()
            })
            
            try:
                # Create run tree for detailed tracing
                with RunTree(
                    name=run_name,
                    project_name=config.LANGSMITH_PROJECT,
                    tags=run_tags,
                    extra=run_metadata
                ) as rt:
                    result = func(*args, **kwargs)
                    # Safely convert result to string for output
                    output_str = str(result)[:1000] if result else ""
                    rt.end(outputs={"result": output_str})
                    return result
            except Exception as e:
                logger.error(f"Error in traced function {run_name}: {e}")
                raise
        
        return wrapper
    return decorator


# ============================================================
# Feedback & Scoring
# ============================================================

def submit_feedback(
    run_id: str,
    key: str,
    score: float,
    comment: Optional[str] = None,
    source_info: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Submit feedback for a run (useful for RLHF and evaluation)
    
    Args:
        run_id: The LangSmith run ID
        key: Feedback key (e.g., "correctness", "helpfulness")
        score: Score value (typically 0-1)
        comment: Optional feedback comment
        source_info: Optional source information
    
    Returns:
        True if feedback was submitted successfully
    """
    client = get_langsmith_client()
    if not client:
        logger.warning("LangSmith not available, feedback not submitted")
        return False
    
    try:
        client.create_feedback(
            run_id=run_id,
            key=key,
            score=score,
            comment=comment,
            source_info=source_info
        )
        logger.info(f"Feedback submitted for run {run_id}: {key}={score}")
        return True
    except Exception as e:
        logger.error(f"Failed to submit feedback: {e}")
        return False


def log_user_feedback(
    run_id: str,
    rating: int,  # 1-5 star rating
    feedback_text: Optional[str] = None
) -> bool:
    """
    Log user feedback (thumbs up/down, star rating)
    
    Args:
        run_id: The LangSmith run ID
        rating: User rating (1-5)
        feedback_text: Optional user comment
    
    Returns:
        True if feedback was logged successfully
    """
    # Normalize to 0-1 scale
    normalized_score = (rating - 1) / 4.0
    
    return submit_feedback(
        run_id=run_id,
        key="user_rating",
        score=normalized_score,
        comment=feedback_text,
        source_info={"type": "user_feedback", "original_rating": rating}
    )


# ============================================================
# Utility Functions
# ============================================================

def generate_run_id() -> str:
    """Generate a unique run ID for tracking"""
    return str(uuid.uuid4())


def get_run_url(run_id: str, project_name: Optional[str] = None) -> str:
    """Get the LangSmith dashboard URL for a run"""
    project = project_name or config.LANGSMITH_PROJECT
    return f"https://smith.langchain.com/o/default/projects/p/{project}/r/{run_id}"






