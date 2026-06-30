"""
Chat Summary Generator.

Provides functionality to summarize recent chat history using:
- SiliconFlow / OpenAI-compatible API (primary)
- Ollama LLM (fallback)
- Simple extractive summarization (last resort)
"""

import sys
import os
from dotenv import load_dotenv
from openai import OpenAI

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv(override=True)
import config.settings as cfg


class SummaryGenerator:
    """Generate summaries of chat history."""

    def __init__(self, llm_client=None):
        """
        Args:
            llm_client: Optional AIBot instance for LLM summarization.
                        If None and SiliconFlow/Ollama is available, will use
                        OpenAI-compatible API directly.
        """
        self.llm_client = llm_client
        self.max_history_for_summary = 10

        # Try to init a direct API client for summarization
        self._direct_client = None
        self._direct_model = None

        sf_key = os.getenv("SILICONFLOW_API_KEY", cfg.SILICONFLOW_API_KEY)
        if sf_key and sf_key not in ("EMPTY", "sk-your-siliconflow-key-here", ""):
            self._direct_client = OpenAI(
                api_key=sf_key,
                base_url=os.getenv("SILICONFLOW_BASE_URL", cfg.SILICONFLOW_BASE_URL)
            )
            self._direct_model = os.getenv("SILICONFLOW_MODEL", cfg.SILICONFLOW_MODEL)

    def generate(self, chat_history: list) -> str:
        """Generate summary of recent chat messages."""
        if not chat_history:
            return "No chat history to summarize."

        recent = chat_history[-self.max_history_for_summary:]

        # Try LLM summarization
        if self.llm_client:
            try:
                return self._summarize_with_llm(recent)
            except Exception as e:
                print(f"[WARNING] LLM summarization failed: {e}, trying direct API")

        if self._direct_client:
            try:
                return self._summarize_with_direct_api(recent)
            except Exception as e:
                print(f"[WARNING] Direct API summarization failed: {e}, using fallback")

        return self._summarize_basic(recent)

    def _summarize_with_llm(self, messages: list) -> str:
        """Use AIBot LLM client to generate intelligent summary."""
        chat_text = "\n".join(messages)
        prompt = (
            "Please summarize the following chat conversation in 2-3 sentences.\n"
            "Focus on the main topics discussed and any important decisions or conclusions.\n\n"
            f"Chat History:\n{chat_text}\n\nSummary:"
        )

        if hasattr(self.llm_client, 'chat'):
            response = self.llm_client.chat(prompt)
            return f"📝 Chat Summary:\n{response}"
        elif hasattr(self.llm_client, 'generate_summary'):
            return self.llm_client.generate_summary(chat_text)
        else:
            raise ValueError("LLM client doesn't support chat method")

    def _summarize_with_direct_api(self, messages: list) -> str:
        """Use SiliconFlow / OpenAI-compatible API directly for summarization."""
        chat_text = "\n".join(messages)
        prompt = (
            "Please summarize the following chat conversation in 2-3 sentences.\n"
            "Focus on the main topics discussed and any important decisions or conclusions.\n\n"
            f"Chat History:\n{chat_text}"
        )

        response = self._direct_client.chat.completions.create(
            model=self._direct_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes chat conversations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=256,
            timeout=30
        )

        content = response.choices[0].message.content
        return f"📝 Chat Summary:\n{content}"

    def _summarize_basic(self, messages: list) -> str:
        """Basic extractive summarization (fallback)."""
        if len(messages) == 0:
            return "No messages to summarize."
        if len(messages) == 1:
            return f"📝 Recent activity:\n{messages[0]}"

        total_messages = len(messages)
        first_msg = messages[0][:100] + ("..." if len(messages[0]) > 100 else "")
        last_msg = messages[-1][:100] + ("..." if len(messages[-1]) > 100 else "")

        # Find unique participants
        participants = set()
        for msg in messages:
            if ':' in msg:
                parts = msg.split(':')
                if len(parts) > 0:
                    name_part = parts[0]
                    if ')' in name_part:
                        name = name_part.split(')')[-1].strip()
                        participants.add(name)

        summary_lines = [
            "📝 Chat Summary",
            f"• Total messages: {total_messages}",
            f"• Participants: {', '.join(participants) if participants else 'Unknown'}",
            f"• Started with: {first_msg}",
            f"• Latest: {last_msg}"
        ]

        return "\n".join(summary_lines)


def create_summary_from_list(messages: list, max_msgs: int = 10) -> str:
    """Convenience function to create summary from message list."""
    generator = SummaryGenerator()
    generator.max_history_for_summary = max_msgs
    return generator.generate(messages)
    return generator.generate(messages)


if __name__ == "__main__":
    # Test the summary generator
    test_history = [
        "(12.04.25,10:00) Alice : Hello everyone!",
        "(12.04.25,10:01) Bob : Hi Alice! How are you?",
        "(12.04.25,10:02) Alice : I'm doing great, thanks for asking.",
        "(12.04.25,10:03) Charlie : Hey team! What's up?",
        "(12.04.25,10:04) Bob : Just working on the project.",
        "(12.04.25,10:05) Alice : Same here. The deadline is approaching.",
        "(12.04.25,10:06) Charlie : Let me know if you need help.",
        "(12.04.25,10:07) Alice : Thanks Charlie! That would be great.",
    ]
    
    generator = SummaryGenerator()
    summary = generator.generate(test_history)
    print("Generated Summary:")
    print("-" * 50)
    print(summary)
