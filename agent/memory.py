"""
Chat Memory Management - Persist conversation history across sessions
Supports Redis persistence with in-memory fallback
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

# Import Redis cache (optional - graceful degradation)
try:
    from config.redis import memory_cache, is_redis_available
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    memory_cache = None

# Memory TTL in seconds (24 hours)
MEMORY_TTL_SECONDS = 24 * 3600


@dataclass
class Message:
    """Single chat message"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            metadata=data.get("metadata", {})
        )


class ChatMemory:
    """
    Conversation memory manager with sliding window.
    Supports Redis persistence with automatic sync.
    """
    
    def __init__(self, window_size: int = 20, session_id: str = None):
        self.window_size = window_size
        self.session_id = session_id
        self.messages: List[Message] = []
        self.context: Dict = {}  # Store additional context (current file, patient, etc.)
        self._dirty = False  # Track if memory needs to be saved
    
    def add_user_message(self, content: str, metadata: Dict = None) -> None:
        """Add a user message to history"""
        msg = Message(role="user", content=content, metadata=metadata or {})
        self.messages.append(msg)
        self._trim_history()
        self._dirty = True
        self._save_to_redis()
    
    def add_assistant_message(self, content: str, metadata: Dict = None) -> None:
        """Add an assistant message to history"""
        msg = Message(role="assistant", content=content, metadata=metadata or {})
        self.messages.append(msg)
        self._trim_history()
        self._dirty = True
        self._save_to_redis()
    
    def add_system_message(self, content: str) -> None:
        """Add a system message to history"""
        msg = Message(role="system", content=content)
        self.messages.append(msg)
        self._trim_history()
        self._dirty = True
        self._save_to_redis()
    
    def _trim_history(self) -> None:
        """Keep only the last N messages"""
        if len(self.messages) > self.window_size:
            # Keep the first system message if exists
            system_msgs = [m for m in self.messages if m.role == "system"]
            other_msgs = [m for m in self.messages if m.role != "system"]
            
            # Keep last (window_size - 1) non-system messages + 1 system message
            if system_msgs:
                self.messages = [system_msgs[0]] + other_msgs[-(self.window_size - 1):]
            else:
                self.messages = other_msgs[-self.window_size:]
    
    def _save_to_redis(self) -> bool:
        """Save memory to Redis if available"""
        if not self.session_id or not REDIS_AVAILABLE or not memory_cache:
            return False
        
        try:
            data = self.to_json()
            memory_cache.set(f"session:{self.session_id}", {
                "data": data,
                "window_size": self.window_size,
                "updated_at": datetime.now().isoformat()
            }, ttl=MEMORY_TTL_SECONDS)
            self._dirty = False
            return True
        except Exception as e:
            logger.debug(f"Failed to save memory to Redis: {e}")
            return False
    
    @classmethod
    def _load_from_redis(cls, session_id: str, window_size: int = 20) -> Optional["ChatMemory"]:
        """Load memory from Redis if available"""
        if not REDIS_AVAILABLE or not memory_cache:
            return None
        
        try:
            cached = memory_cache.get(f"session:{session_id}")
            if cached and "data" in cached:
                memory = cls.from_json(cached["data"], window_size=window_size)
                memory.session_id = session_id
                memory._dirty = False
                return memory
        except Exception as e:
            logger.debug(f"Failed to load memory from Redis: {e}")
        
        return None
    
    def get_history(self) -> List[Dict]:
        """Get message history as list of dicts"""
        return [msg.to_dict() for msg in self.messages]
    
    def get_messages_for_llm(self) -> List[Dict]:
        """Get messages formatted for LLM input"""
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]
    
    def set_context(self, key: str, value) -> None:
        """Set context variable"""
        self.context[key] = value
        self._dirty = True
        saved = self._save_to_redis()
        logger.info(f"Set context '{key}' = '{value}' (saved to Redis: {saved})")
    
    def get_context(self, key: str, default=None):
        """Get context variable"""
        value = self.context.get(key, default)
        logger.debug(f"Get context '{key}' = '{value}' (available keys: {list(self.context.keys())})")
        return value
    
    def clear_context(self) -> None:
        """Clear all context"""
        self.context = {}
        self._dirty = True
        self._save_to_redis()
    
    def clear(self) -> None:
        """Clear all messages and context"""
        self.messages = []
        self.context = {}
        self._dirty = True
        self._save_to_redis()
    
    def get_last_user_message(self) -> Optional[str]:
        """Get the last user message content"""
        for msg in reversed(self.messages):
            if msg.role == "user":
                return msg.content
        return None
    
    def to_json(self) -> str:
        """Serialize memory to JSON"""
        return json.dumps({
            "messages": [m.to_dict() for m in self.messages],
            "context": self.context
        })
    
    @classmethod
    def from_json(cls, data: str, window_size: int = 20) -> "ChatMemory":
        """Deserialize memory from JSON"""
        parsed = json.loads(data)
        memory = cls(window_size=window_size)
        memory.messages = [Message.from_dict(m) for m in parsed.get("messages", [])]
        memory.context = parsed.get("context", {})
        return memory


# Session-based memory store (in-memory fallback)
_memory_store: Dict[str, ChatMemory] = {}


def get_memory(session_id: str, window_size: int = 20) -> ChatMemory:
    """
    Get or create memory for a session.
    ALWAYS loads from Redis first to ensure multi-worker consistency,
    then caches in-memory for performance within the same worker.
    """
    # ALWAYS try to load from Redis first for multi-worker consistency
    redis_memory = ChatMemory._load_from_redis(session_id, window_size)
    
    if redis_memory:
        # Update in-memory cache with latest from Redis
        _memory_store[session_id] = redis_memory
        logger.debug(f"Loaded memory for session {session_id} from Redis (context keys: {list(redis_memory.context.keys())})")
        return redis_memory
    
    # Check in-memory store if Redis didn't have it
    if session_id in _memory_store:
        return _memory_store[session_id]
    
    # Create new memory
    memory = ChatMemory(window_size=window_size, session_id=session_id)
    _memory_store[session_id] = memory
    return memory


def clear_memory(session_id: str) -> None:
    """Clear memory for a session (both in-memory and Redis)"""
    if session_id in _memory_store:
        _memory_store[session_id].clear()
    
    # Also clear from Redis
    if REDIS_AVAILABLE and memory_cache:
        try:
            memory_cache.delete(f"session:{session_id}")
        except Exception as e:
            logger.debug(f"Failed to clear Redis memory: {e}")


def delete_memory(session_id: str) -> None:
    """Completely delete memory for a session"""
    if session_id in _memory_store:
        del _memory_store[session_id]
    
    # Also delete from Redis
    if REDIS_AVAILABLE and memory_cache:
        try:
            memory_cache.delete(f"session:{session_id}")
        except Exception as e:
            logger.debug(f"Failed to delete Redis memory: {e}")


def get_all_sessions() -> List[str]:
    """Get all active session IDs (combines in-memory and Redis)"""
    sessions = set(_memory_store.keys())
    
    # Get sessions from Redis
    if REDIS_AVAILABLE and memory_cache:
        try:
            from config.redis import get_redis_client
            client = get_redis_client()
            if client:
                redis_keys = client.keys("genovaai:memory:session:*")
                for key in redis_keys:
                    # Extract session ID from key
                    session_id = key.replace("genovaai:memory:session:", "")
                    sessions.add(session_id)
        except Exception as e:
            logger.debug(f"Failed to get Redis sessions: {e}")
    
    return list(sessions)


def cleanup_old_sessions(max_sessions: int = 100) -> int:
    """Remove oldest sessions if too many exist"""
    if len(_memory_store) <= max_sessions:
        return 0
    
    # Sort by last message timestamp and remove oldest
    sessions_with_time = []
    for sid, memory in _memory_store.items():
        if memory.messages:
            last_time = memory.messages[-1].timestamp
        else:
            last_time = "1970-01-01T00:00:00"
        sessions_with_time.append((sid, last_time))
    
    sessions_with_time.sort(key=lambda x: x[1])
    
    # Remove oldest sessions
    to_remove = len(_memory_store) - max_sessions
    removed = 0
    for sid, _ in sessions_with_time[:to_remove]:
        delete_memory(sid)
        removed += 1
    
    return removed


def get_memory_stats() -> Dict:
    """Get memory usage statistics"""
    in_memory_count = len(_memory_store)
    redis_count = 0
    redis_available = False
    
    if REDIS_AVAILABLE and is_redis_available():
        redis_available = True
        try:
            from config.redis import get_redis_client
            client = get_redis_client()
            if client:
                redis_keys = client.keys("genovaai:memory:session:*")
                redis_count = len(redis_keys) if redis_keys else 0
        except:
            pass
    
    return {
        "in_memory_sessions": in_memory_count,
        "redis_sessions": redis_count,
        "redis_available": redis_available,
        "storage_backend": "redis" if redis_available else "memory",
        "ttl_seconds": MEMORY_TTL_SECONDS
    }
