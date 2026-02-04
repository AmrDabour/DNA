"""
User Memory Routes - API endpoints for managing user memory for AI Agent

Allows users to view, update, and delete their stored memory data.
Memory is used to personalize AI agent responses.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

user_memory_bp = Blueprint('user_memory', __name__, url_prefix='/api/user/memory')


@user_memory_bp.route('', methods=['GET'])
@login_required
def get_memory():
    """
    Get current user's stored memory data
    ---
    tags:
      - User Memory
    responses:
      200:
        description: User memory data
    """
    try:
        from services.user_memory_service import get_user_memory_service
        
        service = get_user_memory_service()
        memory = service.get_user_memory(current_user.id)
        
        if not memory:
            # Try to build from analyses
            memory = service.build_memory_from_analyses(current_user.id)
        
        return jsonify({
            "success": True,
            "memory": memory,
            "memory_enabled": memory.get('memory_enabled', True) if memory else False
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@user_memory_bp.route('', methods=['PATCH'])
@login_required
def update_memory():
    """
    Update user memory preferences
    ---
    tags:
      - User Memory
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              preferences:
                type: object
                description: User preferences for AI interactions
              name:
                type: string
                description: User's preferred name
    """
    try:
        from services.user_memory_service import get_user_memory_service
        
        data = request.json or {}
        service = get_user_memory_service()
        
        updates = {}
        
        # Allow updating specific fields
        if 'name' in data:
            updates['name'] = data['name']
        
        if 'preferences' in data:
            updates['preferences'] = data['preferences']
        
        if updates:
            service.update_user_memory(current_user.id, updates)
        
        return jsonify({
            "success": True,
            "message": "Memory updated successfully"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@user_memory_bp.route('/enable', methods=['POST'])
@login_required
def enable_memory():
    """
    Enable long-term memory for AI personalization
    ---
    tags:
      - User Memory
    """
    try:
        from services.user_memory_service import get_user_memory_service
        
        service = get_user_memory_service()
        service.enable_memory(current_user.id, enabled=True)
        
        # Build initial memory from existing analyses
        service.build_memory_from_analyses(current_user.id)
        
        return jsonify({
            "success": True,
            "message": "Memory enabled. Your AI assistant will now remember you."
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@user_memory_bp.route('/disable', methods=['POST'])
@login_required
def disable_memory():
    """
    Disable long-term memory (agent won't remember user between sessions)
    ---
    tags:
      - User Memory
    """
    try:
        from services.user_memory_service import get_user_memory_service
        
        service = get_user_memory_service()
        service.enable_memory(current_user.id, enabled=False)
        
        return jsonify({
            "success": True,
            "message": "Memory disabled. Your AI assistant will no longer use stored information."
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@user_memory_bp.route('', methods=['DELETE'])
@login_required
def delete_memory():
    """
    Completely delete all stored memory data (right to be forgotten)
    ---
    tags:
      - User Memory
    """
    try:
        from services.user_memory_service import get_user_memory_service
        
        service = get_user_memory_service()
        service.delete_user_memory(current_user.id)
        
        return jsonify({
            "success": True,
            "message": "All memory data has been deleted."
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@user_memory_bp.route('/refresh', methods=['POST'])
@login_required
def refresh_memory():
    """
    Rebuild memory from analysis history
    Useful after new analyses or to sync data
    ---
    tags:
      - User Memory
    """
    try:
        from services.user_memory_service import get_user_memory_service
        
        service = get_user_memory_service()
        memory = service.build_memory_from_analyses(current_user.id)
        
        return jsonify({
            "success": True,
            "message": "Memory refreshed from your analysis history.",
            "memory": memory
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@user_memory_bp.route('/preview', methods=['GET'])
@login_required
def preview_prompt():
    """
    Preview the prompt that will be injected into AI conversations
    Useful for debugging and understanding what the AI knows about you
    ---
    tags:
      - User Memory
    """
    try:
        from services.user_memory_service import get_user_memory_prompt
        
        prompt = get_user_memory_prompt(current_user.id)
        
        return jsonify({
            "success": True,
            "prompt_preview": prompt,
            "prompt_length": len(prompt)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
