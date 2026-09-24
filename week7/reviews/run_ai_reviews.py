"""AI code reviewer (Graphite-Diamond-style) for week7 PRs.

Fetches each PR diff via gh, sends to the local vLLM qwen38 model with a
review-focused system prompt, saves the review to week7/reviews/.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

client = OpenAI(
    base_url=os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:16869/v1"),
    api_key=os.environ.get("OPENAI_API_KEY", "EMPTY"),
    timeout=300.0,
)

SYSTEM = (
    "You are an expert code reviewer (like Graphite Diamond). Review the diff below. "
    "Output 3 sections:\n"
    "1. SUMMARY: one sentence on what the change does.\n"
    "2. FINDINGS: numbered list; each = severity (blocker/warn/nit) | file:line | issue | concrete suggestion. "
    "Focus on: correctness bugs, security, API contract breaks, missing error paths, test gaps. "
    "Only report REAL issues you can point to in the diff — no style noise, no invented line numbers.\n"
    "3. VERDICT: approve / request-changes / blocked, one-line reason.\n"
)

PRS = [
    (1, "week7/task1: DELETE + stats endpoints, validation, error handling"),
    (2, "week7/task2: extended extraction logic"),
    (3, "week7/task3: Tag model + note-tag M2M + action-item note FK"),
    (4, "week7/task4: pagination & sorting test coverage"),
]

out_dir = Path(__file__).resolve().parent
for pr, title in PRS:
    diff = subprocess.run(
        ["gh", "pr", "diff", str(pr), "--repo", "Samge0/modern-software-dev-assignments"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    ).stdout
    if not diff.strip():
        print(f"PR{pr}: no diff fetched, skipping")
        continue
    # keep prompt bounded
    diff_bounded = diff[:18000]
    resp = client.chat.completions.create(
        model="qwen38",
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"PR #{pr} — {title}\n\n```diff\n{diff_bounded}\n```"},
        ],
        temperature=0.2,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
    review = resp.choices[0].message.content or ""
    (out_dir / f"pr{pr}_ai_review.md").write_text(
        f"# AI Review — PR #{pr}: {title}\n\n(reviewed by local qwen38 via OpenAI-compatible endpoint)\n\n{review}\n",
        encoding="utf-8",
    )
    print(f"PR{pr}: review saved ({len(review)} chars)")
print("DONE")
