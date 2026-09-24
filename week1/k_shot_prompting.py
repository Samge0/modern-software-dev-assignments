# Use OpenAI-compatible backend shim (routes to local vLLM; set WEEK1_BACKEND=ollama for real Ollama)
from backend_shim import chat
from dotenv import load_dotenv

load_dotenv()

NUM_RUNS_TIMES = 5

# K-shot examples demonstrating the exact task format: input word -> reversed word.
# Teaching by demonstration keeps the model on-format (no explanations, exact casing).
YOUR_SYSTEM_PROMPT = (
    "You reverse words letter-by-letter. Follow the exact format of the examples.\n\n"
    "Example 1:\n"
    "Input: hello\n"
    "Output: olleh\n\n"
    "Example 2:\n"
    "Input: ChatGPT\n"
    "Output: TPgtahC\n\n"
    "Example 3:\n"
    "Input: Stanford\n"
    "Output: dronatS\n\n"
    "Rules: Output ONLY the reversed word. Preserve original letter casing and order-reversal. "
    "No quotes, no punctuation, no explanation."
)

USER_PROMPT = """
Reverse the order of letters in the following word. Only output the reversed word, no other text:

httpstatus
"""


EXPECTED_OUTPUT = "sutatsptth"


def test_your_prompt(system_prompt: str) -> bool:
    """Run the prompt up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT.

    Prints "SUCCESS" when a match is found.
    """
    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = chat(
            model="mistral-nemo:12b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": USER_PROMPT},
            ],
            options={"temperature": 0.5},
        )
        output_text = response.message.content.strip()
        if output_text.strip() == EXPECTED_OUTPUT.strip():
            print("SUCCESS")
            return True
        else:
            print(f"Expected output: {EXPECTED_OUTPUT}")
            print(f"Actual output: {output_text}")
    return False


if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)
