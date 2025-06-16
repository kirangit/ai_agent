import json
from openai import OpenAI
import requests
from pathlib import Path
import yaml
from function_router import route_function_call
import re
import logging
from datetime import datetime
import os

# Ensure the logs/ directory exists
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Create unique log filename with timestamp
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = os.path.join(log_dir, f"support_log_{timestamp}.log")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename=log_filename,
    filemode='w'
)

logging.info("=== New support log started ===")


def format_cli_output(text):
    # Convert Markdown-style bold (**bold**) to ANSI bold
    return re.sub(r"\*\*(.*?)\*\*", r"\033[1m\1\033[0m", text)

# Constants for GPT-4o-mini pricing (as of June 2024)
INPUT_COST_PER_MILLION = 0.15     # USD
OUTPUT_COST_PER_MILLION = 0.60    # USD

total_prompt_tokens = 0
total_completion_tokens = 0

def estimate_gpt_cost(prompt_tokens, completion_tokens):
    input_cost = (prompt_tokens / 1_000_000) * INPUT_COST_PER_MILLION
    output_cost = (completion_tokens / 1_000_000) * OUTPUT_COST_PER_MILLION
    return round(input_cost + output_cost, 6)

def print_total_conversation_cost():
    #total_tokens = total_prompt_tokens + total_completion_tokens
    estimated_cost = estimate_gpt_cost(total_prompt_tokens, total_completion_tokens)
    logging.info("\n📊 Token Usage Summary:")
    logging.info(f"  📝 Input tokens  used: {total_prompt_tokens}")
    logging.info(f"  🧠 Output tokens used: {total_completion_tokens}")
    #print(f"  💰 Total tokens  used: {total_tokens}")
    logging.info(f"  💰 Estimated cost (USD): ${estimated_cost}")

def print_one_gpt_request_cost(response):
    logging.info(f"  📝 Input tokens  used: {response.usage.prompt_tokens}")
    logging.info(f"  🧠 Output tokens used: {response.usage.completion_tokens}")
    cost  = estimate_gpt_cost(response.usage.prompt_tokens, response.usage.completion_tokens)
    logging.info(f"  💰 Estimated cost (USD): ${cost}")

def print_gpt_response(response):
    logging.info("\n\n\n")  # Three blank lines before
    logging.info(json.dumps(response.model_dump(), indent=2))
    #print_one_gpt_request_cost(response)
    logging.info("\n\n\n")  # Three blank lines after

def track_token_usage(usage):
    global total_prompt_tokens, total_completion_tokens
    total_prompt_tokens += usage.prompt_tokens
    total_completion_tokens += usage.completion_tokens

def load_initial_messages():
    with open("system_prompt.txt", "r", encoding="utf-8") as f:
        system_prompt = f.read().strip()
    return [{"role": "system", "content": system_prompt}]

model="gpt-4o-mini"

# Load OpenAI key
with open("credentials/openai.json") as f:
    openai_key = json.load(f)["api_key"]
    client = OpenAI(api_key=openai_key)

# Load YAML
with open("cli_agent_functions.yaml") as f:
    tools = yaml.safe_load(f)

# Start CLI loop
print("👋 Welcome to MDU Agent CLI. Type 'exit' to quit.")
messages = load_initial_messages()

while True:
    user_input = input("You: ").strip()
    if user_input.lower() in ("exit", "quit"):
        print_total_conversation_cost()
        break

    # Step 1: Append user input
    messages.append({"role": "user", "content": user_input})

    # Step 2: First GPT response
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    print_gpt_response(response)
    track_token_usage(response.usage)

    assistant_message = response.choices[0].message
    messages.append(assistant_message)

    # Step 3: Print assistant message if present
    if assistant_message.content:
        print(f"\n🤖 GPT: {format_cli_output(assistant_message.content)}")
        #print(f"\n🤖 GPT: {assistant_message.content}")

    # Step 4: Handle tool calls
    while assistant_message.tool_calls:
        for call in assistant_message.tool_calls:
            function_name = call.function.name
            arguments = json.loads(call.function.arguments)

            result = route_function_call(function_name, arguments)
            logging.info(f"🤖 {result}")

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "name": function_name,
                "content": str(result)
            })

        # Step 5: Ask GPT again after tool results
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        print_gpt_response(response)
        track_token_usage(response.usage)

        assistant_message = response.choices[0].message
        messages.append(assistant_message)

        # Step 6: Print next assistant reply (if any)
        if assistant_message.content:
            print(f"\n🤖 GPT: {format_cli_output(assistant_message.content)}")
            #print(f"\n🤖 GPT: {assistant_message.content}")

