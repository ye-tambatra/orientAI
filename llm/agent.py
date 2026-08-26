"""
Conversational agent: a Gemini chat session with memory and tool-calling.

ConversationSession wraps a single Gemini chat (its history is the memory).
ConversationManager keeps one ConversationSession per session_id in memory,
so callers can drive multiple independent conversations by session_id.
"""

from google.genai import types

from llm.client import client, GEMINI_MODEL
from llm.tools import TOOLS

SYSTEM_INSTRUCTION = (
    "Tu es l'assistant d'OrientAI, tu aides les étudiants avec leurs "
    "questions d'orientation scolaire et d'admission. Sois concis et utile. "
    "Si tu ne connais pas la réponse, dis-le plutôt que d'inventer."
)


class ConversationSession:
    """A single ongoing conversation. Memory = the chat's own history."""

    def __init__(self, model: str = GEMINI_MODEL):
        self._chat = client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=TOOLS,
            ),
        )

    def send(self, message: str) -> str:
        """Sends a user message and returns the model's text reply.

        Tool calls the model makes along the way are executed automatically
        by the SDK (automatic function calling) before the final text reply
        is returned.
        """
        response = self._chat.send_message(message)
        return response.text

    @property
    def history(self):
        """The full list of messages (user, model, tool calls) so far."""
        return self._chat.get_history()


class ConversationManager:
    """Keeps one ConversationSession per session_id, in memory."""

    def __init__(self):
        self._sessions: dict[str, ConversationSession] = {}

    def get_or_create(self, session_id: str) -> ConversationSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationSession()
        return self._sessions[session_id]

    def reset(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
