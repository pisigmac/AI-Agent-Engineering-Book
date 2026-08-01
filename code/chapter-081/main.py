#!/usr/bin/env python3
import json
from chatbot import ChatBot, MockLLM


def main() -> int:
    bot = ChatBot(llm=MockLLM(), system_prompt="You are Ada.")
    s = bot.new_session()
    r1 = bot.chat(s.session_id, "Hello")
    r2 = bot.chat(s.session_id, "What is 2+2?")
    print(json.dumps({"r1": r1, "r2": r2, "events": len(bot.events.events)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
