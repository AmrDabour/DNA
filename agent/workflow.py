"""
LangGraph Workflow - DNA Agent Workflow Definition
"""
from typing import TypedDict, Dict, Any, List, Optional, Annotated
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import json
import operator

from .config import config
from .tools import get_all_tools, get_tools_description, POPULATION_INFO
from .memory import ChatMemory, get_memory


# ============================================================
# State Definition
# ============================================================

class AgentState(TypedDict):
    """State for the DNA Agent workflow"""
    
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
    
    # Context data
    context: Dict[str, Any]
    
    # Output
    response: str
    error: str
    
    # User context for personalization
    user_id: int  # Authenticated user ID (0 for guests)


# ============================================================
# System Prompt
# ============================================================

SYSTEM_PROMPT = """You are DNA Analysis Assistant, an expert AI agent specialized in genetic data analysis and predictions.

{user_context}

{current_file_context}

## Your Capabilities:
{tools_description}

## Your Knowledge:
- You understand genetic concepts like SNPs (Single Nucleotide Polymorphisms), alleles, genotypes
- You know about the HapMap populations and their genetic characteristics
- You can explain genetic predictions and their significance
- You understand that genetic predictions are statistical and not absolute

## Available Populations:
{populations}

## CRITICAL RULES:

### 1. ALWAYS Know Your User:
- If user asks "what is my name?" → Answer from the "Current User" section above
- If user asks about their gender or ancestry and you have it in the user context → Tell them directly
- Example: "What is my name?" → "Your name is [name from Current User section]"

### 2. File Selection Rules:
- **ALWAYS use the CURRENT SESSION FILE** shown above when user asks about their data
- If no current file, check chat history for previously mentioned files
- NEVER ask user to upload a file if one is already in the session

### 3. Tool Selection for Questions:
| User Question | When to Answer Directly | When to Use Tool |
|--------------|------------------------|------------------|
| "What is my gender?" | Gender shown in ANALYSIS RESULTS above | No gender in context → use `full_genetic_report` |
| "What is my ancestry?" | Ancestry shown in ANALYSIS RESULTS above | No ancestry in context → use `full_genetic_report` |
| "Predict my traits" | Never - always need fresh prediction | `get_physical_traits_from_sample` |
| "Disease risk?" | Never - always need fresh prediction | `get_disease_risk_from_sample` |
| "Generate my image" | Never - always need to generate | `generate_image_from_sample` (auto-analyzes if needed!) |

### 4. Image Generation - Smart Tool:
**IMPORTANT:** `generate_image_from_sample` is a SMART tool that:
- Automatically analyzes the file if gender/population are not provided
- You can call it DIRECTLY even without prior analysis
- Example: User asks "give me image" → Just call `generate_image_from_sample(sample_file="uploads/file.csv")`
- The tool handles everything: analysis + image generation in ONE call

### 5. IMPORTANT - When NOT to Use Tools:
- **DO NOT call tools if you already have the answer in your context!**
- If ANALYSIS RESULTS shows gender = "Male", just say "Based on your genetic analysis, you are Male"
- If ANALYSIS RESULTS shows ancestry = "CHD", just say "Your predicted ancestry is CHD (Chinese in Denver)"
- Only use tools when you need NEW information

### 6. Context Awareness:
- **Remember the file path**: When user mentions a file, remember it for follow-up questions
- **Use the same file**: If user asks "what is my gender" after analyzing a file, use that SAME file path
- **Don't ask for info you have**: If user's gender/ancestry is in the context, use it directly

## Guidelines:
1. **Use tools proactively**: When asked about genetic info, CALL THE TOOL - don't say you can't determine it
2. **Be accurate**: Only provide information from actual tool results OR from user context
3. **Be cautious**: Genetic predictions are probabilistic, always mention this
4. **Format nicely**: Use markdown for better readability
5. **Be educational**: Help users learn about genetics

## Response Format:
- Use clear, concise language
- Use bullet points and headers
- Include statistics from tool results
- Use emojis to make responses engaging 🧬
"""


# ============================================================
# DNA Agent Workflow
# ============================================================

class DNAAgentWorkflow:
    """LangGraph workflow for DNA Analysis Agent"""
    
    def __init__(self):
        self.llm = self._init_llm()
        self.tools = get_all_tools()
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        self.graph = self._build_graph()
        self._tracer = None
        self._init_tracing()
    
    def _init_tracing(self):
        """Initialize LangSmith tracing if available"""
        try:
            from .langsmith_utils import get_tracer, is_langsmith_available
            if is_langsmith_available():
                self._tracer = get_tracer()
        except ImportError:
            pass
    
    def _init_llm(self) -> ChatGoogleGenerativeAI:
        """Initialize the LLM with optional LangSmith tracing"""
        callbacks = []
        
        # Add LangSmith tracer if available
        try:
            from .langsmith_utils import get_tracer, is_langsmith_available
            if is_langsmith_available():
                tracer = get_tracer()
                if tracer:
                    callbacks.append(tracer)
        except ImportError:
            pass
        
        return ChatGoogleGenerativeAI(
            model=config.MODEL_NAME,
            google_api_key=config.get_api_key(),
            temperature=config.TEMPERATURE,
            max_output_tokens=config.MAX_TOKENS,
            callbacks=callbacks if callbacks else None
        )
    
    def _get_system_prompt(self, user_id: int = None, session_id: str = None) -> str:
        """Generate the system prompt with current context and user memory"""
        populations_list = []
        for code, info in POPULATION_INFO.items():
            populations_list.append(f"- **{code}** ({info['code']}): {info['description']}")
        
        # Get current file context from session memory
        current_file_context = ""
        if session_id:
            try:
                memory = get_memory(session_id)
                current_file = memory.get_context("current_file")
                current_patient_id = memory.get_context("current_patient_id")
                last_analysis_time = memory.get_context("last_analysis_time")
                
                if current_file:
                    # Also get stored gender/population from analysis
                    current_gender = memory.get_context("current_gender")
                    current_population = memory.get_context("current_population")
                    
                    current_file_context = f"""## ⚠️ CURRENT SESSION FILE (USE THIS FILE PATH):
- **Current File:** `{current_file}`
- **Patient ID:** {current_patient_id or 'Unknown'}
- **Last Analyzed:** {last_analysis_time or 'N/A'}"""
                    
                    # Add analysis results if available
                    if current_gender or current_population:
                        current_file_context += "\n\n### 🧬 ANALYSIS RESULTS FROM THIS FILE:"
                        if current_gender:
                            current_file_context += f"\n- **Predicted Gender:** {current_gender}"
                        if current_population:
                            current_file_context += f"\n- **Predicted Ancestry/Population:** {current_population}"
                        current_file_context += "\n\n**⚠️ CRITICAL:** If user asks 'what is my gender?', answer with the gender above!"
                        current_file_context += "\n**⚠️ CRITICAL:** If user asks about ancestry, answer with the population above!"
                    
                    current_file_context += f"""\n
**IMPORTANT:** When user asks about gender, ancestry, traits, or diseases without specifying a file, 
use THIS file path: `{current_file}`
"""
                    print(f"📁 Current file context: {current_file}, gender: {current_gender}, population: {current_population}")
            except Exception as e:
                print(f"⚠️ Failed to get file context: {e}")
        
        # Get user-specific context if authenticated
        user_context = ""
        if user_id and user_id > 0:
            try:
                from services.user_memory_service import get_user_memory_prompt
                user_context = get_user_memory_prompt(user_id)
                if user_context:
                    print(f"🧠 Memory prompt loaded for user {user_id}: {len(user_context)} chars")
                else:
                    print(f"⚠️ No memory found for user {user_id}")
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to load user memory: {e}")
                print(f"❌ Failed to load user memory: {e}")
        
        return SYSTEM_PROMPT.format(
            tools_description=get_tools_description(),
            populations="\n".join(populations_list),
            current_file_context=current_file_context,
            user_context=user_context
        )
    
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
        
        # Add conditional edges from analyze_intent
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
        
        # Add conditional edges from use_tools
        workflow.add_conditional_edges(
            "use_tools",
            self._route_after_tools,
            {
                "analyze": "analyze_intent",
                "respond": "generate_response",
                "error": "handle_error"
            }
        )
        
        # Direct edges
        workflow.add_edge("generate_response", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    # ============================================================
    # Node Functions
    # ============================================================
    
    def _analyze_intent_node(self, state: AgentState) -> Dict[str, Any]:
        """Analyze user intent and decide what to do"""
        try:
            user_input = state["user_input"]
            chat_history = state.get("chat_history", [])
            user_id = state.get("user_id", 0)
            session_id = state.get("session_id", "")
            
            # Build messages for LLM (with user memory and file context)
            messages = [
                SystemMessage(content=self._get_system_prompt(user_id=user_id, session_id=session_id)),
            ]
            
            # Add chat history
            for msg in chat_history[-10:]:  # Last 10 messages for context
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
            
            # Add current user input
            messages.append(HumanMessage(content=user_input))
            
            # Get LLM response with tool binding
            llm_with_tools = self.llm.bind_tools(self.tools)
            response = llm_with_tools.invoke(messages)
            
            # Check for tool calls
            tool_calls = []
            if hasattr(response, 'tool_calls') and response.tool_calls:
                for tc in response.tool_calls:
                    tool_calls.append({
                        "name": tc["name"],
                        "args": tc["args"],
                        "id": tc.get("id", "")
                    })
            
            # Extract text content (handle both string and list formats)
            response_content = self._extract_text_content(response.content) if not tool_calls else ""
            
            return {
                "stage": "thinking" if tool_calls else "responding",
                "tool_calls": tool_calls,
                "response": response_content,
                "iteration": state.get("iteration", 0) + 1
            }
            
        except Exception as e:
            return {
                "stage": "error",
                "error": str(e)
            }
    
    def _extract_text_content(self, content) -> str:
        """Extract text from response content (handles both string and list formats from Gemini)"""
        print(f"🔍 _extract_text_content called with type: {type(content)}, value: {str(content)[:200]}")
        
        if content is None:
            return ""
        
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            if not content:  # Empty list
                print("⚠️ Empty list received from LLM")
                return ""
            
            # New Gemini format: list of dicts with 'type' and 'text' keys
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    # Check for 'text' key (common format)
                    if 'text' in item:
                        text_parts.append(item.get('text', ''))
                    # Also check for 'content' key
                    elif 'content' in item:
                        text_parts.append(item.get('content', ''))
                elif isinstance(item, str):
                    text_parts.append(item)
            result = '\n'.join(text_parts)
            print(f"📝 Extracted text (first 100): {result[:100]}")
            return result
        else:
            return str(content)
    
    def _use_tools_node(self, state: AgentState) -> Dict[str, Any]:
        """Execute the tools requested by the LLM"""
        tool_calls = state.get("tool_calls", [])
        tool_results = []
        
        for tc in tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]
            
            if tool_name in self.tools_by_name:
                try:
                    tool = self.tools_by_name[tool_name]
                    result = tool.invoke(tool_args)
                    tool_results.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": result,
                        "success": True
                    })
                except Exception as e:
                    tool_results.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "error": str(e),
                        "success": False
                    })
            else:
                tool_results.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "error": f"Tool not found: {tool_name}",
                    "success": False
                })
        
        return {
            "tool_results": tool_results,
            "stage": "tool_use"
        }
    
    def _generate_response_node(self, state: AgentState) -> Dict[str, Any]:
        """Generate the final response to the user"""
        try:
            user_input = state["user_input"]
            chat_history = state.get("chat_history", [])
            tool_results = state.get("tool_results", [])
            
            # Check if any tool returned a formatted_result (pre-formatted output)
            formatted_outputs = []
            for tr in tool_results:
                if tr.get("success") and isinstance(tr.get("result"), dict):
                    result = tr["result"]
                    if result.get("formatted_result"):
                        formatted_outputs.append(result["formatted_result"])
            
            # If we have pre-formatted results, return them directly
            if formatted_outputs:
                combined_output = "\n\n".join(formatted_outputs)
                return {
                    "response": combined_output,
                    "stage": "complete"
                }
            
            # Build messages - IMPORTANT: include user_id and session_id for personalization
            user_id = state.get("user_id", 0)
            session_id = state.get("session_id", "")
            messages = [
                SystemMessage(content=self._get_system_prompt(user_id=user_id, session_id=session_id)),
            ]
            
            # Add chat history
            for msg in chat_history[-10:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
            
            # Add current user input
            messages.append(HumanMessage(content=user_input))
            
            # If we have tool results, add them to context
            if tool_results:
                tool_context = "I used the following tools to get this information:\n\n"
                for tr in tool_results:
                    if tr.get("success"):
                        result_data = tr['result']
                        # Remove raw_data and formatted_result for cleaner context
                        if isinstance(result_data, dict):
                            clean_result = {k: v for k, v in result_data.items() 
                                          if k not in ['raw_data', 'formatted_result']}
                            tool_context += f"**{tr['tool']}**: {json.dumps(clean_result, indent=2, default=str)}\n\n"
                        else:
                            tool_context += f"**{tr['tool']}**: {json.dumps(result_data, indent=2, default=str)}\n\n"
                    else:
                        tool_context += f"**{tr['tool']}**: Error - {tr.get('error', 'Unknown error')}\n\n"
                
                messages.append(AIMessage(content=tool_context))
                messages.append(HumanMessage(content="Based on the tool results above, please provide a clear, well-formatted response in markdown to my original question. Use headers, bullet points, and emojis for better readability."))
            
            # Generate response
            print(f"🤖 Generating response with {len(messages)} messages...")
            response = self.llm.invoke(messages)
            print(f"🤖 Raw response content type: {type(response.content)}, content: {str(response.content)[:200]}")
            
            extracted_response = self._extract_text_content(response.content)
            
            # If response is empty, provide a fallback
            if not extracted_response or not extracted_response.strip():
                print("⚠️ Empty response from LLM, using tool results directly")
                # Try to format tool results as the response
                if tool_results:
                    fallback_parts = ["Based on my analysis:\n"]
                    for tr in tool_results:
                        if tr.get("success") and tr.get("result"):
                            result = tr.get("result", {})
                            if isinstance(result, dict):
                                if result.get("error"):
                                    fallback_parts.append(f"⚠️ {tr['tool']}: {result.get('error')}")
                                else:
                                    # Extract key info from result
                                    for key in ['message', 'description', 'summary', 'content']:
                                        if result.get(key):
                                            fallback_parts.append(f"• {result.get(key)}")
                                            break
                                    else:
                                        fallback_parts.append(f"• Tool {tr['tool']} completed successfully")
                    extracted_response = "\n".join(fallback_parts)
                else:
                    extracted_response = "I processed your request but couldn't generate a detailed response. Please try again."
            
            return {
                "response": extracted_response,
                "stage": "complete"
            }
            
        except Exception as e:
            print(f"❌ Error in _generate_response_node: {e}")
            import traceback
            traceback.print_exc()
            return {
                "stage": "error",
                "error": str(e)
            }
    
    def _handle_error_node(self, state: AgentState) -> Dict[str, Any]:
        """Handle errors gracefully"""
        error = state.get("error", "An unknown error occurred")
        
        return {
            "response": f"I apologize, but I encountered an error: {error}\n\nPlease try again or rephrase your question.",
            "stage": "complete"
        }
    
    # ============================================================
    # Routing Functions
    # ============================================================
    
    def _route_after_analysis(self, state: AgentState) -> str:
        """Decide what to do after analyzing user intent"""
        stage = state.get("stage", "")
        iteration = state.get("iteration", 0)
        max_iterations = state.get("max_iterations", config.MAX_ITERATIONS)
        
        if stage == "error":
            return "error"
        
        if iteration >= max_iterations:
            return "respond"
        
        if state.get("tool_calls"):
            return "use_tools"
        
        if state.get("response"):
            return "respond"
        
        return "respond"
    
    def _route_after_tools(self, state: AgentState) -> str:
        """Decide what to do after tool execution"""
        iteration = state.get("iteration", 0)
        max_iterations = state.get("max_iterations", config.MAX_ITERATIONS)
        
        if state.get("error"):
            return "error"
        
        if iteration >= max_iterations:
            return "respond"
        
        # After tools, generate response
        return "respond"
    
    # ============================================================
    # Public Methods
    # ============================================================
    
    def run(self, 
            user_input: str, 
            session_id: str, 
            chat_history: List[Dict[str, str]] = None,
            user_id: int = 0) -> Dict[str, Any]:
        """
        Run the agent workflow
        
        Args:
            user_input: The user's message
            session_id: Session identifier for memory
            chat_history: Previous conversation messages
            user_id: Authenticated user ID (0 for guests, no memory)
            
        Returns:
            dict: Contains response and other metadata
        """
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
            "context": {},
            "response": "",
            "error": "",
            "user_id": user_id
        }
        
        # Run the graph with LangSmith tracing
        try:
            # Build config with callbacks for tracing
            run_config = {}
            if self._tracer:
                run_config["callbacks"] = [self._tracer]
                run_config["metadata"] = {
                    "session_id": session_id,
                    "input_length": len(user_input),
                    "history_length": len(chat_history) if chat_history else 0
                }
                run_config["tags"] = ["dna-agent", "chat"]
            
            result = self.graph.invoke(
                initial_state,
                config=run_config if run_config else None
            )
            
            return {
                "success": True,
                "response": result.get("response", ""),
                "stage": result.get("stage", "complete"),
                "tool_results": result.get("tool_results", []),
                "iterations": result.get("iteration", 0)
            }
        except Exception as e:
            return {
                "success": False,
                "response": f"An error occurred: {str(e)}",
                "error": str(e)
            }
    
    def chat(self, 
             user_input: str, 
             session_id: str) -> str:
        """
        Simple chat interface that manages memory automatically
        
        Args:
            user_input: The user's message
            session_id: Session identifier for memory
            
        Returns:
            str: The agent's response
        """
        # Get memory for this session
        memory = get_memory(session_id)
        
        # Add user message to memory
        memory.add_user_message(user_input)
        
        # Get chat history
        chat_history = memory.get_messages_for_llm()
        
        # Run the workflow
        result = self.run(user_input, session_id, chat_history)
        
        # Add assistant response to memory
        response = result.get("response", "I apologize, but I couldn't generate a response.")
        memory.add_assistant_message(response)
        
        return response


# ============================================================
# Singleton Instance
# ============================================================

_workflow_instance: Optional[DNAAgentWorkflow] = None


def get_workflow() -> DNAAgentWorkflow:
    """Get the singleton workflow instance"""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = DNAAgentWorkflow()
    return _workflow_instance


def reset_workflow() -> None:
    """Reset the workflow instance"""
    global _workflow_instance
    _workflow_instance = None

