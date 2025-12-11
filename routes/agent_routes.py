"""
Agent Routes - API endpoints for AI Agent chat
"""
from flask import jsonify, request
import os
import pandas as pd
from werkzeug.utils import secure_filename
from . import agent_bp

# Agent availability flag
AGENT_AVAILABLE = False

try:
    from agent import get_workflow, get_memory, clear_memory
    AGENT_AVAILABLE = True
except ImportError:
    pass


UPLOAD_FOLDER = "uploads"


@agent_bp.route('/chat', methods=['POST'])
def chat():
    """
    Chat with the DNA Agent
    ---
    tags:
      - Agent
    """
    if not AGENT_AVAILABLE:
        return jsonify({
            "success": False,
            "error": "AI Agent is not available. Please install langchain and langgraph."
        })
    
    try:
        data = request.json
        message = data.get("message", "").strip()
        session_id = data.get("session_id", "default")
        
        if not message:
            return jsonify({"success": False, "error": "Message cannot be empty"})
        
        workflow = get_workflow()
        memory = get_memory(session_id)
        chat_history = memory.get_messages_for_llm()
        
        memory.add_user_message(message)
        
        # Run agent workflow
        result = workflow.run(message, session_id, chat_history)
        
        response_text = result.get("response", "I apologize, I couldn't generate a response.")
        memory.add_assistant_message(response_text)
        
        tools_used = []
        if result.get("tool_results"):
            tools_used = [tr.get("tool", "") for tr in result["tool_results"] if tr.get("success")]
        
        return jsonify({
            "success": True,
            "response": response_text,
            "tools_used": tools_used,
            "iterations": result.get("iterations", 1)
        })
        
    except Exception as e:
        import traceback
        return jsonify({"success": False, "error": str(e)})


@agent_bp.route('/history', methods=['GET'])
def get_history():
    """
    Get chat history for a session
    ---
    tags:
      - Agent
    """
    if not AGENT_AVAILABLE:
        return jsonify({"success": False, "error": "Agent not available"})
    
    try:
        session_id = request.args.get("session_id", "default")
        memory = get_memory(session_id)
        
        return jsonify({
            "success": True,
            "messages": memory.get_history(),
            "session_id": session_id
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@agent_bp.route('/clear', methods=['POST'])
def clear_chat():
    """
    Clear chat history for a session
    ---
    tags:
      - Agent
    """
    if not AGENT_AVAILABLE:
        return jsonify({"success": False, "error": "Agent not available"})
    
    try:
        data = request.json
        session_id = data.get("session_id", "default")
        clear_memory(session_id)
        
        return jsonify({"success": True, "message": "Chat history cleared"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@agent_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload SNP file for agent analysis
    ---
    tags:
      - Agent
    """
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No file provided"})
        
        file = request.files["file"]
        
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"})
        
        if not file.filename.endswith(".csv"):
            return jsonify({"success": False, "error": "Only CSV files are supported"})
        
        filename = secure_filename(file.filename)
        
        # Create upload folder if needed
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        try:
            # Read CSV to get info
            df = pd.read_csv(file_path)
            columns = df.columns.tolist()
            row_count = len(df)
            
            return jsonify({
                "success": True,
                "file_path": file_path,
                "filename": filename,
                "columns": columns,
                "row_count": row_count,
                "message": f"File uploaded successfully! {row_count} SNPs found."
            })
        except Exception as e:
            return jsonify({
                "success": True,
                "file_path": file_path,
                "filename": filename,
                "warning": f"File uploaded but couldn't read preview: {str(e)}"
            })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@agent_bp.route('/status', methods=['GET'])
def get_status():
    """
    Get agent status and capabilities
    ---
    tags:
      - Agent
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY")
    
    status = {
        "available": AGENT_AVAILABLE,
        "gemini_configured": bool(api_key)
    }
    
    if AGENT_AVAILABLE:
        try:
            from agent.tools import get_all_tools
            tools = get_all_tools()
            status["tools"] = [
                {"name": t.name, "description": t.description.split('.')[0]}
                for t in tools
            ]
            status["tool_count"] = len(tools)
        except Exception as e:
            status["tools_error"] = str(e)
    
    return jsonify(status)

