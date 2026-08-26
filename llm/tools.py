"""
Tools the conversational AI can call.

Each tool is a plain Python function with type hints and a docstring — the
google-genai SDK reads these to auto-generate the function-calling schema, so
no manual JSON schema is needed. Add new tools by writing a function here and
appending it to TOOLS.
"""

import datetime


def get_current_time() -> str:
    """Returns the current date and time.

    Use this whenever the user asks what the current date, day, or time is.
    """
    return datetime.datetime.now().isoformat()


def echo(text: str) -> str:
    """Repeats the given text back verbatim.

    Use this only when the user explicitly asks you to echo/repeat something.
    """
    return text


TOOLS = [get_current_time, echo]
