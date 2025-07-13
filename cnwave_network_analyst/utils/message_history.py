
"""
message_history.py
----------------------------------
A lightweight replacement for LangChain's ConversationSummaryBufferMemory
that works directly with OpenAI's chat.completions API.

Features
--------
* Keeps the system prompt.
* Automatically summarises older turns once the prompt exceeds
  MAX_PROMPT_TOKENS tokens.
* Preserves the last RECENT_TURNS turns verbatim (including tool messages).
* Prevents orphaned tool messages (drops whole turns when summarising).

Environment variables
---------------------
MAX_PROMPT_TOKENS - token cap before summarisation (default 15000)
RECENT_TURNS      - number of recent turns to keep raw (default 3)
SUMMARY_MAX_TOK   - max tokens in the recap (default 120)
SUMMARY_MODEL     - model used for summarising (default gpt-3.5-turbo)
OPENAI_API_KEY    - your OpenAI key
"""

from __future__ import annotations
import os, logging
from typing import List, Any

# ---------------------- CONFIG ----------------------
MAX_PROMPT_TOKENS = int(os.getenv("MAX_PROMPT_TOKENS", "15000"))
RECENT_TURNS      = int(os.getenv("RECENT_TURNS", "3"))
SUMMARY_MAX_TOK   = int(os.getenv("SUMMARY_MAX_TOK", "500"))
SUMMARY_MODEL     = os.getenv("SUMMARY_MODEL", "gpt-3.5-turbo")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")

# ---------------------- TOKEN COUNTER ---------------
try:
    import tiktoken
except ModuleNotFoundError:  # fallback: rough estimate
    tiktoken = None

_enc_cache = {}

# ---------------------- LOGGER ----------------------
# Re-use the “agent” logger that main.py registers.
# If it doesn’t exist yet, fallback to root logger.
_logger = logging.getLogger("agent")
if not _logger.handlers:
    _logger = logging.getLogger(__name__)

def _encoding(model: str):
    if model in _enc_cache:
        return _enc_cache[model]
    if tiktoken:
        try:
            enc = tiktoken.encoding_for_model(model)
        except KeyError:
            enc = tiktoken.get_encoding("cl100k_base")
        _enc_cache[model] = enc
        return enc
    # simple fallback
    _enc_cache[model] = None
    return None

def _count_tokens(text, model: str = "gpt-3.5-turbo") -> int:
    """Return token count for any content; safely handles non‑string or None."""
    if text is None:
        return 0
    if not isinstance(text, str):
        text = str(text)
    enc = _encoding(model)
    if enc:
        return len(enc.encode(text))
    return max(1, len(text) // 4)

def tokens_in_messages(msgs: List[Any]) -> int:
    return sum(_count_tokens(
        str(msg["content"] if isinstance(msg, dict) else getattr(msg, 'content', ''))
    ) for msg in msgs)

# ---------------------- ROLE ACCESS -----------------
def role_of(msg: Any) -> str | None:
    return msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)

# ---------------------- TURN SPLITTER ---------------
def split_into_turns(history: List[Any]) -> List[List[Any]]:
    turns, current = [], []
    for m in history:
        if role_of(m) == "user" and current:
            turns.append(current)
            current = []
        current.append(m)
    if current:
        turns.append(current)
    return turns

# ---------------------- CHAT -> PLAIN TEXT ----------
def render_chat(turns: List[List[Any]]) -> str:
    lines = []
    for turn in turns:
        for m in turn:
            role = role_of(m).upper()
            raw = m["content"] if isinstance(m, dict) else getattr(m, "content", "")
            content = str(raw).strip() if raw is not None else ""
            lines.append(f"{role}: {content}")
    return "\n".join(lines)

# ---------------------- LLM SUMMARY -----------------
try:
    from openai import OpenAI
    _client = OpenAI(api_key=OPENAI_API_KEY)
except ModuleNotFoundError:
    _client = None  # will error if used without openai package

def call_llm_summary(transcript: str, max_tokens: int = SUMMARY_MAX_TOK) -> str:
    """Return a compact summary string."""
    if not transcript.strip():
        return ""
    if _client is None:
        raise RuntimeError("openai package not available.")
    resp = _client.chat.completions.create(
        model       = SUMMARY_MODEL,
        messages    = [
            {"role":"system","content":(
                "You are an assistant that writes concise summaries. "
                "ALWAYS begin with: Active network: <name>. " 
                f"Summarise the following chat in ≤{max_tokens} tokens, " 
                "highlighting key decisions, configurations and open issues."
            )},
            {"role":"user","content": transcript}
        ],
        temperature = 0.3,
        max_tokens  = max_tokens + 40
    )
    return resp.choices[0].message.content.strip()[:max_tokens]

# ---------------------- MAIN ENTRY ------------------
def maybe_summarise(messages: List[Any]) -> List[Any]:
    """Rebase conversation when it grows beyond MAX_PROMPT_TOKENS."""
    total_tokens = tokens_in_messages(messages)
    if total_tokens <= MAX_PROMPT_TOKENS:
        return messages  # within budget

    _logger.info(
        f"[memory] Prompt {total_tokens} tokens > "
        f"limit {MAX_PROMPT_TOKENS}. Triggering summarisation..."
    )

    system_prompt = messages[0]
    turns = split_into_turns(messages[1:])  # exclude system

    #print(f"Turns:{len(turns)}")

    recent_turns = turns[-RECENT_TURNS:] if RECENT_TURNS else []
    older_turns  = turns[:-RECENT_TURNS] if RECENT_TURNS else turns

    transcript   = render_chat(older_turns)
    summary_text = call_llm_summary(transcript)

    _logger.info(
        "[memory] Summary ▶ "
        + summary_text.replace("\n", " ")[:500]    # 500-char preview
        + ("…" if len(summary_text) > 500 else "")
    )

    tokens_after = tokens_in_messages(
        [system_prompt,
         {"role":"assistant","content": summary_text},
         *[m for turn in recent_turns for m in turn]]
    )
    _logger.info(
        f"[memory] Summarised {len(older_turns)} old turn(s) "
        f"→ prompt now {tokens_after} tokens."
    )

    #print(f"Summary: {summary_text}")
    rebased = [system_prompt,
               {"role":"assistant", "content": summary_text}]
    for t in recent_turns:
        rebased.extend(t)
    return rebased
