import os
import re
from typing import List, Callable
from dotenv import load_dotenv
# Use OpenAI-compatible backend shim (routes to local vLLM; set WEEK1_BACKEND=ollama for real Ollama)
from backend_shim import chat

load_dotenv()

NUM_RUNS_TIMES = 5

DATA_FILES: List[str] = [
    os.path.join(os.path.dirname(__file__), "data", "api_docs.txt"),
]


def load_corpus_from_files(paths: List[str]) -> List[str]:
    corpus: List[str] = []
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    corpus.append(f.read())
            except Exception as exc:
                corpus.append(f"[load_error] {p}: {exc}")
        else:
            corpus.append(f"[missing_file] {p}")
    return corpus


# Load corpus from external files (simple API docs). If missing, fall back to inline snippet
CORPUS: List[str] = load_corpus_from_files(DATA_FILES)

QUESTION = (
    "Write a Python function `fetch_user_name(user_id: str, api_key: str) -> str` that calls the documented API "
    "to fetch a user by id and returns only the user's name as a string."
)


# RAG system prompt: the context block already carries the retrieved API docs.
# The prompt pins the model to ground every code decision in that context only.
YOUR_SYSTEM_PROMPT = (
    "You are a code generation assistant that writes strictly from the provided context. "
    "Rules:\n"
    "1. Read the 'Context' section: it is the ONLY authoritative API reference.\n"
    "2. Use the exact Base URL and endpoint path from the context.\n"
    "3. Use the exact authentication header name from the context (X-API-Key) with the api_key argument.\n"
    "4. Build the request with requests.get, call raise_for_status(), then return only the 'name' field.\n"
    "5. Output a single fenced python code block containing imports and the function. No prose."
)


# For this simple example
# For this coding task, validate by required snippets rather than exact string
REQUIRED_SNIPPETS = [
    "def fetch_user_name(",
    "requests.get",
    "/users/",
    "X-API-Key",
    "return",
]


def YOUR_CONTEXT_PROVIDER(corpus: List[str]) -> List[str]:
    """Select and return the relevant subset of documents from CORPUS for this task.

    Naive lexical retrieval: score each document by overlap with the task's key
    entities (user, api, endpoint, authentication). The api_docs.txt entry wins
    and is returned as the retrieved context; irrelevant documents are dropped.
    An empty return would simulate "no retrieval" (ablation) and fail the checks.
    """
    query_terms = {"user", "users", "api", "key", "endpoint", "authentication", "fetch"}
    scored: List[tuple] = []
    for doc in corpus:
        if not doc or doc.startswith("[") :  # skip error/missing placeholders
            continue
        tokens = set(re.findall(r"[a-zA-Z]+", doc.lower()))
        score = len(tokens & query_terms)
        scored.append((score, doc))
    if not scored:
        return []
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [scored[0][1]]


def make_user_prompt(question: str, context_docs: List[str]) -> str:
    if context_docs:
        context_block = "\n".join(f"- {d}" for d in context_docs)
    else:
        context_block = "(no context provided)"
    return (
        f"Context (use ONLY this information):\n{context_block}\n\n"
        f"Task: {question}\n\n"
        "Requirements:\n"
        "- Use the documented Base URL and endpoint.\n"
        "- Send the documented authentication header.\n"
        "- Raise for non-200 responses.\n"
        "- Return only the user's name string.\n\n"
        "Output: A single fenced Python code block with the function and necessary imports.\n"
    )


def extract_code_block(text: str) -> str:
    """Extract the last fenced Python code block, or any fenced code block, else return text."""
    # Try ```python ... ``` first
    m = re.findall(r"```python\n([\s\S]*?)```", text, flags=re.IGNORECASE)
    if m:
        return m[-1].strip()
    # Fallback to any fenced code block
    m = re.findall(r"```\n([\s\S]*?)```", text)
    if m:
        return m[-1].strip()
    return text.strip()


def test_your_prompt(system_prompt: str, context_provider: Callable[[List[str]], List[str]]) -> bool:
    """Run up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT."""
    context_docs = context_provider(CORPUS)
    user_prompt = make_user_prompt(QUESTION, context_docs)

    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = chat(
            model="llama3.1:8b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": 0.0},
        )
        output_text = response.message.content
        code = extract_code_block(output_text)
        missing = [s for s in REQUIRED_SNIPPETS if s not in code]
        if not missing:
            print(output_text)
            print("SUCCESS")
            return True
        else:
            print("Missing required snippets:")
            for s in missing:
                print(f"  - {s}")
            print("Generated code:\n" + code)
    return False


if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT, YOUR_CONTEXT_PROVIDER)
