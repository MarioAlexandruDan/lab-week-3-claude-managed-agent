# Lab Week 3 — Claude Managed Agents Pipeline

A CLI pipeline that uses [Claude Managed Agents](https://docs.anthropic.com/en/docs/agents) to autonomously implement, fix, and debug tasks on a Python CLI task manager app, then open a GitHub PR with the changes.

## How it works

1. **Agent + Environment** — Created once and persisted in `agent.json`. The agent has access to bash, file tools, and a custom `create_pr` tool.
2. **Session** — A new session is created per run, with the GitHub repo mounted at `/workspace/repo`.
3. **Stream** — The task is sent as a user message; events are streamed back in real time. If the run fails before a PR is created, any branch pushed by the agent is automatically deleted.

## Project structure

```
├── main.py          # entry point: arg parse, session, stream
├── config.py        # dotenv load, env validation, constants
├── agent.py         # agent + environment persistence
├── github.py        # create_pr and delete_branch helpers
├── requirements.txt
├── .env             # secrets (gitignored)
└── .env.example
```

## Setup

Requires Python 3.10+.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

The `.env` file is loaded automatically on startup — no manual export needed.

## Usage

```bash
python3 main.py "fix the bug in complete_task"
python3 main.py "add a search command that filters tasks by title keyword"
```

## Environment variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `GITHUB_TOKEN` | GitHub PAT with `repo` scope (for pushing branches and creating PRs) |
| `REPO_URL` | Full HTTPS URL of the target repo (defaults to the task manager repo) |
