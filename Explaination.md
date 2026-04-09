# MCP + Ollama: Bridging Local AI with Real-Time Data

## 🎯 Project Summary

This project successfully bridged the gap between an offline, local AI model (Llama 3.2 via Ollama) and real-time internet data (Formula 1 statistics via Fast-F1).

We achieved this using the **Model Context Protocol (MCP)**. Instead of relying on the AI's outdated internal memory, we gave it a "menu" of tools it could use to fetch live data, read the results, and synthesize accurate answers.

### Architecture Overview

The system relies on three interconnected parts:

- **The Server (server.py)**: Holds the data tools
- **The Client (client.py)**: Acts as the translator and conversation manager
- **The AI (Ollama)**: The brain that decides when a tool is needed

---

## 🧩 Core Mechanics & Code Snippets

Instead of looking at the whole file, here are the core engines that make the system work.

### 1. Generating the Tool Schema (Server)

We don't write JSON schemas by hand. By using type hints (`year: int`) and docstrings, the `@mcp.tool()` decorator automatically reads our code and generates the strict rules the AI must follow.

```python
# The Docstring and Type Hints become the JSON Schema
@mcp.tool()
def get_session_results(year: int, event_name: str, session_type: str = 'R') -> str:
    """
    Fetches the final classification results for a specific Formula 1 session.
    """
    # Fetch data, clean it up (removing abbreviations), and return a string
    # ...
```

### 2. The Universal Translation (Client)

Because every AI company formats their tool menus differently, the Client must translate the universal MCP menu into Ollama's specific dialect before the AI can read it.

```python
# Ask the server for the universal MCP menu
mcp_tools = await session.list_tools()

# Rebuild the menu exactly how Ollama likes it
ollama_tools = []
for tool in mcp_tools.tools:
    ollama_tools.append({
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema
        }
    })
```

### 3. The Synthesis Nudge (Client)

Local models get easily confused when handed raw tool data. We use a "Nudge" to act like a user pointing directly at the data, forcing the AI to read it and answer the original question.

```python
# Hand the raw F1 data back to Llama disguised as a strict user command
messages.append({
    "role": "user",
    "content": f"The tool just successfully returned this data:\n{result_text}\n\nBased ONLY on the data above, directly answer my original question: '{user_input}'"
})
```

## Key Takeaways
