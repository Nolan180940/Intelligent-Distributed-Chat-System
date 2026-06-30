"""
AI Chat Bot with LLM Integration.

Features:
- Context-aware conversations using message history
- Configurable persona via system prompts
- Primary: SiliconFlow API (OpenAI-compatible, cloud)
- Fallback: Ollama (local), then offline pattern matching
- Image generation via Pollinations (/aipic command)
"""

import json
import requests
from typing import Optional, List, Dict
import sys
import os
from dotenv import load_dotenv
from openai import OpenAI

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env if present
load_dotenv(override=True)

import config.settings as cfg
from bot.image_gen import generate_image


class AIBot:
    """AI-powered chatbot with context memory and persona support."""

    def __init__(
        self,
        name: str = "Bot",
        persona: str = "helpful"
    ):
        self.name = name
        self.persona = persona

        # Message history for context
        self.message_history: List[Dict[str, str]] = []
        self.max_history_length = 20

        # Persona definitions
        self.personas = {
            "helpful": "You are a helpful, friendly assistant. Be concise and warm in your responses.",
            "humorous": "You are a witty, humorous assistant. Add jokes and light-hearted comments to your responses.",
            "serious": "You are a professional, serious assistant. Be formal and precise in your responses.",
            "creative": "You are a creative, imaginative assistant. Think outside the box and provide unique perspectives.",
            "advisor": "You are an academic advisor at NYU Shanghai. Provide guidance on courses and programming."
        }

        # ---- SiliconFlow (primary cloud AI) ----
        self.sf_api_key = os.getenv("SILICONFLOW_API_KEY", cfg.SILICONFLOW_API_KEY)
        self.sf_base_url = os.getenv("SILICONFLOW_BASE_URL", cfg.SILICONFLOW_BASE_URL)
        self.sf_model = os.getenv("SILICONFLOW_MODEL", cfg.SILICONFLOW_MODEL)

        # ---- Ollama (local fallback) ----
        self.ollama_host = os.getenv("OLLAMA_HOST", cfg.OLLAMA_HOST)
        self.ollama_model = os.getenv("OLLAMA_MODEL", cfg.OLLAMA_MODEL)

        # Detect available backends
        self.siliconflow_available = self._check_siliconflow()
        self.ollama_available = self._check_ollama()

        if self.siliconflow_available:
            self.client = OpenAI(
                api_key=self.sf_api_key,
                base_url=self.sf_base_url
            )
            print(f"[BOT] ✅ SiliconFlow ready ({self.sf_model})")
        elif self.ollama_available:
            print(f"[BOT] ⚠️  SiliconFlow not configured, using Ollama ({self.ollama_model})")
        else:
            print("[BOT] ⚠️  No AI backend available. Using offline fallback responses.")

    # ---- Backend health checks ----

    def _check_siliconflow(self) -> bool:
        """Check if SiliconFlow API key is configured."""
        return bool(self.sf_api_key) and self.sf_api_key not in ("EMPTY", "sk-your-siliconflow-key-here", "")

    def _check_ollama(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    # ---- Persona management ----

    def set_persona(self, persona: str):
        """Set bot persona."""
        if persona in self.personas:
            self.persona = persona
            self.message_history = []
            return True
        return False

    def get_system_prompt(self) -> str:
        """Get system prompt based on current persona."""
        return self.personas.get(self.persona, self.personas["helpful"])

    # ---- Main chat interface ----

    def chat(self, user_message: str) -> str:
        """
        Process user message and generate response.

        Priority: SiliconFlow > Ollama > offline fallback
        """
        # Handle special commands
        if user_message.startswith("/aipic"):
            return self._handle_image_generation(user_message)

        # Add user message to history
        self.message_history.append({"role": "user", "content": user_message})

        # Trim history if too long
        if len(self.message_history) > self.max_history_length:
            self.message_history = self.message_history[-self.max_history_length:]

        # Generate response (priority chain)
        if self.siliconflow_available:
            response = self._chat_with_siliconflow()
        elif self.ollama_available:
            response = self._chat_with_ollama()
        else:
            response = self._fallback_response(user_message)

        # Add bot response to history
        self.message_history.append({"role": "assistant", "content": response})

        return response

    # ---- SiliconFlow (primary) ----

    def _chat_with_siliconflow(self) -> str:
        """Send message to SiliconFlow via OpenAI-compatible API."""
        try:
            messages = [
                {"role": "system", "content": self.get_system_prompt()}
            ] + self.message_history

            response = self.client.chat.completions.create(
                model=self.sf_model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                timeout=30
            )

            content = response.choices[0].message.content
            return content if content else "I'm not sure how to respond."

        except Exception as e:
            print(f"[BOT] SiliconFlow error: {e}")
            # Fall through to next available backend
            if self.ollama_available:
                print("[BOT] Falling back to Ollama...")
                return self._chat_with_ollama()
            return self._fallback_response(
                self.message_history[-1].get("content", "") if self.message_history else ""
            )

    # ---- Ollama (local fallback) ----

    def _chat_with_ollama(self) -> str:
        """Send message to local Ollama and get response."""
        try:
            messages = [
                {"role": "system", "content": self.get_system_prompt()}
            ] + self.message_history

            payload = {
                "model": self.ollama_model,
                "messages": messages,
                "stream": False
            }

            response = requests.post(
                f"{self.ollama_host}/api/chat",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "I'm not sure how to respond.")
            else:
                return f"Error: API returned status {response.status_code}"

        except requests.exceptions.Timeout:
            return "Response timed out. Please try again."
        except Exception as e:
            return f"Error communicating with AI: {str(e)}"

    # ---- Offline fallback ----

    def _fallback_response(self, user_message: str) -> str:
        """Generate simple fallback response when no AI backend is available."""
        msg_lower = user_message.lower()

        if any(word in msg_lower for word in ["hello", "hi", "hey"]):
            return f"Hello! I'm {self.name}, your {self.persona} assistant. How can I help?"
        elif any(word in msg_lower for word in ["how are you", "how're you"]):
            return "I'm doing well, thank you for asking! How about you?"
        elif any(word in msg_lower for word in ["name", "who are you"]):
            return f"I'm {self.name}, a chatbot with a {self.persona} personality."
        elif any(word in msg_lower for word in ["bye", "goodbye", "see you"]):
            return "Goodbye! Feel free to come back anytime!"
        elif "?" in user_message:
            return "That's an interesting question! Configure an AI backend for smarter answers."
        else:
            return f"I received: '{user_message}'. Set up SiliconFlow or Ollama for intelligent responses!"

    # ---- Image generation ----

    def _handle_image_generation(self, command: str) -> str:
        """Handle /aipic command for AI image generation."""
        parts = command.split(maxsplit=1)
        if len(parts) > 1:
            description = parts[1].lstrip(":").strip()
        elif ":" in command:
            description = command.split(":", 1)[1].strip()
        else:
            description = "a beautiful scene"

        print(f"[BOT] Image generation requested: '{description}'")

        try:
            image_path = generate_image(description)
            return (
                f"🎨 AI Image Generated: '{description}'\n"
                f"Saved to: {image_path}"
            )
        except Exception as e:
            print(f"[BOT] Image generation error: {e}")
            return (
                f"🎨 AI Image Generation Request:\n"
                f"Description: '{description}'\n\n"
                f"[Image generation failed: {e}]"
            )

    # ---- Utility ----

    def clear_history(self):
        """Clear conversation history."""
        self.message_history = []

    def get_context_summary(self) -> str:
        """Get a brief summary of conversation context."""
        if not self.message_history:
            return "No conversation history."
        user_msgs = [m for m in self.message_history if m["role"] == "user"]
        return f"Context: {len(user_msgs)} user messages in history."


# ---- Singleton ----

_bot_instance: Optional[AIBot] = None


def get_bot(persona: str = "helpful") -> AIBot:
    """Get singleton AIBot instance."""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = AIBot(persona=persona)
    return _bot_instance


def reset_bot():
    """Reset the bot singleton (e.g. after persona change)."""
    global _bot_instance
    _bot_instance = None


def reset_bot():
    """Reset bot instance (useful for testing)."""
    global _bot_instance
    _bot_instance = None


if __name__ == "__main__":
    # Test the bot
    bot = AIBot(persona="humorous")
    
    print(f"Ollama Available: {bot.ollama_available}")
    print(f"Persona: {bot.persona}")
    print("-" * 50)
    
    test_messages = [
        "Hello!",
        "What's your name?",
        "Tell me a joke",
        "/aipic: a sunset over mountains"
    ]
    
    for msg in test_messages:
        print(f"\nUser: {msg}")
        response = bot.chat(msg)
        print(f"Bot: {response}")
