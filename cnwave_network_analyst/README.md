# cnWave Network Analyst AI Agent

This AI Agent helps engineers analyze, troubleshoot, and visualize data from Cambium Networks' cnWave 60 GHz platform using API integrations and natural language interactions.

## Setup

### Prerequisites

* Python 3.9+
* `pip install -r requirements.txt`

### Environment Configuration (`.env` file)

Create a `.env` file in the project's root directory containing the following parameters:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-model-name
CNMAESTRO_CLIENT_ID=your_cnmaestro_client_id
CNMAESTRO_CLIENT_SECRET=your_cnmaestro_client_secret
```

### Explanation of parameters

| Parameter                 | Description                                   |
| ------------------------- | --------------------------------------------- |
| `OPENAI_API_KEY`          | API Key from OpenAI for GPT API interactions. |
| `OPENAI_MODEL`            | The GPT model to use (e.g., `gpt-4-turbo`).   |
| `CNMAESTRO_CLIENT_ID`     | Client ID from Cambium's cnMaestro API.       |
| `CNMAESTRO_CLIENT_SECRET` | Client Secret from Cambium's cnMaestro API.   |

## Project Structure

```
cnwave_agent/
│
├── agent.py                     # Main entry point for running the AI agent
├── requirements.txt             # Python dependencies
├── system_prompt.txt            # GPT system-level prompt configuration
├── functions.yaml               # YAML definitions of GPT-accessible functions
│
├── tools/
│   ├── __init__.py
│   ├── cnmaestro.py             # Handles Cambium Networks cnMaestro API interactions
│   ├── weather.py               # Retrieves weather data for analysis
│   └── tool_router.py           # Routes GPT-initiated function calls
│
├── utils/
│   ├── __init__.py
│   ├── logger_setup.py          # Sets up logging
│   ├── map.py                   # Generates network visualizations (maps)
│   └── message_history_utils.py # Manages GPT message history
│
├── tests/
│   └── test_tools.py            # Contains tests for API and tool functions
│
├── logs/                        # Stores runtime logs
└── maps/                        # Stores generated HTML network visualizations
```

## Running the AI Agent

```bash
python agent.py
```

You're now ready to interact with the cnWave AI Agent!
