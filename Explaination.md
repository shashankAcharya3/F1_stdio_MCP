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

---

## 🧠 Q&A: Deep Dive into Your Questions

Here is a record of the specific doubts you had during the build and the architectural concepts they revealed.

### Q: What about the line `if __name__ == "__main__":`?

**A:** This is a safety gate in Python. A Python file can be run directly (like clicking an app) or imported by another script (like borrowing a library).

This line means: *"Only run the code below this line if the user launched this exact file directly from the terminal."* It prevents your client from accidentally auto-executing if another script decides to import it.

---

### Q: How will the response be when an MCP gives the tool list?

**A:** When the client calls `await session.list_tools()`, the server replies with a highly structured JSON object that defines the exact data types the tool demands. It looks like this:

```json
{
  "tools": [
    {
      "name": "get_session_results",
      "description": "Fetches final classification results...",
      "inputSchema": {
        "type": "object",
        "properties": {
          "year": { "type": "integer" },
          "event_name": { "type": "string" }
        }
      }
    }
  ]
}
```

---

### Q: What kind of message will Ollama send to decide it needs a tool? How does it look?

**A:** When Llama decides to use a tool, it completely stops talking to the human. The `content` field is left empty, and it generates a special `tool_calls` array meant only for your Python script to read.

```json
{
  "message": {
    "role": "assistant",
    "content": "", 
    "tool_calls": [ 
      {
        "function": {
          "name": "get_session_results",
          "arguments": { "year": 2024, "event_name": "Monza" }
        }
      }
    ]
  }
}
```

---

### Q: How does `response['message'].get('tool_calls')` work?

**A:** If Llama just says "Hello!", the `tool_calls` array doesn't exist in the JSON. If you try to force Python to read it using standard brackets (`response['message']['tool_calls']`), Python will crash with a `KeyError`.

Using `.get('tool_calls')` is the safe way to look inside the dictionary. It means: *"Check if 'tool_calls' exists. If it does, give it to me. If it doesn't, just silently ignore it without crashing."*

---

### Q: Is the response different for every LLM?

**A:** Yes! OpenAI (ChatGPT), Anthropic (Claude), and Ollama all expect tool menus and tool calls to be formatted in slightly different JSON structures. This is the exact reason the **Model Context Protocol** was invented. It provides a universal standard so you only write your Server once, and your Client script handles the translation for whichever LLM you happen to be using today.

---

### Q: From which point is the session initialized, and what does it mean? Are we taking the session as server.py?

**A:** The session is **NOT** the server.py script. Think of server.py as a Librarian in another room. Think of the stdio connection as a tin-can telephone string connecting your rooms. The session is the actual conversation happening over that string.

When we run `await session.initialize()`, we are performing a formal **Handshake**. The client says, "I speak MCP Version 1.0, are you there?" and the server replies, "Yes, I also speak Version 1.0, let's begin." 

We use `session.list_tools()` because the session object handles all the invisible networking paperwork (formatting JSON, assigning message IDs, waiting for replies) so we don't have to write hundreds of lines of connection code ourselves.

---

## Key Takeaways

✅ MCP provides a universal standard for LLM tool integration  
✅ Type hints and docstrings auto-generate tool schemas  
✅ Client acts as a translator between MCP and LLM-specific formats  
✅ Local models need data "nudges" to process tool results effectively  
✅ Session management handles all the networking complexity