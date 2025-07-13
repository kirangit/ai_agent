import logging
import os
from datetime import datetime
import sys

LOG_BASE_DIR = "logs"

def init_logging():
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_log_dir = os.path.join(LOG_BASE_DIR, timestamp)
    os.makedirs(run_log_dir, exist_ok=True)

    # Force UTF-8 encoding for stdout (fixes Windows console issues)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    # Console logger
    console_handler = logging.StreamHandler(sys.stdout)
#    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    # General debug and info logs
    agent_log_path = os.path.join(run_log_dir, "agent.log")
    # Logs related to OpenAI API calls
    openai_log_path = os.path.join(run_log_dir, "openai.log")
    # Logs related to cnMaestro API calls
    cnmaestro_log_path = os.path.join(run_log_dir, "cnmaestro.log")

    # Optional but recommended before basicConfig
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Root logger (captures all)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(agent_log_path)
        ]
    )

    # Reduce verbosity for noisy third-party libraries
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Separate loggers
    openai_logger = logging.getLogger("openai")
    openai_logger.setLevel(logging.INFO)
    openai_handler = logging.FileHandler(openai_log_path)
    openai_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    openai_logger.addHandler(openai_handler)

    cnmaestro_logger = logging.getLogger("cnmaestro")
    cnmaestro_logger.setLevel(logging.INFO)
    cnmaestro_handler = logging.FileHandler(cnmaestro_log_path)
    cnmaestro_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    cnmaestro_logger.addHandler(cnmaestro_handler)

    agent_logger = logging.getLogger("agent")
    agent_logger.setLevel(logging.INFO)
    agent_handler = logging.FileHandler(agent_log_path)
    agent_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    agent_logger.addHandler(agent_handler)

    # Later after setting up each logger:
    openai_logger.propagate = False
    cnmaestro_logger.propagate = False
    agent_logger.propagate = False

    return {
        "agent": agent_logger,
        "openai": openai_logger,
        "cnmaestro": cnmaestro_logger,
        "run_log_dir": run_log_dir
    }
