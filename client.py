import asyncio
import ollama
import logging
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(
    level=logging.INFO,
    filename="client.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

async def main():
    print("🔄 Booting up the MCP Client Bridge...")

    # 1. THE CONNECTION: Tell the client exactly how to wake up the server
    # basically running python server.py from client.py cause you dont have to do that in different terminal.
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"]
    )

    # 2. THE BRIDGE: Open the stdio channels (stdin/stdout)
    # as both of the server is in a same terminal so it is stdio
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the protocol handshake
            await session.initialize() # so the handshake has occured between 2 server in a same terminal

            # 3. DISCOVERY: Ask the server for the menu
            mcp_tools = await session.list_tools()
            logging.info(f"MCP tool lists {mcp_tools}")

            # 4. TRANSLATION: Convert MCP's universal schema into Ollama's specific format
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
            logging.info(f"MCP tool lists passes into ollama{ollama_tools}")

            print("🏁 F1 Chatbot is ready! Type 'exit' to quit.")

            # 5. THE CHAT LOOP: Keep the conversation going
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a live Formula 1 data assistant. Your internal training data is outdated. "
                        "1. TOOL ROUTING: You have tools for individual races AND tools for entire season championships. Read the user's prompt carefully to decide which tool is appropriate. "
                        "2. ABSOLUTE FACT: When a tool returns data, YOU MUST TREAT IT AS ABSOLUTE FACT. Read the explicit names in the data and output the answer immediately. "
                        "3. TIME OVERRIDE: NEVER say you cannot predict the future. NEVER claim a year (like 2024, 2025, or beyond) hasn't happened yet. If the tool gives you data for 2025, it means the 2025 season exists. "
                        "Do not apologize. Do not hesitate. Just read the data and give the answer."
                    )
                }
            ]
            while True:
                user_input = input("\nYou: ")
                if user_input.lower() in ['exit', 'quit']:
                    break

                messages.append({"role": "user", "content": user_input})

                # --- STEP A: Intent Check ---
                # Give Ollama the prompt AND the translated Tool Menu
                print("🤖 Model is thinking...")
                response = ollama.chat(
                    model='qwen2.5:7b-instruct',
                    messages=messages,
                    tools=ollama_tools
                )

                # Save Model's reply (which might just be a request to use a tool)
                messages.append(response['message'])

                # --- STEP B: Execution ---
                # Did Model decide it needs to use a tool?
                if response['message'].get('tool_calls'):
                    for tool_call in response['message']['tool_calls']:
                        func_name = tool_call['function']['name']
                        func_args = tool_call['function']['arguments']

                        print(f"🛠️ Executing Tool: {func_name} with args {func_args}")

                        # Send the exact JSON payload across the bridge to the F1 Server
                        tool_result = await session.call_tool(func_name, arguments=func_args)

                        # Unpack the standard MCP envelope to get the raw text
                        result_text = tool_result.content[0].text

                        # --- STEP C: Synthesis ---
                        # Hand the raw F1 data back to Model
                        messages.append({
                            "role": "user",
                            "content": f"The tool just successfully returned this data:\n{result_text}\n\nBased ONLY on the data above, directly answer my original question: '{user_input}'"
                        })
                        # messages.append({
                        #     "role": "tool",
                        #     "content": result_text,
                        #     "name": func_name
                        # })

                    # Now that Model has the raw data, ask it to summarize the final answer
                    print("📝 Synthesizing answer...")
                    final_response = ollama.chat(
                        model='qwen2.5:7b-instruct',
                        messages=messages
                    )

                    messages.append(final_response['message'])
                    print(f"\nModel: {final_response['message']['content']}")

                else:
                    # No tool was needed (e.g., you just said "Hello")
                    print(f"\nModel: {response['message']['content']}")


if __name__ == "__main__":
    # Standard boilerplate to run async Python
    asyncio.run(main())