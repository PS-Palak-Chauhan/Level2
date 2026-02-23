# agent_fun.py

import asyncio
import json
import re
import sys
from typing import Any, Dict, List, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from ollama import chat


def detect_tool(user: str) -> Optional[Dict[str, Any]]:
    u = user.lower()

    if any(w in u for w in ["weather", "temperature", "forecast"]):
        m = re.search(r"\b(?:in|at|for)\s+([a-zA-Z ]+?)(?:\?|$|\.)", user, re.I)
        city = m.group(1).strip() if m else None
        if city:
            return {"tool": "weather_pipeline", "city": city}

    if any(w in u for w in ["trivia", "quiz", "question", "test me", "challenge"]):
        return {"tool": "trivia", "args": {}}

    if any(w in u for w in ["joke", "funny", "laugh", "humor", "humour"]):
        return {"tool": "random_joke", "args": {}}

    if any(w in u for w in ["dog", "puppy", "doggo", "pup", "woof"]):
        return {"tool": "random_dog", "args": {}}

    if any(w in u for w in ["book", "read", "novel", "recommend", "fiction", "story"]):
        m = re.search(r"\b(?:about|on|topic|genre|like)\s+([a-zA-Z ]+?)(?:\?|$|\.|,)", user, re.I)
        topic = m.group(1).strip() if m else "fiction"
        return {"tool": "book_recs", "args": {"topic": topic, "limit": 3}}

    return None


async def call_tool(session: ClientSession, name: str, args: dict) -> str:
    try:
        result = await asyncio.wait_for(session.call_tool(name, args), timeout=20)
        if result.content:
            return "\n".join(
                b.text if hasattr(b, "text") and isinstance(b.text, str) else str(b)
                for b in result.content
            )
        return str(result.model_dump_json())
    except asyncio.TimeoutError:
        return f"[Error: '{name}' timed out]"
    except Exception as e:
        return f"[Error: {e}]"


def ask_llm(messages: List[Dict[str, str]]) -> str:
    resp = chat(model="mistral:7b", messages=messages, options={"temperature": 0.7})
    return (resp["message"]["content"] or "").strip()


async def agent_loop(session: ClientSession) -> None:
    SYSTEM = (
        "You are a cheerful weekend assistant. "
        "When you receive tool data, present it naturally in plain English — no JSON, no code. "
        "For trivia, show the question and all options clearly, then reveal the answer. "
        "For jokes, just say the joke. "
        "For weather, give a friendly summary. "
        "Keep replies short and warm."
    )
    history: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM}]

    while True:
        sys.stdout.write("You: ")
        sys.stdout.flush()

        try:
            user = sys.stdin.readline().strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user or user.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        decision = detect_tool(user)
        tool_result = None

        if decision:
            tname = decision["tool"]
            if tname == "weather_pipeline":
                city = decision["city"]
                raw = await call_tool(session, "city_to_coords", {"city": city})
                try:
                    coords = json.loads(raw)
                    lat, lon = coords.get("latitude"), coords.get("longitude")
                    if lat and lon:
                        weather = await call_tool(session, "weather_summary",
                                                  {"latitude": lat, "longitude": lon})
                        tool_result = f"Weather for {city}:\n{weather}"
                    else:
                        tool_result = f"Could not find city '{city}'."
                except Exception:
                    tool_result = raw
            else:
                args = decision.get("args", {})
                tool_result = await call_tool(session, tname, args)

        if tool_result:
            prompt = (
                f"User asked: \"{user}\"\n\n"
                f"Tool returned:\n{tool_result}\n\n"
                "Reply to the user naturally in plain English. No JSON or code."
            )
        else:
            prompt = user

        history.append({"role": "user", "content": prompt})

        answer = ask_llm(history)
        sys.stdout.write(f"Agent: {answer}\n\n")
        sys.stdout.flush()

        history.append({"role": "assistant", "content": answer})


async def main() -> None:
    server_path = sys.argv[1] if len(sys.argv) > 1 else "server_fun.py"

    async with AsyncExitStack() as stack:
        stdio = await stack.enter_async_context(
            stdio_client(StdioServerParameters(command="python", args=[server_path]))
        )
        r_in, w_out = stdio
        session = await stack.enter_async_context(ClientSession(r_in, w_out))
        await session.initialize()
        tools = (await session.list_tools()).tools
        tool_index = {t.name: t for t in tools}
        print("Connected tools:", list(tool_index.keys()))
        await agent_loop(session)


if __name__ == "__main__":
    asyncio.run(main())