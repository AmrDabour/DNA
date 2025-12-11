"""
Chat Memory Management - Persist conversation history across sessions
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


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
    Conversation memory manager with sliding window
    """
    
    def __init__(self, window_size: int = 20):
        self.window_size = window_size
        self.messages: List[Message] = []
        self.context: Dict = {}  # Store additional context (current file, patient, etc.)
        
    def add_user_message(self, content: str, metadata: Dict = None) -> None:
        """Add a user message to history"""
        msg = Message(role="user", content=content, metadata=metadata or {})
        self.messages.append(msg)
        self._trim_history()
    
    def add_assistant_message(self, content: str, metadata: Dict = None) -> None:
        """Add an assistant message to history"""
        msg = Message(role="assistant", content=content, metadata=metadata or {})
        self.messages.append(msg)
        self._trim_history()
    
    def add_system_message(elf, content: str) -> None:
        """Add a system message to history"""
        msg = Message(role="system", content=content)
        self.messages.append(msg)
        self._trim_history()
    
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
    
    def get_history(self) -> List[Dict]:
        """Get message history as list of dicts"""
        return [msg.to_dict() for msg in self.messages]
    
    def get_messages_for_llm(self) -> List[Dict]:
        """Get messages formatted for LLM input"""
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]
    
    def set_context(self, key: str, value) -> None:
        """Set context variable"""
        self.context[key] = value
    
    def get_context(self, key: str, default=None):
        """Get context variable"""
        return self.context.get(key, default)
    
    def clear_context(self) -> None:
        """Clear all context"""
        self.context = {}
    
    def clear(self) -> None:
        """Clear all messages and context"""
        self.messages = []
        self.context = {}
    
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


# Session-based memory store (one memory per session)
_memory_store: Dict[str, ChatMemory] = {}


def get_memory(session_id: str, window_size: int = 20) -> ChatMemory:
    """Get or create memory for a session"""
    if session_id not in _memory_store:
        _memory_store[session_id] = ChatMemory(window_size=window_size)
    return _memory_store[session_id]


def clear_memory(session_id: str) -> None:
    """Clear memory for a session"""
    if session_id in _memory_store:
        _memory_store[session_id].clear()


def get_all_sessions() -> List[str]:
    """Get all active session IDs"""
    return list(_memory_store.keys())


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
        del _memory_store[sid]
        removed += 1
    
    return removed

