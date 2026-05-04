import os
import subprocess
from anthropic import Anthropic
from config import GITHUB_TOKEN

_REVIEW_PROMPT = """You are reviewing a pull request for a Python CLI task manager app.

Review the diff below. Focus on:
- Correctness and logic errors
- Edge cases that aren't handled
- Code clarity

Be concise. Use bullet points. If the change looks good, say so briefly.

Diff:
{diff}"""


def review_pr(pr_url: str) -> None:
    diff_result = subprocess.run(
        ["gh", "pr", "diff", pr_url],
        capture_output=True,
        text=True,
        env={**os.environ, "GH_TOKEN": GITHUB_TOKEN},
    )
    diff = diff_result.stdout.strip()
    if not diff:
        print("No diff found, skipping review.")
        return

    print("[Requesting Claude review...]")
    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": _REVIEW_PROMPT.format(diff=diff)}
        ],
    )
    review_body = next(
        (block.text for block in response.content if block.type == "text"),
        "No review generated.",
    )

    review_result = subprocess.run(
        ["gh", "pr", "review", pr_url, "--comment", "--body", review_body],
        capture_output=True,
        text=True,
        env={**os.environ, "GH_TOKEN": GITHUB_TOKEN},
    )
    if review_result.returncode == 0:
        print(f"[Review posted: {pr_url}]")
    else:
        print(f"Failed to post review: {review_result.stderr.strip()}")
