# Week 1 — Prompting Techniques (Solutions)

All six prompting-technique exercises completed. Each script's `TODO`s are resolved
(see `YOUR_SYSTEM_PROMPT` / `YOUR_REFLEXION_PROMPT` / `YOUR_CONTEXT_PROVIDER` /
`your_build_reflexion_context` in each file) and every harness prints `SUCCESS`.

## Techniques

| File | Technique | Result |
|---|---|---|
| `k_shot_prompting.py` | K-shot (3 examples of word reversal) | SUCCESS |
| `chain_of_thought.py` | Chain-of-thought (modular exponentiation 3^12345 mod 100 = 43) | SUCCESS (run 1) |
| `self_consistency_prompting.py` | Self-consistency (5 samples @ T=1, majority vote) | SUCCESS — 5/5 votes "Answer: 25" |
| `tool_calling.py` | Tool calling (model emits JSON tool call, executed locally) | SUCCESS |
| `rag.py` | RAG (lexical retrieval over `data/api_docs.txt` + grounded codegen) | SUCCESS |
| `reflexion.py` | Reflexion (generate → test → reflect → repair) | SUCCESS (initial impl passed; reflexion prompt wired) |

## Backend note (environment adaptation)

The assignment targets local Ollama with `mistral-nemo:12b` / `llama3.1:8b`.
This machine instead runs an OpenAI-compatible vLLM server (`qwen38`,
Qwen3.8-9B-GPTQ-Int4). `backend_shim.py` provides a drop-in `chat()` that mimics
the `ollama` package API and routes to the vLLM endpoint, controlled by env vars
in `../.env`:

- `WEEK1_BACKEND=vllm` (default) — use the OpenAI-compatible endpoint
- `WEEK1_BACKEND=ollama` — use real Ollama if the course models are pulled
- `WEEK1_ENABLE_THINKING=1` (default) — sends `chat_template_kwargs.enable_thinking=true`
  per request, which materially matters for this model family: with thinking
  disabled, the 9B model cannot do reliable letter-level reversal (token-level
  blind spot), while enabling internal chain-of-thought fixes it — itself a nice
  demonstration of why CoT-style prompting helps on symbolic manipulation tasks.

Credentials live in `../.env` (git-ignored) and are read by the shim via
`OPENAI_BASE_URL` / `OPENAI_API_KEY` / `VLLM_MODEL`.
