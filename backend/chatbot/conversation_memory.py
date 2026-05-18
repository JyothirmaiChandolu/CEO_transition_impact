"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Manages a rolling buffer of recent conversation messages for context-aware chatbot responses.
"""

from collections import deque
from datetime import datetime
from typing import List, Dict, Optional


class ConversationMemory:
    """Manages conversation history with a buffer window."""

    def __init__(self, max_messages: int = 10):
        """
        Initialize conversation memory.

        Args:
            max_messages: Maximum number of recent messages to keep in buffer
        """
        self.max_messages = max_messages
        self.buffer = deque(maxlen=max_messages)
        self.session_start = datetime.now()

    def add_message(self, role: str, content: str, tokens_input: int = 0, tokens_output: int = 0):
        """
        Add a message to the buffer.

        Args:
            role: "user" or "assistant"
            content: Message text
            tokens_input: Input tokens used
            tokens_output: Output tokens generated
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "tokens_input": tokens_input,
            "tokens_output": tokens_output
        }
        self.buffer.append(message)

    def get_buffer(self) -> List[Dict]:
        """Get current message buffer as list."""
        return list(self.buffer)

    def get_context_string(self) -> str:
        """
        Get conversation context as formatted string for LLM.

        Returns:
            Formatted conversation history for context
        """
        if not self.buffer:
            return "No previous conversation history."

        context_lines = ["Recent conversation context:"]
        for msg in self.buffer:
            role = "User" if msg["role"] == "user" else "Assistant"
            context_lines.append(f"\n{role}: {msg['content'][:100]}...")

        return "\n".join(context_lines)

    def get_total_tokens(self) -> Dict[str, int]:
        """
        Get total tokens used in this conversation.

        Returns:
            Dict with total_input and total_output tokens
        """
        total_input = sum(msg.get("tokens_input", 0) for msg in self.buffer)
        total_output = sum(msg.get("tokens_output", 0) for msg in self.buffer)

        return {
            "total_input": total_input,
            "total_output": total_output,
            "total": total_input + total_output
        }

    def get_session_duration(self) -> str:
        """Get formatted session duration."""
        duration = datetime.now() - self.session_start
        minutes = int(duration.total_seconds() / 60)
        seconds = int(duration.total_seconds() % 60)
        return f"{minutes}m {seconds}s"

    def clear(self):
        """Clear the conversation buffer."""
        self.buffer.clear()
        self.session_start = datetime.now()

    def get_summary(self) -> Dict:
        """
        Get session summary.

        Returns:
            Dict with session statistics
        """
        tokens = self.get_total_tokens()
        return {
            "message_count": len(self.buffer),
            "session_duration": self.get_session_duration(),
            "total_tokens": tokens["total"],
            "input_tokens": tokens["total_input"],
            "output_tokens": tokens["total_output"],
            "session_start": self.session_start.isoformat()
        }


if __name__ == "__main__":
    # Test conversation memory
    memory = ConversationMemory(max_messages=5)

    memory.add_message("user", "What is a recession?", tokens_input=10, tokens_output=50)
    memory.add_message("assistant", "A recession is a period of economic decline...", tokens_input=10, tokens_output=50)
    memory.add_message("user", "How does it affect stock prices?", tokens_input=8, tokens_output=45)
    memory.add_message("assistant", "During recessions, stock prices typically decline...", tokens_input=8, tokens_output=45)

    print("Buffer Contents:")
    for msg in memory.get_buffer():
        print(f"  {msg['role']}: {msg['content'][:50]}...")

    print("\nContext String:")
    print(memory.get_context_string())

    print("\nSession Summary:")
    import json
    print(json.dumps(memory.get_summary(), indent=2))
