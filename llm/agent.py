"""
Conversational agent: a Gemini chat session with memory and tool-calling.

ConversationSession wraps a single Gemini chat (its history is the memory).
ConversationManager keeps one ConversationSession per session_id in memory,
so callers can drive multiple independent conversations by session_id.
"""

import uuid

from google.genai import types

from llm.client import client, GEMINI_MODEL
from llm.sources import RAG_TOOL_NAMES, parse_sources
from llm.tools import TOOLS

SYSTEM_INSTRUCTION = (
    "Tu es l'assistant d'OrientAI, tu aides les étudiants avec leurs "
    "questions d'orientation scolaire et d'admission. Sois concis et utile. "
    "Si tu ne connais pas la réponse, dis-le plutôt que d'inventer. "
    "Distingue toujours, dans tes réponses, ce qui provient : (1) du modèle "
    "de Machine Learning (outils analyser_profil_ml, calculer_score_adequation, "
    "identifier_points_forts, expliquer_recommandation_ml — un résultat "
    "statistique, jamais une décision officielle), (2) des documents "
    "pédagogiques (outils de recherche "
    "documentaire, à citer), et (3) de ton propre raisonnement. Ne fonde "
    "jamais une recommandation sur un trait de personnalité, une "
    "caractéristique personnelle sensible (sexe, âge, origine...) ou une "
    "inférence psychologique — utilise uniquement ce que l'utilisateur "
    "déclare explicitement comme matières, compétences ou centres d'intérêt. "
    "Avant d'appeler analyser_profil_ml ou calculer_score_adequation, "
    "recueille si possible, en plus des matières/compétences/intérêts, la "
    "série de bac (ou envisagée) et le type d'environnement de travail "
    "recherché (bureau, atelier, laboratoire, terrain, contact clientèle) — "
    "ce sont des signaux que le modèle utilise réellement et qui affinent "
    "nettement la recommandation. Ne bloque cependant pas la première "
    "estimation si l'utilisateur ne les connaît pas encore. Si l'utilisateur "
    "demande pourquoi le modèle recommande un parcours/domaine précis, "
    "appelle expliquer_recommandation_ml et cite ses chiffres de "
    "contribution tels quels plutôt que d'inventer une justification. "
    "Quand tu appelles demarrer_questionnaire_orientation, précise le "
    "paramètre statut (lyceen / etudiant / professionnel) dès que tu le "
    "connais — cela adapte le temps des verbes et les options proposées "
    "(ex: ne pas demander une 'compétence en gestion de projet' à un "
    "lycéen, ne pas demander la série de bac au présent à quelqu'un qui "
    "l'a déjà passée). Par défaut, si le statut n'est pas mentionné, laisse "
    "la valeur par défaut 'lyceen'."
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

    def send(
        self, message: str
    ) -> tuple[str, list[dict[str, str | None]], list[dict]]:
        """Sends a user message, returns (reply_text, sources, steps).

        Tool calls the model makes along the way are executed automatically
        by the SDK (automatic function calling) before the final text reply
        is returned.
        - `sources` lists the unique RAG citations (source_id, file, title,
          url) pulled in by any RAG-backed tool during this turn.
        - `steps` lists every tool call made this turn (id, tool, args,
          result), in order, for observability.
        Both are kept separate from the reply text so callers can display
        them apart from the model's prose.
        """
        history_before = len(self._chat.get_history())
        response = self._chat.send_message(message)
        new_history = self._chat.get_history()[history_before:]
        return (
            response.text,
            self._extract_sources(new_history),
            self._extract_steps(new_history),
        )

    def _extract_sources(self, new_history: list) -> list[dict[str, str | None]]:
        sources: dict[str, dict[str, str | None]] = {}
        for content in new_history:
            for part in content.parts or []:
                function_response = getattr(part, "function_response", None)
                if function_response is None or function_response.name not in RAG_TOOL_NAMES:
                    continue
                result = (function_response.response or {}).get("result")
                if isinstance(result, str):
                    for source in parse_sources(result):
                        sources[source["source_id"]] = source
        return list(sources.values())

    def _extract_steps(self, new_history: list) -> list[dict]:
        steps: list[dict] = []
        pending_call: dict | None = None
        for content in new_history:
            for part in content.parts or []:
                function_call = getattr(part, "function_call", None)
                if function_call is not None:
                    pending_call = {
                        "tool": function_call.name,
                        "args": dict(function_call.args or {}),
                    }
                    continue
                function_response = getattr(part, "function_response", None)
                if function_response is not None and pending_call is not None:
                    result = (function_response.response or {}).get("result")
                    steps.append(
                        {
                            "id": str(uuid.uuid4()),
                            "tool": pending_call["tool"],
                            "args": pending_call["args"],
                            "result": result if isinstance(result, str) else str(result),
                        }
                    )
                    pending_call = None
        return steps

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
