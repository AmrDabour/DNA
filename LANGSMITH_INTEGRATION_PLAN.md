# 🔬 LangSmith Professional Integration Plan

## DNA Analysis Agent - Observability, Tracing & Evaluation

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Environment Setup](#phase-1-environment-setup)
4. [Phase 2: Core Tracing Integration](#phase-2-core-tracing-integration)
5. [Phase 3: Custom Metadata & Tagging](#phase-3-custom-metadata--tagging)
6. [Phase 4: Evaluation Framework](#phase-4-evaluation-framework)
7. [Phase 5: Dataset Management](#phase-5-dataset-management)
8. [Phase 6: Production Monitoring](#phase-6-production-monitoring)
9. [Phase 7: Team Collaboration](#phase-7-team-collaboration)
10. [Implementation Checklist](#implementation-checklist)

---

## Overview

### What is LangSmith?

LangSmith is LangChain's platform for **debugging, testing, evaluating, and monitoring** LLM applications. It provides:

| Feature | Benefit |
|---------|---------|
| **Tracing** | Full visibility into every LLM call, tool invocation, and chain execution |
| **Debugging** | Identify bottlenecks, errors, and unexpected behaviors |
| **Evaluation** | Systematic testing with datasets and custom evaluators |
| **Monitoring** | Production metrics, latency tracking, cost analysis |
| **Collaboration** | Shared datasets, annotation queues, team dashboards |

### Why LangSmith for DNA Agent?

```
┌─────────────────────────────────────────────────────────────────┐
│                    DNA Analysis Agent                            │
├─────────────────────────────────────────────────────────────────┤
│  User Query → LangGraph Workflow → Tools → LLM → Response       │
│       ↓              ↓                ↓       ↓       ↓         │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              LangSmith Observability Layer              │    │
│  │  • Trace every workflow execution                       │    │
│  │  • Monitor tool success/failure rates                   │    │
│  │  • Track token usage and costs                          │    │
│  │  • Evaluate response quality                            │    │
│  │  • Debug production issues                              │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### 1. LangSmith Account Setup

```bash
# 1. Sign up at https://smith.langchain.com/
# 2. Create an organization (or use personal)
# 3. Generate API key from Settings → API Keys
```

### 2. Required Packages

```bash
# Add to requirements.txt
langsmith>=0.1.0
```

### 3. Pricing Tiers

| Tier | Traces/Month | Features | Recommended For |
|------|--------------|----------|-----------------|
| **Developer** | 5,000 | Basic tracing, 14-day retention | Development |
| **Plus** | 50,000 | Extended retention, collaboration | Staging |
| **Enterprise** | Unlimited | SSO, SLA, dedicated support | Production |

---

## Phase 1: Environment Setup

### 1.1 Environment Variables

Create/update `.env` file:

```env
# ============================================================
# LangSmith Configuration
# ============================================================

# Enable LangSmith tracing (set to "true" to enable)
LANGCHAIN_TRACING_V2=true

# Your LangSmith API key
LANGCHAIN_API_KEY=ls__xxxxxxxxxxxxxxxxxxxxxxxxxx

# Project name for organizing traces
LANGCHAIN_PROJECT=dna-analysis-agent

# Optional: Custom endpoint (for enterprise/self-hosted)
# LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

### 1.2 Update Configuration Module

**File: `agent/config.py`**

```python
"""
Agent Configuration - Environment variables and settings
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration for the DNA Agent"""
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
    
    # Model settings
    MODEL_NAME = os.getenv("AGENT_MODEL", "gemini-2.5-flash")
    TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("AGENT_MAX_TOKENS", "2048"))
    
    # Memory settings
    MEMORY_WINDOW_SIZE = int(os.getenv("MEMORY_WINDOW_SIZE", "20"))
    
    # File paths
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
    PATIENT_DATA_DIR = os.getenv("PATIENT_DATA_DIR", "./patient_snp_data")
    gender_model_dir = os.getenv("gender_model_dir", "./hapmap_data/gender_prediction_data")
    ANCESTRY_MODEL_DIR = os.getenv("ANCESTRY_MODEL_DIR", "./hapmap_data/Model_region")
    
    # Agent settings
    MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))
    TIMEOUT_SECONDS = int(os.getenv("AGENT_TIMEOUT", "120"))
    
    # ============================================================
    # LangSmith Configuration (NEW)
    # ============================================================
    LANGSMITH_ENABLED = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    LANGSMITH_API_KEY = os.getenv("LANGCHAIN_API_KEY")
    LANGSMITH_PROJECT = os.getenv("LANGCHAIN_PROJECT", "dna-analysis-agent")
    LANGSMITH_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.GEMINI_API_KEY and not cls.GOOGLE_AI_API_KEY:
            raise ValueError("GEMINI_API_KEY or GOOGLE_AI_API_KEY is required")
        return True
    
    @classmethod
    def get_api_key(cls):
        """Get the first available API key"""
        return cls.GEMINI_API_KEY or cls.GOOGLE_AI_API_KEY
    
    @classmethod
    def is_langsmith_enabled(cls) -> bool:
        """Check if LangSmith is properly configured"""
        return cls.LANGSMITH_ENABLED and bool(cls.LANGSMITH_API_KEY)


config = Config()
```

---

## Phase 2: Core Tracing Integration

### 2.1 Create LangSmith Utility Module

**File: `agent/langsmith_utils.py`**

```python
"""
LangSmith Utilities - Tracing, callbacks, and monitoring helpers
"""
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from functools import wraps
import logging

from langsmith import Client
from langsmith.run_trees import RunTree
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.tracers import LangChainTracer

from .config import config

logger = logging.getLogger(__name__)


# ============================================================
# LangSmith Client Singleton
# ============================================================

_langsmith_client: Optional[Client] = None


def get_langsmith_client() -> Optional[Client]:
    """Get or create LangSmith client singleton"""
    global _langsmith_client
    
    if not config.is_langsmith_enabled():
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
) -> Optional[LangChainTracer]:
    """
    Get a LangChain tracer configured for LangSmith
    
    Args:
        project_name: Override default project name
        tags: Custom tags for filtering traces
        metadata: Additional metadata to attach to traces
    
    Returns:
        LangChainTracer if LangSmith is enabled, None otherwise
    """
    if not config.is_langsmith_enabled():
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
        super().__init__()
        self.session_id = session_id
        self.user_id = user_id
        self.metadata = metadata or {}
        self.run_start_time: Optional[datetime] = None
        self.tool_calls: List[Dict[str, Any]] = []
        self.errors: List[str] = []
    
    @property
    def always_verbose(self) -> bool:
        return True
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        """Called when LLM starts"""
        self.run_start_time = datetime.now()
        logger.debug(f"[LangSmith] LLM started for session {self.session_id}")
    
    def on_llm_end(self, response, **kwargs):
        """Called when LLM completes"""
        duration = (datetime.now() - self.run_start_time).total_seconds() if self.run_start_time else 0
        logger.debug(f"[LangSmith] LLM completed in {duration:.2f}s for session {self.session_id}")
    
    def on_llm_error(self, error: Exception, **kwargs):
        """Called when LLM errors"""
        self.errors.append(str(error))
        logger.error(f"[LangSmith] LLM error for session {self.session_id}: {error}")
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs):
        """Called when tool starts"""
        tool_name = serialized.get("name", "unknown")
        self.tool_calls.append({
            "name": tool_name,
            "start_time": datetime.now().isoformat(),
            "input": input_str[:500]  # Truncate long inputs
        })
        logger.debug(f"[LangSmith] Tool '{tool_name}' started")
    
    def on_tool_end(self, output: str, **kwargs):
        """Called when tool completes"""
        if self.tool_calls:
            self.tool_calls[-1]["end_time"] = datetime.now().isoformat()
            self.tool_calls[-1]["success"] = True
    
    def on_tool_error(self, error: Exception, **kwargs):
        """Called when tool errors"""
        if self.tool_calls:
            self.tool_calls[-1]["error"] = str(error)
            self.tool_calls[-1]["success"] = False
        self.errors.append(f"Tool error: {error}")
    
    def get_run_metadata(self) -> Dict[str, Any]:
        """Get aggregated metadata for the run"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "tool_calls_count": len(self.tool_calls),
            "errors_count": len(self.errors),
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
            if not config.is_langsmith_enabled():
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
                    rt.end(outputs={"result": str(result)[:1000]})
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
```

### 2.2 Update Workflow with Tracing

**File: `agent/workflow.py`** - Updated with LangSmith integration

```python
"""
LangGraph Workflow - DNA Agent Workflow Definition with LangSmith Tracing
"""
from typing import TypedDict, Dict, Any, List, Optional, Annotated
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.callbacks import CallbackManager
import json
import operator
import uuid

from .config import config
from .tools import get_all_tools, get_tools_description, POPULATION_INFO
from .memory import ChatMemory, get_memory
from .langsmith_utils import (
    get_tracer,
    DNAAgentCallbackHandler,
    trace_agent_run,
    get_langsmith_client
)


# [... AgentState and SYSTEM_PROMPT remain the same ...]


class DNAAgentWorkflow:
    """LangGraph workflow for DNA Analysis Agent with LangSmith tracing"""
    
    def __init__(self):
        self.llm = self._init_llm()
        self.tools = get_all_tools()
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        self.graph = self._build_graph()
    
    def _init_llm(self) -> ChatGoogleGenerativeAI:
        """Initialize the LLM with optional LangSmith tracing"""
        callbacks = []
        
        # Add LangSmith tracer if enabled
        tracer = get_tracer()
        if tracer:
            callbacks.append(tracer)
        
        return ChatGoogleGenerativeAI(
            model=config.MODEL_NAME,
            google_api_key=config.get_api_key(),
            temperature=config.TEMPERATURE,
            max_output_tokens=config.MAX_TOKENS,
            callbacks=callbacks if callbacks else None
        )
    
    def _get_callback_manager(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[CallbackManager]:
        """Get callback manager with LangSmith handlers"""
        if not config.is_langsmith_enabled():
            return None
        
        handlers = []
        
        # Add LangSmith tracer
        tracer = get_tracer(
            tags=[f"session:{session_id}"],
            metadata=metadata
        )
        if tracer:
            handlers.append(tracer)
        
        # Add custom DNA agent handler
        custom_handler = DNAAgentCallbackHandler(
            session_id=session_id,
            user_id=user_id,
            metadata=metadata
        )
        handlers.append(custom_handler)
        
        return CallbackManager(handlers) if handlers else None
    
    # [... rest of the workflow methods ...]
    
    @trace_agent_run(name="dna_agent_chat", tags=["chat", "production"])
    def run(
        self,
        user_input: str,
        session_id: str,
        chat_history: List[Dict[str, str]] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run the agent workflow with LangSmith tracing
        
        Args:
            user_input: The user's message
            session_id: Session identifier for memory
            chat_history: Previous conversation messages
            user_id: Optional user identifier for tracking
            metadata: Optional metadata for tracing
        
        Returns:
            dict: Contains response and other metadata including run_id
        """
        # Generate unique run ID for LangSmith tracking
        run_id = str(uuid.uuid4())
        
        # Build trace metadata
        trace_metadata = {
            "run_id": run_id,
            "session_id": session_id,
            "user_id": user_id,
            "input_length": len(user_input),
            "history_length": len(chat_history) if chat_history else 0,
            **(metadata or {})
        }
        
        # Initialize state
        initial_state: AgentState = {
            "session_id": session_id,
            "messages": [],
            "chat_history": chat_history or [],
            "user_input": user_input,
            "stage": "init",
            "iteration": 0,
            "max_iterations": config.MAX_ITERATIONS,
            "tool_calls": [],
            "tool_results": [],
            "context": trace_metadata,
            "response": "",
            "error": ""
        }
        
        # Get callback manager for tracing
        callback_manager = self._get_callback_manager(
            session_id=session_id,
            user_id=user_id,
            metadata=trace_metadata
        )
        
        # Run the graph with tracing
        try:
            result = self.graph.invoke(
                initial_state,
                config={"callbacks": callback_manager} if callback_manager else None
            )
            
            return {
                "success": True,
                "response": result.get("response", ""),
                "stage": result.get("stage", "complete"),
                "tool_results": result.get("tool_results", []),
                "iterations": result.get("iteration", 0),
                "run_id": run_id  # Return for feedback submission
            }
        except Exception as e:
            return {
                "success": False,
                "response": f"An error occurred: {str(e)}",
                "error": str(e),
                "run_id": run_id
            }
```

---

## Phase 3: Custom Metadata & Tagging

### 3.1 Tagging Strategy

Implement consistent tagging for filtering and analysis:

```python
# agent/langsmith_tags.py
"""
LangSmith Tagging Constants and Utilities
"""
from enum import Enum
from typing import List


class TraceTags(str, Enum):
    """Standard tags for DNA Agent traces"""
    
    # Environment tags
    PRODUCTION = "env:production"
    STAGING = "env:staging"
    DEVELOPMENT = "env:development"
    
    # Feature tags
    ANALYSIS = "feature:analysis"
    PREDICTION = "feature:prediction"
    IMAGE_GEN = "feature:image_generation"
    EDUCATION = "feature:education"
    
    # Tool category tags
    TOOL_SNP = "tool:snp"
    TOOL_SAMPLE = "tool:sample"
    TOOL_DISEASE = "tool:disease"
    TOOL_TRAITS = "tool:traits"
    
    # Quality tags
    HIGH_CONFIDENCE = "quality:high_confidence"
    LOW_CONFIDENCE = "quality:low_confidence"
    NEEDS_REVIEW = "quality:needs_review"


def get_tags_for_tools(tool_names: List[str]) -> List[str]:
    """Generate tags based on tools used"""
    tags = []
    
    tool_tag_map = {
        "analyze_snp_file": [TraceTags.ANALYSIS, TraceTags.TOOL_SNP],
        "get_disease_risk_from_sample": [TraceTags.PREDICTION, TraceTags.TOOL_DISEASE],
        "predict_physical_characteristics": [TraceTags.PREDICTION, TraceTags.TOOL_TRAITS],
        "generate_person_image": [TraceTags.IMAGE_GEN],
        "get_genetic_fun_facts": [TraceTags.EDUCATION],
    }
    
    for tool_name in tool_names:
        if tool_name in tool_tag_map:
            tags.extend([t.value for t in tool_tag_map[tool_name]])
    
    return list(set(tags))
```

### 3.2 Rich Metadata Schema

```python
# agent/langsmith_metadata.py
"""
LangSmith Metadata Schemas
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class RunMetadata:
    """Standard metadata for all runs"""
    
    # Required fields
    run_id: str
    session_id: str
    timestamp: str
    
    # User information
    user_id: Optional[str] = None
    user_tier: Optional[str] = None  # "free", "premium", "enterprise"
    
    # Request information
    input_length: int = 0
    input_tokens_estimate: int = 0
    
    # Context information
    sample_file: Optional[str] = None
    population: Optional[str] = None
    gender: Optional[str] = None
    
    # Tool execution
    tools_requested: List[str] = None
    tools_executed: List[str] = None
    
    # Performance
    total_duration_ms: Optional[float] = None
    llm_duration_ms: Optional[float] = None
    tool_duration_ms: Optional[float] = None
    
    # Outcome
    success: bool = True
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.tools_requested is None:
            self.tools_requested = []
        if self.tools_executed is None:
            self.tools_executed = []
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def create(cls, session_id: str, **kwargs) -> "RunMetadata":
        """Factory method to create metadata with defaults"""
        import uuid
        return cls(
            run_id=str(uuid.uuid4()),
            session_id=session_id,
            timestamp=datetime.now().isoformat(),
            **kwargs
        )
```

---

## Phase 4: Evaluation Framework

### 4.1 Create Evaluation Module

**File: `agent/evaluation.py`**

```python
"""
LangSmith Evaluation Framework for DNA Agent
"""
import os
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import json

from langsmith import Client
from langsmith.evaluation import evaluate, EvaluationResult
from langchain_core.messages import HumanMessage

from .config import config
from .workflow import get_workflow


# ============================================================
# Custom Evaluators
# ============================================================

def accuracy_evaluator(run, example) -> EvaluationResult:
    """
    Evaluate accuracy of genetic predictions
    Compare predicted values with ground truth
    """
    prediction = run.outputs.get("response", "")
    expected = example.outputs.get("expected_response", "")
    
    # Check for key information presence
    score = 0.0
    expected_elements = example.outputs.get("expected_elements", [])
    
    if expected_elements:
        matches = sum(1 for elem in expected_elements if elem.lower() in prediction.lower())
        score = matches / len(expected_elements)
    
    return EvaluationResult(
        key="accuracy",
        score=score,
        comment=f"Matched {int(score * 100)}% of expected elements"
    )


def tool_usage_evaluator(run, example) -> EvaluationResult:
    """
    Evaluate if the correct tools were used
    """
    expected_tools = set(example.outputs.get("expected_tools", []))
    actual_tools = set(run.outputs.get("tools_used", []))
    
    if not expected_tools:
        return EvaluationResult(key="tool_usage", score=1.0)
    
    # Calculate Jaccard similarity
    intersection = expected_tools & actual_tools
    union = expected_tools | actual_tools
    score = len(intersection) / len(union) if union else 1.0
    
    return EvaluationResult(
        key="tool_usage",
        score=score,
        comment=f"Expected: {expected_tools}, Actual: {actual_tools}"
    )


def safety_evaluator(run, example) -> EvaluationResult:
    """
    Evaluate safety of genetic information responses
    Check for appropriate disclaimers and non-deterministic language
    """
    response = run.outputs.get("response", "").lower()
    
    safety_phrases = [
        "statistical",
        "probability",
        "may",
        "might",
        "consult",
        "professional",
        "not a diagnosis"
    ]
    
    # Count safety phrases
    safety_count = sum(1 for phrase in safety_phrases if phrase in response)
    score = min(safety_count / 3, 1.0)  # Expect at least 3 safety phrases
    
    return EvaluationResult(
        key="safety",
        score=score,
        comment=f"Found {safety_count} safety indicators"
    )


def helpfulness_evaluator(run, example) -> EvaluationResult:
    """
    Evaluate overall helpfulness using LLM-as-judge
    """
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=config.get_api_key()
    )
    
    prompt = f"""Evaluate the helpfulness of this AI response to a genetic analysis question.

User Question: {example.inputs.get('user_input', '')}

AI Response: {run.outputs.get('response', '')}

Rate the helpfulness on a scale of 0-1:
- 0: Not helpful at all, incorrect or irrelevant
- 0.5: Partially helpful, some useful information
- 1: Very helpful, accurate and comprehensive

Return only a number between 0 and 1."""

    try:
        result = llm.invoke([HumanMessage(content=prompt)])
        score = float(result.content.strip())
        score = max(0, min(1, score))  # Clamp to 0-1
    except:
        score = 0.5  # Default if evaluation fails
    
    return EvaluationResult(
        key="helpfulness",
        score=score
    )


# ============================================================
# Dataset Management
# ============================================================

@dataclass
class TestCase:
    """Single test case for evaluation"""
    name: str
    user_input: str
    session_id: str
    expected_elements: List[str]
    expected_tools: List[str]
    category: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "inputs": {
                "user_input": self.user_input,
                "session_id": self.session_id
            },
            "outputs": {
                "expected_elements": self.expected_elements,
                "expected_tools": self.expected_tools
            },
            "metadata": {
                "name": self.name,
                "category": self.category
            }
        }


# Standard test cases for DNA Agent
STANDARD_TEST_CASES = [
    TestCase(
        name="basic_analysis",
        user_input="Analyze the sample file uploads/NA20805_GIH_Male.csv",
        session_id="test_session_1",
        expected_elements=["GIH", "Male", "analysis", "prediction"],
        expected_tools=["analyze_snp_file"],
        category="analysis"
    ),
    TestCase(
        name="disease_risk",
        user_input="What are the disease risks for a CEU Male?",
        session_id="test_session_2",
        expected_elements=["disease", "risk", "CEU"],
        expected_tools=["assess_genetic_disease_risk"],
        category="prediction"
    ),
    TestCase(
        name="population_info",
        user_input="Tell me about the YRI population",
        session_id="test_session_3",
        expected_elements=["Yoruba", "Nigeria", "West Africa"],
        expected_tools=["get_population_info"],
        category="education"
    ),
    TestCase(
        name="physical_traits",
        user_input="What physical characteristics would a JPT Female likely have?",
        session_id="test_session_4",
        expected_elements=["Japanese", "hair", "eye"],
        expected_tools=["predict_physical_characteristics"],
        category="prediction"
    ),
    TestCase(
        name="genetic_facts",
        user_input="Give me some fun facts about genetics",
        session_id="test_session_5",
        expected_elements=["DNA", "genetic"],
        expected_tools=["get_genetic_fun_facts"],
        category="education"
    ),
]


def create_evaluation_dataset(
    dataset_name: str = "dna-agent-eval",
    test_cases: List[TestCase] = None
) -> str:
    """
    Create or update evaluation dataset in LangSmith
    
    Returns:
        Dataset ID
    """
    client = Client()
    
    if test_cases is None:
        test_cases = STANDARD_TEST_CASES
    
    # Create dataset
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="Evaluation dataset for DNA Analysis Agent"
    )
    
    # Add examples
    for tc in test_cases:
        client.create_example(
            inputs=tc.to_dict()["inputs"],
            outputs=tc.to_dict()["outputs"],
            metadata=tc.to_dict()["metadata"],
            dataset_id=dataset.id
        )
    
    return dataset.id


def run_evaluation(
    dataset_name: str = "dna-agent-eval",
    experiment_name: str = None,
    evaluators: List[Callable] = None
) -> Dict[str, Any]:
    """
    Run evaluation on the DNA Agent
    
    Args:
        dataset_name: Name of the evaluation dataset
        experiment_name: Name for this evaluation run
        evaluators: List of evaluator functions
    
    Returns:
        Evaluation results summary
    """
    if evaluators is None:
        evaluators = [
            accuracy_evaluator,
            tool_usage_evaluator,
            safety_evaluator,
            helpfulness_evaluator
        ]
    
    workflow = get_workflow()
    
    def run_agent(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper to run agent for evaluation"""
        result = workflow.run(
            user_input=inputs["user_input"],
            session_id=inputs["session_id"]
        )
        return {
            "response": result.get("response", ""),
            "tools_used": [
                tr.get("tool", "") 
                for tr in result.get("tool_results", [])
                if tr.get("success")
            ]
        }
    
    # Run evaluation
    results = evaluate(
        run_agent,
        data=dataset_name,
        evaluators=evaluators,
        experiment_prefix=experiment_name or "dna-agent-eval"
    )
    
    return results
```

### 4.2 Evaluation CLI

**File: `scripts/run_evaluation.py`**

```python
#!/usr/bin/env python
"""
CLI script to run LangSmith evaluations
"""
import argparse
import sys
from datetime import datetime

sys.path.insert(0, '.')

from agent.evaluation import (
    create_evaluation_dataset,
    run_evaluation,
    STANDARD_TEST_CASES
)


def main():
    parser = argparse.ArgumentParser(description="Run DNA Agent evaluations")
    parser.add_argument(
        "--create-dataset",
        action="store_true",
        help="Create/update evaluation dataset"
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run evaluation"
    )
    parser.add_argument(
        "--dataset",
        default="dna-agent-eval",
        help="Dataset name"
    )
    parser.add_argument(
        "--experiment",
        default=None,
        help="Experiment name (defaults to timestamp)"
    )
    
    args = parser.parse_args()
    
    if args.create_dataset:
        print(f"Creating dataset: {args.dataset}")
        dataset_id = create_evaluation_dataset(args.dataset)
        print(f"✅ Dataset created: {dataset_id}")
    
    if args.run:
        experiment_name = args.experiment or f"eval-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        print(f"Running evaluation: {experiment_name}")
        results = run_evaluation(
            dataset_name=args.dataset,
            experiment_name=experiment_name
        )
        print(f"✅ Evaluation complete!")
        print(f"View results at: https://smith.langchain.com/")


if __name__ == "__main__":
    main()
```

---

## Phase 5: Dataset Management

### 5.1 Dataset Builder

```python
# agent/datasets.py
"""
Dataset management for LangSmith evaluation and fine-tuning
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import csv
from pathlib import Path

from langsmith import Client

from .config import config


@dataclass
class DatasetExample:
    """Single dataset example"""
    input_text: str
    expected_output: str
    metadata: Dict[str, Any]
    
    def to_langsmith_format(self) -> Dict[str, Any]:
        return {
            "inputs": {"user_input": self.input_text},
            "outputs": {"expected_response": self.expected_output},
            "metadata": self.metadata
        }


class DatasetManager:
    """Manage evaluation datasets"""
    
    def __init__(self):
        self.client = Client() if config.is_langsmith_enabled() else None
    
    def create_dataset(
        self,
        name: str,
        description: str,
        examples: List[DatasetExample]
    ) -> Optional[str]:
        """Create a new dataset"""
        if not self.client:
            return None
        
        dataset = self.client.create_dataset(
            dataset_name=name,
            description=description
        )
        
        for example in examples:
            data = example.to_langsmith_format()
            self.client.create_example(
                inputs=data["inputs"],
                outputs=data["outputs"],
                metadata=data["metadata"],
                dataset_id=dataset.id
            )
        
        return dataset.id
    
    def load_from_csv(self, file_path: str) -> List[DatasetExample]:
        """Load examples from CSV file"""
        examples = []
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                examples.append(DatasetExample(
                    input_text=row.get("input", ""),
                    expected_output=row.get("expected_output", ""),
                    metadata={
                        "category": row.get("category", ""),
                        "difficulty": row.get("difficulty", "medium"),
                        "source": file_path
                    }
                ))
        
        return examples
    
    def export_production_traces(
        self,
        project_name: str,
        output_file: str,
        limit: int = 1000,
        filter_feedback: Optional[str] = None
    ) -> int:
        """
        Export production traces for analysis or fine-tuning
        
        Args:
            project_name: LangSmith project name
            output_file: Output JSON file path
            limit: Maximum traces to export
            filter_feedback: Filter by feedback key (e.g., "user_rating")
        
        Returns:
            Number of traces exported
        """
        if not self.client:
            return 0
        
        runs = self.client.list_runs(
            project_name=project_name,
            limit=limit
        )
        
        exported = []
        for run in runs:
            if filter_feedback:
                feedbacks = list(self.client.list_feedback(run_ids=[run.id]))
                if not any(f.key == filter_feedback for f in feedbacks):
                    continue
            
            exported.append({
                "id": str(run.id),
                "inputs": run.inputs,
                "outputs": run.outputs,
                "start_time": run.start_time.isoformat() if run.start_time else None,
                "end_time": run.end_time.isoformat() if run.end_time else None,
                "error": run.error,
                "tags": run.tags,
                "metadata": run.extra
            })
        
        with open(output_file, 'w') as f:
            json.dump(exported, f, indent=2)
        
        return len(exported)
```

---

## Phase 6: Production Monitoring

### 6.1 Monitoring Dashboard Metrics

```python
# agent/monitoring.py
"""
Production monitoring utilities for LangSmith
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics

from langsmith import Client

from .config import config


@dataclass
class AgentMetrics:
    """Aggregated metrics for the DNA Agent"""
    
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    
    total_tokens: int
    avg_tokens_per_run: float
    
    top_tools: List[Dict[str, Any]]
    error_breakdown: Dict[str, int]
    
    time_period: str


class MonitoringService:
    """Service for monitoring DNA Agent performance"""
    
    def __init__(self):
        self.client = Client() if config.is_langsmith_enabled() else None
    
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
            return None
        
        project = project_name or config.LANGSMITH_PROJECT
        start_time = datetime.now() - timedelta(hours=hours)
        
        runs = list(self.client.list_runs(
            project_name=project,
            start_time=start_time
        ))
        
        if not runs:
            return None
        
        # Calculate metrics
        successful = [r for r in runs if not r.error]
        failed = [r for r in runs if r.error]
        
        latencies = []
        for r in successful:
            if r.start_time and r.end_time:
                latency = (r.end_time - r.start_time).total_seconds() * 1000
                latencies.append(latency)
        
        # Tool usage
        tool_counts = {}
        for r in runs:
            if r.outputs and "tools_used" in r.outputs:
                for tool in r.outputs["tools_used"]:
                    tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        # Error breakdown
        error_types = {}
        for r in failed:
            error_type = type(r.error).__name__ if r.error else "Unknown"
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return AgentMetrics(
            total_runs=len(runs),
            successful_runs=len(successful),
            failed_runs=len(failed),
            success_rate=len(successful) / len(runs) if runs else 0,
            avg_latency_ms=statistics.mean(latencies) if latencies else 0,
            p95_latency_ms=self._percentile(latencies, 95) if latencies else 0,
            p99_latency_ms=self._percentile(latencies, 99) if latencies else 0,
            total_tokens=0,  # Would need token tracking
            avg_tokens_per_run=0,
            top_tools=sorted(
                [{"name": k, "count": v} for k, v in tool_counts.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:10],
            error_breakdown=error_types,
            time_period=f"Last {hours} hours"
        )
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def create_alert_rules(self) -> Dict[str, Any]:
        """
        Define alert rules for monitoring
        (To be implemented with your alerting system)
        """
        return {
            "high_error_rate": {
                "condition": "error_rate > 0.1",
                "threshold": 0.1,
                "window": "5m",
                "severity": "critical"
            },
            "high_latency": {
                "condition": "p95_latency > 10000",
                "threshold": 10000,
                "window": "5m",
                "severity": "warning"
            },
            "tool_failures": {
                "condition": "tool_error_rate > 0.2",
                "threshold": 0.2,
                "window": "15m",
                "severity": "warning"
            }
        }
```

### 6.2 API Endpoint for Metrics

**Update `routes/agent_routes.py`**

```python
# Add to agent_routes.py

@agent_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """
    Get agent performance metrics from LangSmith
    ---
    tags:
      - Agent
    """
    try:
        from agent.monitoring import MonitoringService
        
        hours = request.args.get("hours", 24, type=int)
        monitoring = MonitoringService()
        metrics = monitoring.get_metrics(hours=hours)
        
        if not metrics:
            return jsonify({
                "success": False,
                "error": "Metrics not available. Check LangSmith configuration."
            })
        
        return jsonify({
            "success": True,
            "metrics": {
                "total_runs": metrics.total_runs,
                "success_rate": metrics.success_rate,
                "avg_latency_ms": metrics.avg_latency_ms,
                "p95_latency_ms": metrics.p95_latency_ms,
                "top_tools": metrics.top_tools,
                "time_period": metrics.time_period
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@agent_bp.route('/feedback', methods=['POST'])
def submit_user_feedback():
    """
    Submit user feedback for a run
    ---
    tags:
      - Agent
    """
    try:
        from agent.langsmith_utils import log_user_feedback
        
        data = request.json
        run_id = data.get("run_id")
        rating = data.get("rating", 3)  # 1-5 scale
        comment = data.get("comment")
        
        if not run_id:
            return jsonify({"success": False, "error": "run_id is required"})
        
        success = log_user_feedback(
            run_id=run_id,
            rating=rating,
            feedback_text=comment
        )
        
        return jsonify({
            "success": success,
            "message": "Feedback submitted" if success else "Failed to submit feedback"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
```

---

## Phase 7: Team Collaboration

### 7.1 Annotation Queue Setup

```python
# agent/annotation.py
"""
Annotation queue management for human review
"""
from typing import Optional, List, Dict, Any
from langsmith import Client

from .config import config


class AnnotationManager:
    """Manage annotation queues for human review"""
    
    def __init__(self):
        self.client = Client() if config.is_langsmith_enabled() else None
    
    def create_review_queue(
        self,
        name: str,
        description: str,
        criteria: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create an annotation queue for human review
        
        Args:
            name: Queue name
            description: Queue description
            criteria: Filtering criteria for runs
        
        Returns:
            Queue ID if created
        """
        # Note: Annotation queues are typically managed via LangSmith UI
        # This is a placeholder for programmatic access when available
        pass
    
    def add_run_to_queue(
        self,
        run_id: str,
        queue_id: str,
        priority: int = 0
    ) -> bool:
        """Add a run to annotation queue"""
        # Placeholder for API integration
        pass
    
    def get_runs_for_review(
        self,
        project_name: str,
        criteria: str = "low_confidence"
    ) -> List[Dict[str, Any]]:
        """
        Get runs that need human review
        
        Criteria options:
        - "low_confidence": Runs with low confidence scores
        - "errors": Runs that resulted in errors
        - "negative_feedback": Runs with negative user feedback
        - "long_latency": Runs with unusually long latency
        """
        if not self.client:
            return []
        
        runs = list(self.client.list_runs(
            project_name=project_name,
            limit=100
        ))
        
        flagged = []
        for run in runs:
            should_review = False
            reason = ""
            
            if criteria == "errors" and run.error:
                should_review = True
                reason = f"Error: {run.error}"
            elif criteria == "long_latency":
                if run.start_time and run.end_time:
                    latency = (run.end_time - run.start_time).total_seconds()
                    if latency > 30:  # Over 30 seconds
                        should_review = True
                        reason = f"High latency: {latency:.2f}s"
            
            if should_review:
                flagged.append({
                    "run_id": str(run.id),
                    "reason": reason,
                    "inputs": run.inputs,
                    "outputs": run.outputs
                })
        
        return flagged
```

---

## Implementation Checklist

### Phase 1: Setup (Day 1)
- [ ] Create LangSmith account and organization
- [ ] Generate API key
- [ ] Add environment variables to `.env`
- [ ] Update `requirements.txt` with `langsmith>=0.1.0`
- [ ] Update `agent/config.py` with LangSmith settings

### Phase 2: Core Tracing (Days 2-3)
- [ ] Create `agent/langsmith_utils.py`
- [ ] Implement `DNAAgentCallbackHandler`
- [ ] Update `DNAAgentWorkflow` with tracing
- [ ] Test basic tracing in development
- [ ] Verify traces appear in LangSmith dashboard

### Phase 3: Metadata & Tagging (Day 4)
- [ ] Create `agent/langsmith_tags.py`
- [ ] Create `agent/langsmith_metadata.py`
- [ ] Implement consistent tagging strategy
- [ ] Add rich metadata to all runs

### Phase 4: Evaluation (Days 5-7)
- [ ] Create `agent/evaluation.py`
- [ ] Define custom evaluators
- [ ] Create standard test cases
- [ ] Create evaluation dataset in LangSmith
- [ ] Run initial evaluation and analyze results

### Phase 5: Dataset Management (Day 8)
- [ ] Create `agent/datasets.py`
- [ ] Implement CSV import functionality
- [ ] Set up production trace export
- [ ] Create baseline datasets for regression testing

### Phase 6: Monitoring (Days 9-10)
- [ ] Create `agent/monitoring.py`
- [ ] Add `/metrics` API endpoint
- [ ] Add `/feedback` API endpoint
- [ ] Set up alert rules
- [ ] Create monitoring dashboard

### Phase 7: Collaboration (Day 11)
- [ ] Set up annotation queues in LangSmith UI
- [ ] Create `agent/annotation.py` helpers
- [ ] Define review criteria
- [ ] Document review workflow for team

### Final Steps (Day 12)
- [ ] End-to-end testing
- [ ] Documentation review
- [ ] Team training session
- [ ] Production deployment
- [ ] Monitor first week of production data

---

## Quick Start Commands

```bash
# Install dependencies
pip install langsmith

# Set environment variables
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=ls__xxxxxxxxxx
export LANGCHAIN_PROJECT=dna-analysis-agent

# Create evaluation dataset
python scripts/run_evaluation.py --create-dataset

# Run evaluation
python scripts/run_evaluation.py --run --experiment "baseline-v1"

# Export traces for analysis
python -c "from agent.datasets import DatasetManager; dm = DatasetManager(); dm.export_production_traces('dna-analysis-agent', 'traces.json')"
```

---

## Resources

- 📚 [LangSmith Documentation](https://docs.smith.langchain.com/)
- 🎥 [LangSmith YouTube Tutorials](https://www.youtube.com/langchain)
- 💬 [LangChain Discord](https://discord.gg/langchain)
- 📊 [LangSmith Dashboard](https://smith.langchain.com/)

---

*Last Updated: January 2026*
*Version: 1.0.0*




