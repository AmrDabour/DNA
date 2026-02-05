# DNA Analysis AI Agent
## Building an Intelligent Genetic Analysis Assistant

---

<!-- 
PRESENTATION STYLE GUIDE
========================
Background: Warm beige/cream paper texture (aged blueprint look)
Borders: Hand-drawn frames with slightly irregular edges
Typography: Clean modern fonts, hand-written feel for headings

COLOR CODING:
- Blue (#4A90D9): Workflow & Pipelines
- Green (#5CB85C): Security & Validation  
- Orange (#F0AD4E): Warnings & Important Notes
- Purple (#9B59B6): Infrastructure & Deployment
-->

---

# Slide 1: Overview

## What is the AI Agent?

An intelligent conversational assistant that uses **LangGraph** workflow to analyze DNA data and respond to user questions.

### Technology Stack

| Component | Technology | Color |
|-----------|------------|-------|
| Workflow Engine | LangGraph | Blue |
| AI Model | Google Gemini 3.0 Flash | Purple |
| Observability | LangSmith | Green |
| Memory | Redis | Purple |

### How It Works

```
User Question → Agent Analyzes → Calls Tools → Returns Response
```

---

# Slide 2: LangGraph Workflow [Blue]

## State Machine Architecture

The agent uses a **4-node workflow** that processes each request:

```
USER INPUT
    │
    ▼
ANALYZE INTENT (LLM)                    [Purple - AI Model]
    │
    ├── No tools needed ──► RESPOND ──► OUTPUT
    │
    ▼
EXECUTE TOOLS                           [Blue - Pipeline]
    │
    ├── Success ──► RESPOND ──► OUTPUT  [Green - Validated]
    │
    ▼
ERROR? ──► RETRY (max 5) ──► Circuit Breaker   [Orange - Warning]
    │
    ▼
GIVE UP ──► ERROR RESPONSE ──► OUTPUT
```

### Key Features

| Feature | Description | Status |
|---------|-------------|--------|
| Conditional Routing | Agent decides which path | Green |
| Iterative Processing | Up to 10 iterations | Blue |
| Error Handling | Graceful error messages | Orange |

---

# Slide 3: Gemini 3.0 Flash [Purple]

## The AI Model

| Setting | Value |
|---------|-------|
| Model | gemini-3.0-flash |
| Temperature | 0.7 |
| Max Tokens | 2048 |

### Tool Binding

The model automatically decides which tools to call based on user input:

```
User: "Analyze my DNA file"
  ↓
Model decides: Call analyze_snp_file tool    [Purple - AI Decision]
  ↓
Tool returns results                          [Blue - Pipeline]
  ↓
Model generates response                      [Green - Success]
```

---

# Slide 4: Tools (25+) [Blue]

## Agent Toolkit

The agent has access to 25+ specialized tools:

| Category | Tools |
|----------|-------|
| Sample Management | list_samples, get_sample_info, compare_samples |
| Analysis | analyze_snp_file, query_snp, get_statistics |
| Predictions | predict_traits, disease_risk, full_report |
| Image Generation | generate_portrait, generate_from_sample |
| VEP Analysis | analyze_effects, get_pathogenicity |

### Tool Flow

```
Agent ──► Tool ──► Flask API ──► Returns Result ──► Agent Responds
[Purple]  [Blue]   [Purple]      [Green]           [Green]
```

---

# Slide 5: LangSmith [Green]

## Observability & Monitoring

| Feature | Purpose |
|---------|---------|
| Tracing | Track every LLM call and tool execution |
| Latency | Measure response times |
| Token Usage | Monitor costs |
| Tags | Organize traces by feature |
| Evaluation | Run test cases |

### Trace Example

```
User Query: "Analyze my DNA"
  ├── LLM Call (1.2s)           [Purple]
  ├── Tool: analyze_snp_file    [Blue]
  ├── Latency: 3.5s             [Orange - Monitor]
  └── Total: 5.5s | Tokens: 1,247   [Green - Complete]
```

---

# Slide 6: Memory System [Purple]

## Conversation Persistence

### Architecture

```
┌─────────────────────────────────────────────┐
│              MEMORY SYSTEM                   │
│                                              │
│   IN-MEMORY  ◄────────►  REDIS              │
│   (Fast)         Sync    (Persistent)       │
│   [Blue]                 [Purple]           │
│                                              │
└─────────────────────────────────────────────┘
```

### What Gets Stored

| Data | Purpose |
|------|---------|
| Current File | Remember active sample file |
| Analysis Results | Store gender, ancestry |
| Chat History | Last 20 messages |

### Features

- Automatic sync to Redis [Blue - Pipeline]
- 24-hour TTL auto-expire [Orange - Important]
- Session-based isolation [Green - Security]

---

# Summary

## Complete AI Agent Implementation

| Component | Technology | Color Theme |
|-----------|------------|-------------|
| Workflow | LangGraph (4 nodes) | Blue |
| Model | Gemini 3.0 Flash | Purple |
| Tools | 25+ custom tools | Blue |
| Observability | LangSmith | Green |
| Memory | Redis + In-Memory | Purple |

---

*Built with LangGraph, Gemini 3.0 Flash, and LangSmith*

<!-- 
VISUAL NOTES FOR DESIGNER:
- Use hand-drawn style borders
- Aged paper texture background (cream/beige)
- Color code sections as marked
- Friendly icons for each component
-->

---

*Built with LangGraph, Gemini 3.0 Flash, and LangSmith*
