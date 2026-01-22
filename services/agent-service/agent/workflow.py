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


# ============================================================
# System Prompt
# ============================================================

SYSTEM_PROMPT = """You are DNA Analysis Assistant, an expert AI agent specialized in genetic data analysis and predictions.

## Your Capabilities:
{tools_description}

## Your Knowledge:
- You understand genetic concepts like SNPs (Single Nucleotide Polymorphisms), alleles, genotypes
- You know about the HapMap populations and their genetic characteristics
- You can explain genetic predictions and their significance
- You understand that genetic predictions are statistical and not absolute

## Available Populations:
{populations}

## IMPORTANT - Context Awareness:
- **Remember previous analyses**: When a user asks for disease risk or physical characteristics after analyzing a sample, USE THE SAMPLE FILE PATH from the conversation.
- **Use sample-based tools**: If the user previously uploaded/analyzed a file like "uploads/NA20805_GIH_Male.csv", use `get_disease_risk_from_sample` or `get_physical_traits_from_sample` with that file path.
- **Don't ask for info you already have**: If you analyzed a sample showing "GIH Male", don't ask for gender and population again - use the sample file directly.
- **For complete reports**: Use `full_genetic_report` to get analysis + physical traits + disease risks all at once.

## Tool Selection Guide:

### 📊 Analysis Tools:
- User uploads file → use `analyze_snp_file`
- User asks for disease risk after analysis → use `get_disease_risk_from_sample` with the file path
- User asks for physical traits after analysis → use `get_physical_traits_from_sample` with the file path  
- User wants everything → use `full_genetic_report`
- User provides gender + population directly → use `assess_genetic_disease_risk` or `predict_physical_characteristics`

### 🖼️ Image Generation Tools:
- User asks "what do I look like" or "generate image" → use `generate_image_from_sample` with the sample file
- User wants portrait from gender/population → use `generate_person_image`

### 🎓 Educational & Fun Tools:
- User asks about a specific SNP → use `explain_snp_significance`
- User wants fun facts about genetics → use `get_genetic_fun_facts` (topics: general, ancestry, health, traits, evolution)
- User wants ancestry history → use `get_ancestry_deep_dive`
- User wants to compare two samples → use `calculate_genetic_relatedness`
- User asks what traits can be predicted → use `get_trait_predictions_guide`
- User wants a quick summary → use `generate_genetic_summary_card`

## Guidelines:
1. **Be helpful and informative**: Explain genetic concepts clearly when asked
2. **Use tools when needed**: If user asks about specific data, use the appropriate tool
3. **Be accurate**: Only provide information from actual data, don't make up results
4. **Be cautious**: Genetic predictions are probabilistic, always mention this
5. **Respect privacy**: Genetic data is sensitive, treat it appropriately
6. **Format nicely**: Use markdown for better readability
7. **Be fun**: Use emojis and engaging language when appropriate
8. **Be educational**: Help users learn about genetics in an accessible way

## Response Format:
- Use clear, concise language
- Use bullet points for lists
- Use headers for organization when appropriate
- Include relevant statistics when available
- Always explain what the results mean
- Use emojis to make responses more engaging 🧬

Remember: You're here to help users understand genetic data and make predictions. Be friendly, accurate, educational, and FUN!
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
    
    def _init_llm(self) -> ChatGoogleGenerativeAI:
        """Initialize the LLM"""
        return ChatGoogleGenerativeAI(
            model=config.MODEL_NAME,
            google_api_key=config.get_api_key(),
            temperature=config.TEMPERATURE,
            max_output_tokens=config.MAX_TOKENS
        )
    
    def _get_system_prompt(self) -> str:
        """Generate the system prompt with current context"""
        populations_list = []
        for code, info in POPULATION_INFO.items():
            populations_list.append(f"- **{code}** ({info['code']}): {info['description']}")
        
        return SYSTEM_PROMPT.format(
            tools_description=get_tools_description(),
            populations="\n".join(populations_list)
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
            
            # Build messages for LLM
            messages = [
                SystemMessage(content=self._get_system_prompt()),
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
            
            return {
                "stage": "thinking" if tool_calls else "responding",
                "tool_calls": tool_calls,
                "response": response.content if not tool_calls else "",
                "iteration": state.get("iteration", 0) + 1
            }
            
        except Exception as e:
            return {
                "stage": "error",
                "error": str(e)
            }
    
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
            
            # Build messages
            messages = [
                SystemMessage(content=self._get_system_prompt()),
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
            response = self.llm.invoke(messages)
            
            return {
                "response": response.content,
                "stage": "complete"
            }
            
        except Exception as e:
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
            chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Run the agent workflow
        
        Args:
            user_input: The user's message
            session_id: Session identifier for memory
            chat_history: Previous conversation messages
            
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
            "error": ""
        }
        
        # Run the graph
        try:
            result = self.graph.invoke(initial_state)
            
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

