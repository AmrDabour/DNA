"""
Agent Routes - API endpoints for AI Agent chat
"""
from flask import jsonify, request
from flask_login import current_user
import os
import pandas as pd
from datetime import datetime
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


def _extract_and_store_file_context(tool_results, memory):
    """
    Extract file context from tool results and store in session memory.
    This helps the agent remember which file is being analyzed across messages.
    """
    for tr in tool_results:
        if not tr.get("success"):
            continue
            
        result = tr.get("result", {})
        if not isinstance(result, dict):
            continue
        
        # Extract file path from tool arguments or result
        tool_args = tr.get("args", {})
        file_path = tool_args.get("sample_file") or result.get("file_path") or result.get("sample_file")
        
        if file_path:
            # Store file context in session memory
            memory.set_context("current_file", file_path)
            print(f"📁 Stored current file in session: {file_path}")
            
            # Try to extract patient ID
            patient_id = result.get("patient_id") or result.get("sample_id")
            if patient_id:
                memory.set_context("current_patient_id", patient_id)
            
            # Store analysis timestamp
            memory.set_context("last_analysis_time", datetime.now().isoformat())
            
            # Store gender and population if available (check multiple possible keys)
            gender = result.get("gender") or result.get("predicted_gender") or result.get("gender_prediction")
            if gender:
                memory.set_context("current_gender", gender)
                print(f"🧬 Stored gender in session: {gender}")
            
            population = result.get("population") or result.get("predicted_population") or result.get("ancestry_prediction") or result.get("ancestry")
            if population:
                memory.set_context("current_population", population)
                print(f"🌍 Stored population in session: {population}")
            
            # Also check for nested results (from ML prediction)
            if result.get("results"):
                nested = result.get("results", {})
                if nested.get("gender") and not gender:
                    memory.set_context("current_gender", nested.get("gender"))
                    print(f"🧬 Stored gender from nested results: {nested.get('gender')}")
                if nested.get("population") and not population:
                    memory.set_context("current_population", nested.get("population"))
                    print(f"🌍 Stored population from nested results: {nested.get('population')}")
            
            break  # Only store first file context found


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
        
        # Link session to authenticated user for persistent memory
        # Guests use anonymous sessions (no long-term memory)
        user_id = 0
        try:
            if current_user and current_user.is_authenticated:
                user_id = current_user.id
                session_id = f"user_{user_id}"
                print(f"🧠 Authenticated user {user_id} ({current_user.username})")
                
                # Ensure long-term memory exists for this user (initialize if needed)
                try:
                    from services.user_memory_service import get_user_memory_service
                    mem_service = get_user_memory_service()
                    existing_memory = mem_service.get_user_memory(user_id)
                    if not existing_memory:
                        # Initialize memory with user's basic info
                        mem_service.build_memory_from_analyses(user_id)
                        print(f"🧠 Initialized long-term memory for user {user_id}")
                except Exception as mem_init_err:
                    print(f"⚠️ Memory init warning: {mem_init_err}")
            else:
                session_id = data.get("session_id", "default")
                print(f"👤 Guest user, session: {session_id}")
        except Exception as auth_err:
            print(f"⚠️ Auth check error: {auth_err}")
            session_id = data.get("session_id", "default")
        
        if not message:
            return jsonify({"success": False, "error": "Message cannot be empty"})
        
        workflow = get_workflow()
        memory = get_memory(session_id)
        chat_history = memory.get_messages_for_llm()
        
        memory.add_user_message(message)
        
        # Run agent workflow with user_id for personalized memory injection
        import time as _time
        _agent_start = _time.time()
        print(f"🚀 Running agent workflow for message: {message[:50]}...")
        result = workflow.run(message, session_id, chat_history, user_id=user_id)
        _agent_duration = _time.time() - _agent_start
        print(f"📤 Agent result: success={result.get('success')}, has_response={bool(result.get('response'))}")
        
        # Track agent conversation metrics
        try:
            from utils.metrics import metrics_collector
            metrics_collector.track_agent_conversation(duration=_agent_duration, success=result.get('success', False))
        except ImportError:
            pass
        
        if not result.get("success"):
            print(f"❌ Agent error: {result.get('error')}")
            return jsonify({"success": False, "error": result.get("error", "Agent workflow failed")})
        
        response_text = result.get("response", "I apologize, I couldn't generate a response.")
        print(f"💬 Response (first 100 chars): {response_text[:100]}...")
        memory.add_assistant_message(response_text)
        
        tools_used = []
        if result.get("tool_results"):
            tools_used = [tr.get("tool", "") for tr in result["tool_results"] if tr.get("success")]
            
            # Extract and store file context from tool results
            _extract_and_store_file_context(result.get("tool_results", []), memory)
            
            # Update long-term memory if user is authenticated and analysis tool was used
            if user_id > 0:
                analysis_tools = ['analyze_snp_file', 'full_genetic_report']
                if any(t in tools_used for t in analysis_tools):
                    try:
                        from services.user_memory_service import update_user_memory_after_analysis
                        update_user_memory_after_analysis(user_id)
                        print(f"🧠 Updated long-term memory for user {user_id}")
                    except Exception as mem_err:
                        print(f"⚠️ Failed to update long-term memory: {mem_err}")
        
        return jsonify({
            "success": True,
            "response": response_text,
            "tools_used": tools_used,
            "iterations": result.get("iterations", 1),
            "user_id": user_id if user_id > 0 else None
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
        # Use user-specific session if authenticated
        if current_user.is_authenticated:
            session_id = f"user_{current_user.id}"
        else:
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
        data = request.json or {}
        
        # Use user-specific session if authenticated
        if current_user.is_authenticated:
            session_id = f"user_{current_user.id}"
        else:
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
        
        # Check LangSmith status
        try:
            from agent.langsmith_utils import is_langsmith_available
            status["langsmith_enabled"] = is_langsmith_available()
        except ImportError:
            status["langsmith_enabled"] = False
    
    return jsonify(status)


@agent_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """
    Get agent performance metrics from LangSmith
    ---
    tags:
      - Agent
    parameters:
      - name: hours
        in: query
        type: integer
        default: 24
        description: Number of hours to look back
    """
    try:
        from agent.monitoring import get_monitoring_service
        
        hours = request.args.get("hours", 24, type=int)
        monitoring = get_monitoring_service()
        
        if not monitoring.is_available():
            return jsonify({
                "success": False,
                "error": "Metrics not available. Check LangSmith configuration."
            })
        
        metrics = monitoring.get_metrics(hours=hours)
        
        if not metrics:
            return jsonify({
                "success": False,
                "error": "No metrics data available for the specified time period."
            })
        
        return jsonify({
            "success": True,
            "metrics": metrics.to_dict()
        })
        
    except ImportError:
        return jsonify({
            "success": False,
            "error": "LangSmith monitoring not available. Install langsmith package."
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
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - run_id
            - rating
          properties:
            run_id:
              type: string
              description: The LangSmith run ID
            rating:
              type: integer
              minimum: 1
              maximum: 5
              description: User rating (1-5 stars)
            comment:
              type: string
              description: Optional feedback comment
    """
    try:
        from agent.langsmith_utils import log_user_feedback
        
        data = request.json
        run_id = data.get("run_id")
        rating = data.get("rating", 3)  # 1-5 scale
        comment = data.get("comment")
        
        if not run_id:
            return jsonify({"success": False, "error": "run_id is required"})
        
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({"success": False, "error": "rating must be an integer between 1 and 5"})
        
        success = log_user_feedback(
            run_id=run_id,
            rating=rating,
            feedback_text=comment
        )
        
        return jsonify({
            "success": success,
            "message": "Feedback submitted successfully" if success else "Failed to submit feedback. Check LangSmith configuration."
        })
        
    except ImportError:
        return jsonify({
            "success": False,
            "error": "LangSmith not available. Install langsmith package."
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@agent_bp.route('/errors', methods=['GET'])
def get_recent_errors():
    """
    Get recent error traces from LangSmith
    ---
    tags:
      - Agent
    parameters:
      - name: hours
        in: query
        type: integer
        default: 24
        description: Number of hours to look back
      - name: limit
        in: query
        type: integer
        default: 50
        description: Maximum number of errors to return
    """
    try:
        from agent.monitoring import get_monitoring_service
        
        hours = request.args.get("hours", 24, type=int)
        limit = request.args.get("limit", 50, type=int)
        
        monitoring = get_monitoring_service()
        
        if not monitoring.is_available():
            return jsonify({
                "success": False,
                "error": "Monitoring not available. Check LangSmith configuration."
            })
        
        errors = monitoring.get_recent_errors(hours=hours, limit=limit)
        
        return jsonify({
            "success": True,
            "errors": errors,
            "count": len(errors)
        })
        
    except ImportError:
        return jsonify({
            "success": False,
            "error": "LangSmith monitoring not available."
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

