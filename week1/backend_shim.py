"""
Week 1 shared backend: Ollama-compatible chat() over an OpenAI-compatible endpoint.

The course scripts call `from ollama import chat`. On this machine the graded
models (mistral-nemo:12b / llama3.1:8b) are not pulled into Ollama; instead a
local vLLM server (OpenAI-compatible) serves `qwen38`. This shim installs a
`chat` symbol that mimics the ollama-python client API surface used by the
week1 scripts (response.message.content) while routing to the vLLM endpoint.

Set WEEK1_BACKEND=ollama to use real Ollama instead (default: vllm).
Set WEEK1_MODEL_MAP_JSON to override the model-name mapping.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

BACKEND = os.environ.get("WEEK1_BACKEND", "vllm").lower()

# Course model name -> backend model name
_DEFAULT_MAP = {
    "mistral-nemo:12b": os.environ.get("VLLM_MODEL_NEMO", "qwen38"),
    "llama3.1:8b": os.environ.get("VLLM_MODEL_LLAMA", "qwen38"),
}
try:
    MODEL_MAP: Dict[str, str] = json.loads(
        os.environ.get("WEEK1_MODEL_MAP_JSON", "") or "{}"
    ) or dict(_DEFAULT_MAP)
except json.JSONDecodeError:
    MODEL_MAP = dict(_DEFAULT_MAP)


class _Message:
    def __init__(self, content: str):
        self.content = content


class _ChatResponse:
    def __init__(self, content: str):
        self.message = _Message(content)


def _norm_options(options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    opts = dict(options or {})
    # vLLM/OpenAI uses 0..2 scale, same semantic as ollama temperature
    return opts


def _chat_vllm(
    model: str, messages: List[Dict[str, str]], options: Optional[Dict[str, Any]] = None
) -> _ChatResponse:
    from openai import OpenAI

    base_url = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:16869/v1")
    api_key = os.environ.get("OPENAI_API_KEY", "EMPTY")
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=600.0)
    resolved = MODEL_MAP.get(model, model)
    opts = _norm_options(options)
    kwargs: Dict[str, Any] = {
        "model": resolved,
        "messages": messages,
    }
    if "temperature" in opts:
        kwargs["temperature"] = float(opts["temperature"])
    # Qwen3 family: server default disables thinking; re-enable per request so the
    # model can do chain-of-thought internally before answering (see week1 CoT task).
    if os.environ.get("WEEK1_ENABLE_THINKING", "1") == "1":
        kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": True}}
    resp = client.chat.completions.create(**kwargs)
    content = resp.choices[0].message.content or ""
    return _ChatResponse(content)


def _chat_ollama(
    model: str, messages: List[Dict[str, str]], options: Optional[Dict[str, Any]] = None
) -> _ChatResponse:
    from ollama import chat as _ollama_chat

    resp = _ollama_chat(model=model, messages=messages, options=options or {})
    return _ChatResponse(resp.message.content)


def chat(
    model: str, messages: List[Dict[str, str]], options: Optional[Dict[str, Any]] = None
) -> _ChatResponse:
    """Drop-in replacement for ollama.chat used across week1 scripts."""
    if BACKEND == "ollama":
        return _chat_ollama(model, messages, options)
    return _chat_vllm(model, messages, options)
