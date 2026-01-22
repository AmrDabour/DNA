"""
Agent Routes - REST API for DNA Analysis Agent
Agent Service Microservice
"""
from flask import Blueprint, request, jsonify
import os
import sys
import uuid
import requests
from datetime import datetime

agent_bp = Blueprint('agent', __name__)

# Import agent components
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from agent.workflow import get_workflow, DNAAgentWorkflow
    from agent.memory import get_memory, ChatMemory
    AGENT_AVAILABLE = True
    
    # Create helper function that matches what routes expect
    def run_agent(message: str, session_id: str) -> dict:
        """Run the agent workflow"""
        workflow = get_workflow()
        return workflow.run(message, session_id)
    
except ImportError as e:
    print(f"⚠️ Agent import error: {e}")
    AGENT_AVAILABLE = False
    run_agent = None


# Service URLs
PREDICTION_SERVICE_URL = os.environ.get("PREDICTION_SERVICE_URL", "http://prediction-service:5003")
ANALYSIS_SERVICE_URL = os.environ.get("ANALYSIS_SERVICE_URL", "http://analysis-service:5002")
AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://ai-service:5004")


# ============================================================
# Chat Endpoints
# ============================================================

@agent_bp.route('/api/agent/chat', methods=['POST'])
def agent_chat():
    """
    Send message to DNA Analysis Agent
    
    POST /api/agent/chat
    Body: {"message": "...", "session_id": "..."}
    
    Returns: {"success": true, "response": "...", "session_id": "..."}
    """
    try:
        if not AGENT_AVAILABLE:
            return jsonify({
                "success": False,
                "error": "Agent not available. Check configuration."
            }), 503
        
        data = request.get_json() or {}
        message = data.get('message')
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        if not message:
            return jsonify({
                "success": False,
                "error": "message is required"
            }), 400
        
        # Run agent
        result = run_agent(message, session_id)
        
        # Extract tool names used for the frontend
        tool_results = result.get("tool_results", [])
        tools_used = [t.get("tool", t.get("name", "unknown")) for t in tool_results if isinstance(t, dict)]
        
        return jsonify({
            "success": True,
            "response": result.get("response", ""),
            "session_id": session_id,
            "tool_calls": result.get("tool_calls", []),
            "tools_used": tools_used,
            "iterations": result.get("iterations", 0)
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agent_bp.route('/api/agent/chat/stream', methods=['POST'])
def agent_chat_stream():
    """
    Stream response from DNA Analysis Agent
    
    POST /api/agent/chat/stream
    Body: {"message": "...", "session_id": "..."}
    
    Returns: Server-Sent Events stream
    """
    try:
        if not AGENT_AVAILABLE:
            return jsonify({
                "success": False,
                "error": "Agent not available"
            }), 503
        
        data = request.get_json() or {}
        message = data.get('message')
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        if not message:
            return jsonify({
                "success": False,
                "error": "message is required"
            }), 400
        
        # For now, return non-streaming response
        # TODO: Implement true streaming
        result = run_agent(message, session_id)
        
        return jsonify({
            "success": True,
            "response": result.get("response", ""),
            "session_id": session_id,
            "streaming": False
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# Session Management
# ============================================================

@agent_bp.route('/api/agent/session', methods=['POST'])
def create_session():
    """
    Create new chat session
    
    POST /api/agent/session
    
    Returns: {"success": true, "session_id": "..."}
    """
    session_id = str(uuid.uuid4())
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        "created_at": datetime.utcnow().isoformat()
    }), 201


@agent_bp.route('/api/agent/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """
    Get session info and chat history
    
    GET /api/agent/session/<session_id>
    
    Returns: {"success": true, "session": {...}, "history": [...]}
    """
    try:
        memory = get_memory(session_id)
        history = memory.get_history() if memory else []
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "history": history
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agent_bp.route('/api/agent/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """
    Delete chat session and history
    
    DELETE /api/agent/session/<session_id>
    
    Returns: {"success": true}
    """
    try:
        memory = get_memory(session_id)
        if memory:
            memory.clear()
        
        return jsonify({
            "success": True,
            "message": "Session deleted"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# Quick Actions (Direct API calls without full agent)
# ============================================================

@agent_bp.route('/api/agent/quick/analyze', methods=['POST'])
def quick_analyze():
    """
    Quick file analysis without full agent conversation
    
    POST /api/agent/quick/analyze
    Body: {"file_path": "...", "sample_id": "..."}
    
    Returns: {"success": true, "analysis": {...}}
    """
    try:
        data = request.get_json() or {}
        file_path = data.get('file_path')
        sample_id = data.get('sample_id')
        
        if not file_path and not sample_id:
            return jsonify({
                "success": False,
                "error": "file_path or sample_id is required"
            }), 400
        
        # Call prediction service
        if sample_id:
            response = requests.post(
                f"{PREDICTION_SERVICE_URL}/api/predictions/combined",
                json={"sample_id": sample_id},
                timeout=60
            )
            
            if response.ok:
                return jsonify(response.json()), 200
            else:
                return jsonify({
                    "success": False,
                    "error": "Prediction service error"
                }), 502
        
        return jsonify({
            "success": False,
            "error": "File analysis not implemented in quick mode"
        }), 400
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "error": f"Service communication error: {str(e)}"
        }), 502
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agent_bp.route('/api/agent/quick/physical', methods=['POST'])
def quick_physical():
    """
    Quick physical characteristics generation
    
    POST /api/agent/quick/physical
    Body: {"gender": "Male", "population": "CEU"}
    
    Returns: {"success": true, "characteristics": "..."}
    """
    try:
        data = request.get_json() or {}
        gender = data.get('gender')
        population = data.get('population')
        
        if not gender or not population:
            return jsonify({
                "success": False,
                "error": "gender and population are required"
            }), 400
        
        # Call AI service
        response = requests.post(
            f"{AI_SERVICE_URL}/api/ai/physical",
            json={"gender": gender, "population": population},
            timeout=60
        )
        
        if response.ok:
            return jsonify(response.json()), 200
        else:
            return jsonify({
                "success": False,
                "error": "AI service error"
            }), 502
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "error": f"Service communication error: {str(e)}"
        }), 502
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agent_bp.route('/api/agent/quick/disease-risk', methods=['POST'])
def quick_disease_risk():
    """
    Quick disease risk analysis
    
    POST /api/agent/quick/disease-risk
    Body: {"gender": "Male", "population": "CEU"}
    
    Returns: {"success": true, "report": "..."}
    """
    try:
        data = request.get_json() or {}
        gender = data.get('gender')
        population = data.get('population')
        
        if not gender or not population:
            return jsonify({
                "success": False,
                "error": "gender and population are required"
            }), 400
        
        # Call AI service
        response = requests.post(
            f"{AI_SERVICE_URL}/api/ai/disease-risk",
            json={"gender": gender, "population": population},
            timeout=60
        )
        
        if response.ok:
            return jsonify(response.json()), 200
        else:
            return jsonify({
                "success": False,
                "error": "AI service error"
            }), 502
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "error": f"Service communication error: {str(e)}"
        }), 502
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# Health/Status
# ============================================================

@agent_bp.route('/api/agent/status', methods=['GET'])
def agent_status():
    """
    Get agent service status
    
    GET /api/agent/status
    
    Returns: {"success": true, "status": {...}}
    """
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY")
    
    # Check dependent services
    services_status = {}
    
    for name, url in [
        ("prediction", PREDICTION_SERVICE_URL),
        ("analysis", ANALYSIS_SERVICE_URL),
        ("ai", AI_SERVICE_URL)
    ]:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            services_status[name] = response.ok
        except:
            services_status[name] = False
    
    return jsonify({
        "success": True,
        "status": {
            "agent_available": AGENT_AVAILABLE,
            "gemini_configured": gemini_key is not None,
            "model": os.environ.get("AGENT_MODEL", "gemini-2.5-flash"),
            "services": services_status
        }
    }), 200


# ============================================================
# File Upload for Agent
# ============================================================

@agent_bp.route('/api/agent/upload', methods=['POST'])
def agent_upload():
    """
    Upload file for agent analysis
    
    POST /api/agent/upload
    Form: file=<file>
    
    Returns: {"success": true, "file_path": "...", "sample_id": "..."}
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "error": "No file provided"
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                "success": False,
                "error": "No file selected"
            }), 400
        
        # Forward to analysis service for file handling
        files = {'file': (file.filename, file.stream, file.content_type or 'application/octet-stream')}
        
        response = requests.post(
            f"{ANALYSIS_SERVICE_URL}/api/upload",
            files=files,
            timeout=120
        )
        
        if response.ok:
            data = response.json()
            return jsonify(data), response.status_code
        else:
            return jsonify({
                "success": False,
                "error": "Upload service error"
            }), 502
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            "success": False,
            "error": f"Service communication error: {str(e)}"
        }), 502
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# Chat History Endpoint
# ============================================================

@agent_bp.route('/api/agent/history', methods=['GET'])
def get_chat_history():
    """
    Get chat history for a session
    
    GET /api/agent/history?session_id=xxx
    
    Returns: {"success": true, "messages": [...]}
    """
    try:
        session_id = request.args.get('session_id')
        
        if not session_id:
            return jsonify({
                "success": False,
                "error": "session_id is required"
            }), 400
        
        if not AGENT_AVAILABLE:
            return jsonify({
                "success": True,
                "messages": []
            }), 200
        
        memory = get_memory(session_id)
        messages = memory.get_history() if memory else []
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "messages": messages
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@agent_bp.route('/api/agent/clear', methods=['POST'])
def clear_chat_history():
    """
    Clear chat history for a session
    
    POST /api/agent/clear
    Body: {"session_id": "xxx"}
    
    Returns: {"success": true}
    """
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({
                "success": False,
                "error": "session_id is required"
            }), 400
        
        if AGENT_AVAILABLE:
            memory = get_memory(session_id)
            if memory:
                memory.clear()
        
        return jsonify({
            "success": True,
            "message": "Chat history cleared"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
