import os
import openai
import json
from dotenv import load_dotenv
from tools.tool_router import route_tool_call
from utils.logger_setup import init_logging
from datetime import datetime
from utils.message_history import maybe_summarise 
import yaml
from openai import OpenAI
import re

# Load environment variables
load_dotenv()
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
openai.api_key = OPENAI_API_KEY

#GPT tokens
total_prompt_tokens = 0
total_completion_tokens = 0

# Initialize logging and get paths
loggers = init_logging()
agent_logger = loggers["agent"]
openai_logger = loggers["openai"]
cnmaestro_logger = loggers["cnmaestro"]
run_log_dir = loggers["run_log_dir"]

agent_logger.info("Starting ChatCompletion-based cnWave Agent")

def track_token_usage(usage):
    global total_prompt_tokens, total_completion_tokens
    total_prompt_tokens += usage.prompt_tokens
    total_completion_tokens += usage.completion_tokens

def format_cli_output(text):
    # Convert Markdown-style bold (**bold**) to ANSI bold
    return re.sub(r"\*\*(.*?)\*\*", r"\033[1m\1\033[0m", text)

# Load system prompt
with open("system_prompt.txt", encoding="utf-8") as f:
    system_prompt = f.read()

# Message history and context state
messages = [
    {"role": "system", "content": system_prompt}
]

MAX_HISTORY_LENGTH = 10

session_state = {
    "selected_network_id": None
}

def load_function_list_from_yaml(yaml_path: str):
    with open(yaml_path, "r") as f:
        parsed = yaml.safe_load(f)

    function_list = []
    for item in parsed:
        if item.get("type") == "function":
            function_list.append({
                "type": "function",
                "function": item["function"]
            })
    return function_list

tools = load_function_list_from_yaml("functions.yaml")

client = OpenAI(api_key=OPENAI_API_KEY)

def chat():
    global messages
    print("\n💬 cnWave Network Analyst Agent is ready. Type 'exit' to quit.\n")
    while True:
        user_input = input("🧑 You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print(f"  Input tokens  used: {total_prompt_tokens}")
            print(f"  Output tokens used: {total_completion_tokens}")
            openai_logger.info(f"  Input tokens  used: {total_prompt_tokens}")
            openai_logger.info(f"  Output tokens used: {total_completion_tokens}")
            break

        # Step 1: Append user input
        messages.append({"role": "user", "content": user_input})

        # Step 2: First GPT response
        messages = maybe_summarise(messages)
        openai_logger.info(f"OpenAI request started at {datetime.now().isoformat()}")
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=tools,
            tool_choice = "auto"
        )
        openai_logger.info(f"OpenAI response ID: {response.id}")

        track_token_usage(response.usage)
        openai_logger.info(json.dumps(response.model_dump(), indent=2))
        assistant_message = response.choices[0].message
        messages.append(assistant_message)

        # Step 3: Print assistant message if present
        if assistant_message.content:
            print(f"\n🤖 GPT: {format_cli_output(assistant_message.content)}")
            agent_logger.info(f"Assistant response: {assistant_message.content}")

        # Step 4: Handle tool calls
        while assistant_message.tool_calls:
            for call in assistant_message.tool_calls:
                function_name = call.function.name

                result = route_tool_call(call)
                cnmaestro_logger.info(f"Tool result: {result}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": function_name,
                    "content": str(result)
                })

            # Step 5: Ask GPT again after tool results
            openai_logger.info(f"OpenAI request started at {datetime.now().isoformat()}")
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=tools,
                tool_choice = "auto"
            )
            openai_logger.info(f"OpenAI response ID: {response.id}")

            track_token_usage(response.usage)
            openai_logger.info(json.dumps(response.model_dump(), indent=2))
            assistant_message = response.choices[0].message
            messages.append(assistant_message)

            # Step 6: Print next assistant reply (if any)
            if assistant_message.content:
                print(f"\n🤖 GPT: {format_cli_output(assistant_message.content)}")
                agent_logger.info(f"Assistant response: {assistant_message.content}")

if __name__ == "__main__":
    chat()
