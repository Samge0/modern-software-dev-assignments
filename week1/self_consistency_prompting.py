import re
from collections import Counter

# Use OpenAI-compatible backend shim (routes to local vLLM; set WEEK1_BACKEND=ollama for real Ollama)
from backend_shim import chat
from dotenv import load_dotenv

load_dotenv()

NUM_RUNS_TIMES = 5

# Self-consistency: the harness already samples 5 runs @ temperature=1 and majority-votes.
# The system prompt's job is to make each independent reasoning chain maximally likely
# to reach the correct intermediate computation (60 - 20 - 15 = 25) and stay on-format,
# so the majority vote lands on "Answer: 25".
YOUR_SYSTEM_PROMPT = (
    "You are a precise arithmetic word-problem solver. Solve independently and carefully.\n"
    "Steps: (1) identify the total distance, (2) identify each stop's position in miles, "
    "(3) compute the distance between stop 1 and stop 2 by subtraction, "
    "(4) sanity-check the result is positive and less than the total.\n"
    "End with a final line exactly: Answer: <number>\n"
    "The final line must contain ONLY 'Answer: ' and the integer. Double-check your subtraction."
)

USER_PROMPT = """
Solve this problem, then give the final answer on the last line as "Answer: <number>".

Henry made two stops during his 60-mile bike trip. He first stopped after 20
miles. His second stop was 15 miles before the end of the trip. How many miles
did he travel between his first and second stops?
"""

EXPECTED_OUTPUT = "Answer: 25"


def extract_final_answer(text: str) -> str:
    """Extract the final 'Answer: ...' line from a verbose reasoning trace.

    - Finds the LAST line that starts with 'Answer:' (case-insensitive)
    - Normalizes to 'Answer: <number>' when a number is present
    - Falls back to returning the matched content if no number is detected
    """
    matches = re.findall(r"(?mi)^\s*answer\s*:\s*(.+)\s*$", text)
    if matches:
        value = matches[-1].strip()
        num_match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        if num_match:
            return f"Answer: {num_match.group(0)}"
        return f"Answer: {value}"
    return text.strip()


def test_your_prompt(system_prompt: str) -> bool:
    """Run the prompt NUM_RUNS_TIMES, majority-vote on the extracted 'Answer: ...' lines.

    Prints "SUCCESS" if the majority answer equals EXPECTED_OUTPUT.
    """
    answers: list[str] = []
    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = chat(
            model="llama3.1:8b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": USER_PROMPT},
            ],
            options={"temperature": 1},
        )
        output_text = response.message.content
        final_answer = extract_final_answer(output_text)
        print(f"Run {idx + 1} answer: {final_answer}")
        answers.append(final_answer.strip())

    if not answers:
        print("No answers produced.")
        return False

    counts = Counter(answers)
    majority_answer, majority_count = counts.most_common(1)[0]
    print(f"Majority answer: {majority_answer} ({majority_count}/{len(answers)})")

    if majority_answer.strip() == EXPECTED_OUTPUT.strip():
        print("SUCCESS")
        return True

    # Print distribution for debugging when majority does not match expected
    print(f"Expected output: {EXPECTED_OUTPUT}")
    print("Answer distribution:")
    for answer, count in counts.most_common():
        print(f"  {answer}: {count}")
    return False


if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)
