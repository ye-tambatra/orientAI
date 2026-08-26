"""
Manual test REPL for the conversational AI: memory + tool-calling.

Run from the repo root with:
    python -m llm.demo_cli

Try:
  - Multi-turn context, e.g. "My name is Jenny" then "What's my name?"
    -> proves conversation memory works.
  - "What time is it right now?"
    -> proves tool-calling works (calls get_current_time).
  - "Echo back: hello world"
    -> proves tool-calling with arguments works (calls echo).
Type "exit" or "quit" to stop.
"""

from llm.agent import ConversationManager

if __name__ == "__main__":
    manager = ConversationManager()
    session = manager.get_or_create("cli")

    print("OrientAI conversational demo. Type 'exit' to quit.\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue

        reply, sources, steps = session.send(user_input)
        print(f"AI: {reply}")
        if steps:
            print("Steps:")
            for step in steps:
                print(f"  - {step['tool']}({step['args']})")
        if sources:
            print("Sources:")
            for source in sources:
                print(f"  - {source['title']} ({source['file']})")
        print()
