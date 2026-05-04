"""Entry point: parses the task arg, runs an interactive multi-turn session, and calls GitHub helpers.

Flow:
  1. Load or create the persistent agent + environment (agent.json).
  2. Create a new session with the GitHub repo mounted.
  3. Send the task and stream events until idle.
  4. On idle, prompt for a reply — continue the session or press Enter to finish.
  5. If a PR was created, offer a Claude review and print the PR URL at the end.
  6. On error before PR creation, automatically delete any branch the agent pushed.
"""
import argparse
from anthropic import Anthropic

import config
from agent import load_or_create
from github import create_pr, delete_branch
from reviewer import review_pr


def main():
    parser = argparse.ArgumentParser(description="Claude Managed Agent — task manager pipeline")
    parser.add_argument("task", help="Task description for the agent")
    args = parser.parse_args()

    task = args.task
    client = Anthropic()

    # ── Step 1: Agent + Environment ───────────────────────────────────────────
    # Created once, reused on every subsequent run via agent.json
    agent_id, environment_id = load_or_create(client)

    # ── Step 2: Session ───────────────────────────────────────────────────────
    # New session per run, mounts the GitHub repo
    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=environment_id,
        title="Task Manager Dev Session",
        resources=[
            {
                "type": "github_repository",
                "url": config.REPO_URL,
                "authorization_token": config.GITHUB_TOKEN,
                "mount_path": "/workspace/repo",
                "checkout": {"type": "branch", "name": "master"},
            }
        ],
    )
    print(f"Session ID: {session.id}")

    # ── Step 3: Stream ────────────────────────────────────────────────────────
    # Send the task and process events
    current_branch = None
    pr_url = None
    pr_created = False

    try:
        # Stream must be opened before sending the message so early events aren't missed.
        with client.beta.sessions.events.stream(session.id) as stream:
            client.beta.sessions.events.send(
                session.id,
                events=[
                    {
                        "type": "user.message",
                        "content": [{"type": "text", "text": task}],
                    }
                ],
            )

            # Tracks whether the cursor is at a line start to avoid spurious blank lines
            # between consecutive tool-use events.
            at_line_start = True
            for event in stream:
                match event.type:
                    case "agent.message":
                        for block in event.content:
                            if block.type == "text":
                                print(block.text, end="", flush=True)
                                at_line_start = block.text.endswith("\n")
                    case "agent.tool_use":
                        if not at_line_start:
                            print()
                        print(f"[Tool: {event.name}]")
                        at_line_start = True
                    case "agent.custom_tool_use":
                        if event.name == "create_pr":
                            current_branch = event.input.get("branch")
                            if not at_line_start:
                                print()
                            print(f"[Creating PR: {event.input['title']}]")
                            at_line_start = True
                            output, success = create_pr(
                                title=event.input["title"],
                                body=event.input["body"],
                                branch=event.input["branch"],
                            )
                            if success:
                                pr_created = True
                                pr_url = output
                                answer = input("\nRequest a Claude review? [y/N] ").strip().lower()
                                if answer == "y":
                                    review_pr(output)
                            client.beta.sessions.events.send(
                                session.id,
                                events=[
                                    {
                                        "type": "user.custom_tool_result",
                                        "custom_tool_use_id": event.id,
                                        "content": [{"type": "text", "text": output}],
                                    }
                                ],
                            )
                    case "session.status_idle":
                        reply = input("\nReply (or press Enter to finish): ").strip()
                        if not reply:
                            print("\nAgent finished.")
                            if pr_url:
                                print(f"PR: {pr_url}")
                            break
                        client.beta.sessions.events.send(
                            session.id,
                            events=[
                                {
                                    "type": "user.message",
                                    "content": [{"type": "text", "text": reply}],
                                }
                            ],
                        )
    except Exception as e:
        print(f"\nError: {e}")
        if current_branch and not pr_created:
            print(f"Cleaning up branch '{current_branch}'...")
            delete_branch(current_branch)
        raise


if __name__ == "__main__":
    main()
