import datetime
import json
import os
from typing import Any, Optional, Dict, List


class AgentMemory:
    def __init__(self, memory_size: int=10):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.storage_dir = current_dir
        self.memory_size = memory_size

        self.conversations_file = os.path.join(current_dir, 'conversations.json')
        self.conversations = self._load_json(self.conversations_file, default=[])

        # Working memory (stays in RAM)
        self.working_memory = []
        self.working_memory_capacity = memory_size

    def _load_json(self, file_path: str, default:Any = None) -> list:
        """Load data from JSON file or return default if file doesn't exist"""
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except json.decoder.JSONDecodeError:
                return default
        return default

    def _save_json(self, date:Any, file_path:str) -> None:
        """Save data to JSON file """
        with open(file_path, 'w') as f:
            json.dump(date, f, indent=2)

    def add_conversation(self, user_message:str, agent_response:str,  metadata:Optional[Dict[str, Any]]=None) -> None:
        """Add conversation to memory."""
        conversation = {
            'user_message': user_message,
            'agent_response': agent_response,
            'timestamp': datetime.datetime.now().isoformat(),
            'metadata': metadata
        }
        self.conversations.append(conversation)
        self._save_json(self.conversations, self.conversations_file)
        # Also update working memory
        self.add_to_working_memory(f"User: {user_message}", importance=1.0)
        self.add_to_working_memory(f"Agent: {agent_response}", importance=0.9)

    def add_to_working_memory(self, content: str, importance: float = 1.0) -> None:
        """Add an item to working memory with importance score."""
        item = {
            "content": content,
            "importance": importance,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self.working_memory.append(item)

        # If over capacity, remove least important items
        if len(self.working_memory) > self.working_memory_capacity:
            self.working_memory.sort(key=lambda x: (x["importance"], x["timestamp"]))
            self.working_memory = self.working_memory[1:]  # Remove least important

    def search_conversations(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Simple keyword search for past conversations."""
        query_terms = query.lower().split()
        results = []

        for conv in self.conversations:
            text = f"{conv['user_message']} {conv['agent_response']}".lower()
            # Score based on number of matching terms
            score = sum(1 for term in query_terms if term in text)
            if score > 0:
                results.append((conv, score))

        # Sort by score (descending) and return top matches
        results.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in results[:limit]]

    def get_recent_conversations(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get the most recent conversations."""
        return (
            self.conversations[-count:]
            if len(self.conversations) >= count
            else self.conversations
        )

    def generate_context_for_llm(self) -> str:
        """Generate a context string for the LLM using relevant memory."""
        # Get working memory
        working_items = sorted(
            self.working_memory,
            key=lambda x: (x["importance"], x["timestamp"]),
            reverse=True,
        )
        working_memory_text = "\n".join(
            [f"- {item['content']}" for item in working_items]
        )

        # Get recent conversations
        recent = self.get_recent_conversations(count=3)
        recent_text = "\n".join(
            [
                f"User: {conv['user_message']}\nAgent: {conv['agent_response']}"
                for conv in recent
            ]
        )

        # Combine everything into a context string
        context = f"""
        ### Current Context (Working Memory):
        {working_memory_text}
        
        ### Recent Conversation History:
        {recent_text}
        """
        return context.strip()