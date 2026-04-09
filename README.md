# MCP_stdio

A small **Formula 1 MCP (Model Context Protocol) project** that connects a local Ollama model to live Formula 1 data.

- `server.py` exposes F1 data tools over MCP
- `client.py` launches the MCP server over stdio and lets an Ollama model decide when to call those tools
- `Explaination.md` contains a more detailed architecture walk-through

## What this project does

This project lets you ask questions like:

- race results for a specific Grand Prix
- season championship standings

The client sends your prompt to Ollama, Ollama chooses a tool if needed, the MCP server fetches the data using FastF1 / Ergast, and the client feeds the result back to the model for a final answer.

## Features

- MCP server with Formula 1 data tools
- Local LLM orchestration with Ollama
- FastF1 cache for faster repeated requests
- Logging for both server and client

## Project structure

```text
MCP_stdio/
├── server.py            # MCP server with F1 tools
├── client.py            # Interactive Ollama client
├── requirements.txt     # Python dependencies
├── Explaination.md      # Detailed explanation of the architecture
├── f1_server.log        # Server logs
└── client.log           # Client logs
```

## Prerequisites

- Python 3.10+ recommended
- [Ollama](https://ollama.com/) installed and running locally
- The Ollama model used by the client:
  - `qwen2.5:7b-instruct`
- Internet access for live Formula 1 data

If needed, pull the model first:

```bash
ollama pull qwen2.5:7b-instruct
```

## Installation

From the project folder:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If your system uses `python3` instead of `python`, use that consistently for creating the virtual environment.

## Running the project

### 1) Run the MCP server directly

This starts the server over stdio and waits for an MCP client to connect:

```bash
python server.py
```

### 2) Quick server test mode

`server.py` includes a simple test mode that fetches a sample race result without the client:

```bash
python server.py test
```

### 3) Run the interactive client

This launches the MCP server internally, connects to it, and opens the chat loop:

```bash
python client.py
```

Type `exit` or `quit` to close the chat.

> Note: `client.py` starts the server with `command="python"`. If your macOS setup only has `python3`, either make sure `python` points to Python 3 in your environment or update that line in `client.py`.

## Available MCP tools

### `get_race_results(year, event_name, session_type='R')`

Returns the classified finishing order for a specific session.

Examples:

- `get_race_results(2025, "Chinese Grand Prix", "R")`
- `get_race_results(2024, "Monza", "R")`
- `get_race_results(2023, "Italian Grand Prix", "Q")`

### `get_season_standings(year)`

Returns the Formula 1 World Championship driver standings for the full season.

Example:

- `get_season_standings(2025)`

## Logging and cache

### Logs

- `f1_server.log` records server-side activity and fetched data summaries
- `client.log` records client discovery, tool translation, and Ollama tool usage

### Cache

FastF1 uses `f1_cache/` to store downloaded session data so repeated requests are faster.

You can safely leave the cache in place. If it grows too large, you can delete it and FastF1 will rebuild it on demand.

## Example prompts

Try questions like:

- "Show me the 2025 Chinese Grand Prix race results"
- "Who won the 2025 championship?"
- "Give me the standings for 2024"
- "What was the result at Monza in 2023?"

## Troubleshooting

### `python: command not found`

Your system may only expose `python3`. Use a Python 3 virtual environment and ensure `python` resolves correctly, or update `client.py` to call `python3`.

### Ollama cannot find the model

Make sure Ollama is running and the model is installed:

```bash
ollama list
ollama pull qwen2.5:7b-instruct
```

### FastF1 data fetch is slow the first time

The first request for a session can take longer because FastF1 is downloading and caching live data. Subsequent requests should be faster.

### MCP tool call errors

If you see tool-call or session errors, confirm that:

- dependencies are installed from `requirements.txt`
- Ollama is running locally
- the client and server are being run from the project directory

## Learn more

For a deeper explanation of the architecture and design choices, see `Explaination.md`.

