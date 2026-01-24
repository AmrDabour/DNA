"""
DNA Agent - LangGraph Agent for Genetic Prediction System
"""

from .config import config
from .workflow import DNAAgentWorkflow, get_workflow
from .memory import ChatMemory, get_memory, clear_memory

# LangSmith integration (optional - graceful fallback if not installed)
try:
    from .langsmith_utils import (
        get_langsmith_client,
        get_tracer,
        DNAAgentCallbackHandler,
        submit_feedback,
        log_user_feedback,
        is_langsmith_available
    )
    from .langsmith_tags import TraceTags, build_run_tags
    from .monitoring import MonitoringService, get_monitoring_service, AgentMetrics
    from .evaluation import (
        create_evaluation_dataset,
        run_evaluation,
        quick_evaluate_response,
        STANDARD_TEST_CASES
    )
    _langsmith_exports = [
        'get_langsmith_client',
        'get_tracer',
        'DNAAgentCallbackHandler',
        'submit_feedback',
        'log_user_feedback',
        'is_langsmith_available',
        'TraceTags',
        'build_run_tags',
        'MonitoringService',
        'get_monitoring_service',
        'AgentMetrics',
        'create_evaluation_dataset',
        'run_evaluation',
        'quick_evaluate_response',
        'STANDARD_TEST_CASES'
    ]
except ImportError:
    _langsmith_exports = []

__all__ = [
    'config',
    'DNAAgentWorkflow',
    'get_workflow',
    'ChatMemory',
    'get_memory',
    'clear_memory',
    *_langsmith_exports
]

