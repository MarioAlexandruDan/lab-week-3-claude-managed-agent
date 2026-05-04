"""Agent and environment persistence: creates them once and reuses across runs via agent.json."""
import json
from anthropic import Anthropic
from config import CONFIG_FILE

_SYSTEM_PROMPT = """You are a coding agent working on a Python CLI task manager application (task_manager.py).

The repo is mounted at /workspace/repo. The main file is /workspace/repo/task_manager.py.

The app stores tasks in tasks.json and supports these commands:
- add <title> [priority] [due YYYY-MM-DD]
- list [done|pending] [priority]
- complete <id>
- delete <id>
- overdue

When given a task:
1. Read the relevant code first before making changes.
2. Create a new branch: git -C /workspace/repo checkout -b <descriptive-branch-name>
3. Make minimal, focused changes - don't refactor beyond what's asked.
4. Commit: git -C /workspace/repo add -A && git -C /workspace/repo commit -m "<clear message>"
5. Push: git -C /workspace/repo push origin <branch-name>
6. Call create_pr with the branch name, a short title, and a body using this exact template:

## 🧭 What and Why

<short description of the problem and why this change is the right fix>

### Changes included:
- <bullet per logical change>

## 🧪 Test
<how to manually verify the fix>

7. Report clearly what you changed and why."""

_TOOLS = [
    {"type": "agent_toolset_20260401"},
    {
        "type": "custom",
        "name": "create_pr",
        "description": "Create a GitHub pull request from the current branch into master.",
        "input_schema": {
            "type": "object",
            "properties": {
                "branch": {"type": "string", "description": "The branch name to create the PR from"},
                "title": {"type": "string", "description": "The PR title"},
                "body": {"type": "string", "description": "The PR description explaining what was changed and why"},
            },
            "required": ["branch", "title", "body"],
        },
    },
]


def load_or_create(client: Anthropic) -> tuple[str, str]:
    """Return (agent_id, environment_id), reading from agent.json if it exists or creating and persisting new ones."""
    if CONFIG_FILE.exists():
        saved_config = json.loads(CONFIG_FILE.read_text())
        agent_id = saved_config["agent_id"]
        environment_id = saved_config["environment_id"]
        print(f"Loaded agent: {agent_id}")
        print(f"Loaded environment: {environment_id}")
        return agent_id, environment_id

    agent = client.beta.agents.create(
        name="Task Manager Dev Agent",
        model="claude-sonnet-4-6",
        description="A coding agent for Algolia Lab Week 3. Works on task_manager.py - a Python CLI todo app. Can implement features, fix bugs, and debug issues.",
        system=_SYSTEM_PROMPT,
        tools=_TOOLS,
    )

    environment = client.beta.environments.create(
        name="task-manager-env",
        config={
            "type": "cloud",
            "networking": {"type": "unrestricted"},
        },
    )

    CONFIG_FILE.write_text(json.dumps({
        "agent_id": agent.id,
        "environment_id": environment.id,
    }, indent=2))

    print(f"Created agent: {agent.id}")
    print(f"Created environment: {environment.id}")
    return agent.id, environment.id
