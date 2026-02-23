# Agent Fun 🤖

A cheerful conversational AI agent powered by **Mistral 7B** (via Ollama) and live APIs through **MCP (Model Context Protocol)**.

## What it can do

| Say something like... | It will... |
|---|---|
| "Weather in Tokyo" | Fetch live weather |
| "Tell me a joke" | Grab a random joke |
| "Quiz me" | Pull a trivia question |
| "Recommend a book about space" | Search Open Library |
| "Show me a dog" | Fetch a random dog image |

## Requirements

- Python 3.9+
- [Ollama](https://ollama.com) with `mistral:7b` pulled

```bash
pip install mcp ollama requests
ollama pull mistral:7b
```

## Run

```bash
python agent_fun.py
```

## Files

- `agent_fun.py` — agent loop, tool routing, LLM calls
- `server_fun.py` — MCP server with all tool definitions

## License

MIT
