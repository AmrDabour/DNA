# 🧬 DNA Analysis AI Agent
## Comprehensive Presentation

---

# Slide 1: Introduction

## DNA Analysis Platform - AI Agent

### What We Built
A sophisticated **AI-powered DNA Analysis Agent** that can:
- 🧬 Analyze genetic data (SNP files)
- 🔮 Predict gender and ancestry from DNA
- 🏥 Assess genetic disease risks
- 🎨 Generate AI portraits based on genetic profile
- 📚 Provide genetic education

### Technologies Used
| Component | Technology |
|-----------|------------|
| **AI Model** | Google Gemini 2.0 Flash |
| **Agent Framework** | LangGraph |
| **Observability** | LangSmith |
| **Backend** | Python Flask |
| **Memory** | Redis + In-Memory |

---

# Slide 2: Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│                    (Web Chat / API)                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DNA AGENT WORKFLOW                           │
│                      (LangGraph)                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │ Analyze  │→ │ Use      │→ │ Generate │→ │ Handle       │    │
│  │ Intent   │  │ Tools    │  │ Response │  │ Error        │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │   Gemini   │  │   Tools    │  │   Memory   │
    │  2.0 Flash │  │   (25+)    │  │   (Redis)  │
    └────────────┘  └────────────┘  └────────────┘
           │               │               │
           └───────────────┴───────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │      LangSmith         │
              │   (Observability)      │
              └────────────────────────┘
```

---

# Slide 3: Core Components

## Agent Module Structure

```
agent/
├── workflow.py        # 🔄 LangGraph workflow definition
├── tools.py           # 🛠️ 25+ LangChain tools
├── config.py          # ⚙️ Agent configuration
├── memory.py          # 🧠 Conversation memory (Redis)
├── langsmith_utils.py # 📊 LangSmith integration
├── langsmith_tags.py  # 🏷️ Tracing tags
├── evaluation.py      # 🧪 Testing framework
└── monitoring.py      # 📈 Production monitoring
```

### Key Files Purpose:
| File | Purpose |
|------|---------|
| `workflow.py` | Defines the LangGraph state machine |
| `tools.py` | Implements 25+ tools for DNA analysis |
| `memory.py` | Redis-backed conversation persistence |
| `langsmith_utils.py` | Tracing and observability |

---

# Slide 4: LangGraph Workflow

## State Machine Design

### AgentState Definition
```python
class AgentState(TypedDict):
    # Session information
    session_id: str
    
    # Conversation
    messages: Annotated[List[Dict[str, str]], operator.add]
    chat_history: List[Dict[str, str]]
    
    # Current request
    user_input: str
    
    # Workflow control
    stage: str  # "init", "thinking", "tool_use", "responding", "complete", "error"
    iteration: int
    max_iterations: int
    
    # Tool execution
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    
    # User context
    user_id: int
```

---

# Slide 5: Workflow Nodes

## LangGraph Node Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTRY POINT                                   │
└──────────────────────────┬──────────────────────────────────────┘
                           ▼
              ┌────────────────────────┐
              │    analyze_intent      │ ← Analyze user request
              │    (LLM + Tools)       │   Decide action path
              └───────────┬────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│   use_tools   │ │   generate    │ │   handle      │
│               │ │   _response   │ │   _error      │
│ Execute tools │ │               │ │               │
│ Get results   │ │ Format output │ │ Error message │
└───────┬───────┘ └───────┬───────┘ └───────┬───────┘
        │                 │                 │
        └────────►────────┴────────◄────────┘
                          │
                          ▼
                       [ END ]
```

---

# Slide 6: Workflow Code

## Building the Graph

```python
def _build_graph(self) -> StateGraph:
    """Build the LangGraph workflow"""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyze_intent", self._analyze_intent_node)
    workflow.add_node("use_tools", self._use_tools_node)
    workflow.add_node("generate_response", self._generate_response_node)
    workflow.add_node("handle_error", self._handle_error_node)
    
    # Set entry point
    workflow.set_entry_point("analyze_intent")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "analyze_intent",
        self._route_after_analysis,
        {
            "use_tools": "use_tools",
            "respond": "generate_response",
            "error": "handle_error",
            "end": END
        }
    )
    
    # Compile the graph
    return workflow.compile()
```

---

# Slide 7: Google Gemini Integration

## LLM Configuration

### Model: Gemini 2.0 Flash

```python
# config.py
class Config:
    # Model settings
    MODEL_NAME = "gemini-2.5-flash"  # Google Gemini
    TEMPERATURE = 0.7
    MAX_TOKENS = 2048
    
    # Agent settings
    MAX_ITERATIONS = 10
    TIMEOUT_SECONDS = 120
```

### LLM Initialization

```python
def _init_llm(self) -> ChatGoogleGenerativeAI:
    """Initialize Gemini with LangSmith tracing"""
    return ChatGoogleGenerativeAI(
        model=config.MODEL_NAME,           # gemini-2.5-flash
        google_api_key=config.get_api_key(),
        temperature=config.TEMPERATURE,     # 0.7
        max_output_tokens=config.MAX_TOKENS,# 2048
        callbacks=[tracer] if tracer else None
    )
```

### Why Gemini 2.0 Flash?
- ⚡ Fast response time
- 💡 Excellent tool calling capabilities
- 📊 Good at structured output
- 💰 Cost-effective

---

# Slide 8: Tools Overview

## 25+ Specialized Tools

### Tool Categories

| Category | Tools Count | Examples |
|----------|-------------|----------|
| **Sample Management** | 5 | `list_available_samples`, `get_sample_info`, `compare_samples` |
| **Analysis** | 4 | `analyze_snp_file`, `query_snp`, `get_snp_statistics` |
| **Prediction** | 5 | `predict_physical_characteristics`, `assess_genetic_disease_risk`, `full_genetic_report` |
| **Image Generation** | 2 | `generate_person_image`, `generate_image_from_sample` |
| **Education** | 5 | `get_genetic_fun_facts`, `explain_snp_significance`, `get_ancestry_deep_dive` |
| **VEP Analysis** | 4 | `analyze_snp_effects`, `get_variant_pathogenicity` |

---

# Slide 9: Tool Implementation

## Sample Tool: Analyze SNP File

```python
@tool(args_schema=SampleFileInput)
def analyze_snp_file(sample_file: str) -> Dict[str, Any]:
    """
    Perform complete genetic analysis on an uploaded SNP file.
    Runs gender and ancestry prediction models.
    
    Args:
        sample_file: Path to the patient sample CSV file
        
    Returns:
        dict: Complete analysis with Gender, ancestry predictions
    """
    # Call ML prediction endpoint
    result = call_api("/api/process_snp_file", "POST", 
                      {"file_path": sample_file})
    
    # Extract predictions from result
    gender = extract_gender(result)
    population = extract_population(result)
    
    result["gender"] = gender
    result["population"] = population
    
    return result
```

---

# Slide 10: Tool Categories Detail

## Analysis Tools

```python
@tool
def query_snp(sample_file: str, snp_id: str) -> Dict:
    """Query specific SNP value (e.g., rs12345)"""
    
@tool  
def get_snp_statistics(sample_file: str) -> Dict:
    """Get chromosome distribution, allele frequencies"""
```

## Prediction Tools

```python
@tool
def predict_physical_characteristics(gender: str, population: str) -> Dict:
    """Predict hair, eyes, skin, facial features"""

@tool
def assess_genetic_disease_risk(gender: str, population: str) -> Dict:
    """Assess disease risks based on genetics"""

@tool
def full_genetic_report(sample_file: str) -> Dict:
    """Complete genetic report with all analyses"""
```

## Image Generation Tools

```python
@tool
def generate_image_from_sample(sample_file: str, gender: str, population: str) -> Dict:
    """Generate AI portrait from genetic profile"""
```

---

# Slide 11: VEP Tools (Variant Effect Predictor)

## Advanced Genetic Analysis

```python
@tool
def analyze_snp_effects(sample_file: str, limit: int = 50) -> Dict:
    """
    Analyze biological effects using Ensembl VEP.
    Returns:
    - Gene impact predictions
    - Pathogenicity scores
    - Functional annotations
    """

@tool
def get_variant_pathogenicity(rs_id: str) -> Dict:
    """
    Get pathogenicity information for specific SNP.
    Returns:
    - CADD score
    - SIFT/PolyPhen predictions
    - Clinical significance
    """

@tool
def get_population_frequencies_vep(sample_file: str) -> Dict:
    """
    Compare patient alleles to population frequencies.
    Data from gnomAD/1000 Genomes.
    """
```

---

# Slide 12: Memory System

## Conversation Persistence

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      ChatMemory                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Messages   │    │   Context    │    │   Redis      │      │
│  │   (History)  │◄──►│   (Files)    │◄──►│   Sync       │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
class ChatMemory:
    def __init__(self, window_size: int = 20, session_id: str = None):
        self.window_size = window_size  # Keep last 20 messages
        self.session_id = session_id
        self.messages: List[Message] = []
        self.context: Dict = {}  # Current file, patient, etc.
    
    def add_user_message(self, content: str):
        """Add message and sync to Redis"""
        self.messages.append(Message(role="user", content=content))
        self._trim_history()
        self._save_to_redis()
    
    def set_context(self, key: str, value):
        """Store context (current file, gender, population)"""
        self.context[key] = value
        self._save_to_redis()
```

---

# Slide 13: Memory Features

## Smart Memory Management

### Session Context

```python
# Stored context for each session
context = {
    "current_file": "uploads/NA18515_YRI_Male.csv",
    "current_patient_id": "NA18515",
    "current_gender": "Male",
    "current_population": "YRI",
    "last_analysis_time": "2025-02-04T10:30:00"
}
```

### Benefits
- 🔄 **Persistence**: Conversations survive restarts
- 📁 **File Tracking**: Remembers current file for follow-ups
- 👤 **User Context**: Stores analysis results
- ⏱️ **TTL**: Auto-expire after 24 hours

---

# Slide 14: LangSmith Integration

## Complete Observability

### What LangSmith Provides

| Feature | Description |
|---------|-------------|
| **Tracing** | Track every LLM call and tool execution |
| **Debugging** | See inputs/outputs at each step |
| **Latency** | Measure response times |
| **Cost** | Track token usage |
| **Evaluation** | Run test suites |

### Configuration

```python
# config.py
LANGSMITH_ENABLED = os.getenv("LANGCHAIN_TRACING_V2", "false")
LANGSMITH_API_KEY = os.getenv("LANGCHAIN_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGCHAIN_PROJECT", "dna-analysis-agent")
```

---

# Slide 15: LangSmith Tracing

## Trace Visualization

```
🔍 DNA Agent Run
├── 📥 User Input: "Analyze my DNA file"
├── 🤖 LLM Call (Gemini 2.0 Flash)
│   ├── Prompt: [System + History + User]
│   ├── Response: Tool call requested
│   └── Latency: 1.2s
├── 🔧 Tool: analyze_snp_file
│   ├── Input: {"sample_file": "uploads/sample.csv"}
│   ├── Output: {"gender": "Male", "population": "YRI"}
│   └── Latency: 3.5s
├── 🤖 LLM Call (Generate Response)
│   ├── Context: Tool results
│   └── Latency: 0.8s
└── 📤 Final Response: "Your analysis shows..."
    └── Total Time: 5.5s
```

---

# Slide 16: LangSmith Callbacks

## Custom Callback Handler

```python
class DNAAgentCallbackHandler(BaseCallbackHandler):
    """Custom callback for rich metadata tracking"""
    
    def __init__(self, session_id: str, user_id: Optional[str] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.tool_calls: List[Dict] = []
        self.llm_calls: int = 0
        self.total_tokens: int = 0
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        """Track LLM call start"""
        self.run_start_time = datetime.now()
        self.llm_calls += 1
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        """Track tool execution"""
        self.tool_calls.append({
            "name": serialized.get("name"),
            "start_time": datetime.now().isoformat()
        })
```

---

# Slide 17: LangSmith Tags

## Organized Tracing

```python
class TraceTags(str, Enum):
    """Standard tags for DNA Agent traces"""
    
    # Environment
    PRODUCTION = "env:production"
    STAGING = "env:staging"
    DEVELOPMENT = "env:development"
    
    # Features
    ANALYSIS = "feature:analysis"
    PREDICTION = "feature:prediction"
    IMAGE_GEN = "feature:image_generation"
    EDUCATION = "feature:education"
    
    # Tools
    TOOL_SNP = "tool:snp"
    TOOL_DISEASE = "tool:disease"
    TOOL_TRAITS = "tool:traits"
    
    # Quality
    HIGH_CONFIDENCE = "quality:high_confidence"
    NEEDS_REVIEW = "quality:needs_review"
```

---

# Slide 18: Evaluation Framework

## Testing with LangSmith

### Test Cases

```python
STANDARD_TEST_CASES = [
    TestCase(
        name="basic_analysis",
        user_input="Analyze the sample file uploads/NA20805_GIH_Male.csv",
        expected_elements=["GIH", "Male", "analysis"],
        expected_tools=["analyze_snp_file"],
        category="analysis"
    ),
    TestCase(
        name="disease_risk",
        user_input="What are the disease risks for a CEU Male?",
        expected_elements=["disease", "risk", "CEU"],
        expected_tools=["assess_genetic_disease_risk"],
        category="prediction"
    ),
    TestCase(
        name="population_info",
        user_input="Tell me about the YRI population",
        expected_elements=["Yoruba", "Nigeria"],
        expected_tools=["get_population_info"],
        category="education"
    ),
]
```

---

# Slide 19: Monitoring

## Production Metrics

### AgentMetrics Class

```python
@dataclass
class AgentMetrics:
    # Run counts
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate: float
    
    # Latency (milliseconds)
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    
    # Token usage
    total_tokens: int
    avg_tokens_per_run: float
    
    # Tool metrics
    total_tool_calls: int
    tool_success_rate: float
    top_tools: List[Dict]
    
    # Errors
    error_breakdown: Dict[str, int]
```

---

# Slide 20: System Prompt

## Agent Personality & Rules

```python
SYSTEM_PROMPT = """You are DNA Analysis Assistant, 
an expert AI agent specialized in genetic data analysis.

## Your Capabilities:
{tools_description}

## Your Knowledge:
- SNPs (Single Nucleotide Polymorphisms)
- Alleles and genotypes
- HapMap populations and genetics
- Disease risk interpretation

## Available Populations:
- ASW: African ancestry in Southwest USA
- CEU: Northern European ancestry
- CHB: Han Chinese in Beijing
- JPT: Japanese in Tokyo
- YRI: Yoruban in Nigeria
...

## Critical Rules:
1. ALWAYS use current session file for analysis
2. Answer from context before using tools
3. Include confidence levels with predictions
4. Format responses with markdown & emojis 🧬
"""
```

---

# Slide 21: Supported Populations

## HapMap Genetic Populations

| Code | Population | Description |
|------|------------|-------------|
| **ASW** | African SW USA | African ancestry in Southwest USA |
| **CEU** | European | Utah residents with N/W European ancestry |
| **CHB** | Chinese Beijing | Han Chinese in Beijing, China |
| **CHD** | Chinese Denver | Chinese in Denver, Colorado |
| **GIH** | Gujarati Indian | Gujarati Indians in Houston, Texas |
| **JPT** | Japanese | Japanese in Tokyo, Japan |
| **LWK** | Luhya Kenya | Luhya in Webuye, Kenya |
| **MEX** | Mexican | Mexican ancestry in Los Angeles |
| **MKK** | Maasai | Maasai in Kinyawa, Kenya |
| **TSI** | Italian | Tuscan in Italy |
| **YRI** | Yoruban | Yoruban in Ibadan, Nigeria |

---

# Slide 22: API Architecture

## Tool → API Communication

```python
# Base URL for API calls
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:5001")

def call_api(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Make API call to Flask backend"""
    url = f"{API_BASE_URL}{endpoint}"
    
    if method == "GET":
        response = requests.get(url, timeout=120)
    else:
        response = requests.post(url, json=data, timeout=120)
    
    return response.json()
```

### API Endpoints Called by Tools

| Endpoint | Tool |
|----------|------|
| `/api/process_snp_file` | `analyze_snp_file` |
| `/api/predictions/physical` | `predict_physical_characteristics` |
| `/api/predictions/disease-risk` | `assess_genetic_disease_risk` |
| `/api/predictions/generate-image` | `generate_person_image` |
| `/api/vep/analyze-file` | `analyze_snp_effects` |

---

# Slide 23: Running the Agent

## Usage Examples

### Simple Chat Interface

```python
from agent.workflow import get_workflow

# Get singleton workflow instance
workflow = get_workflow()

# Simple chat
response = workflow.chat(
    user_input="What is my genetic ancestry?",
    session_id="user_123"
)
print(response)
```

### Full Control

```python
result = workflow.run(
    user_input="Analyze uploads/sample.csv",
    session_id="session_abc",
    chat_history=[{"role": "user", "content": "Hello"}],
    user_id=42  # For personalization
)

print(result["response"])
print(f"Tools used: {result['tool_results']}")
print(f"Iterations: {result['iterations']}")
```

---

# Slide 24: Key Features Summary

## What Makes This Agent Special

### ✅ Intelligent Tool Selection
- LLM decides which tools to use
- Context-aware decision making
- Iterative reasoning (up to 10 iterations)

### ✅ Persistent Memory
- Redis-backed conversation history
- Session context (current file, results)
- 24-hour automatic expiry

### ✅ Full Observability
- LangSmith tracing
- Custom callbacks
- Production monitoring

### ✅ Rich Tool Ecosystem
- 25+ specialized genetic tools
- VEP integration for variant effects
- AI image generation

---

# Slide 25: Technology Stack

## Complete Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│                    Web Chat Interface                            │
└──────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────┐
│                          AGENT LAYER                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │   LangGraph    │  │    Gemini      │  │   LangSmith    │     │
│  │   (Workflow)   │  │   2.0 Flash    │  │  (Observability)│    │
│  └────────────────┘  └────────────────┘  └────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────┐
│                         BACKEND                                   │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │  Flask API     │  │   ML Models    │  │    Celery      │     │
│  │  (Endpoints)   │  │  (Predictions) │  │  (Async Tasks) │     │
│  └────────────────┘  └────────────────┘  └────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────┐
│                         DATA LAYER                                │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │   PostgreSQL   │  │    Redis       │  │    MongoDB     │     │
│  │   (Primary)    │  │   (Memory)     │  │   (Documents)  │     │
│  └────────────────┘  └────────────────┘  └────────────────┘     │
└──────────────────────────────────────────────────────────────────┘
```

---

# Slide 26: Future Enhancements

## Roadmap

### 🎯 Planned Features

1. **MCP Server (Model Context Protocol)**
   - Separate server for tool hosting
   - Cross-platform tool sharing
   - Standardized tool interface

2. **Multi-Agent System**
   - Specialist agents for different domains
   - Agent collaboration

3. **Enhanced Evaluation**
   - Automated regression testing
   - A/B testing for prompts

4. **Advanced Memory**
   - Long-term user memory
   - Cross-session learning

---

# Slide 27: Conclusion

## What We Achieved

### 🏆 Complete AI Agent Implementation

| Aspect | Implementation |
|--------|----------------|
| **Framework** | LangGraph state machine |
| **LLM** | Google Gemini 2.0 Flash |
| **Tools** | 25+ specialized tools |
| **Memory** | Redis-backed persistence |
| **Observability** | Full LangSmith integration |
| **Testing** | Comprehensive test suite |
| **Monitoring** | Production-ready metrics |

### 📊 Key Metrics
- 25+ specialized genetic analysis tools
- Support for 11 HapMap populations
- Complete tracing with LangSmith
- Redis-backed conversation memory

---

