# Lab Week 3 — Claude Managed Agents Pipeline

A CLI pipeline that uses [Claude Managed Agents](https://docs.anthropic.com/en/docs/agents) to autonomously implement, fix, and debug tasks on a Python CLI task manager app, then open a GitHub PR with the changes.

## How it works

1. **Agent + Environment** — Created once and persisted in `agent.json`. Reused on every subsequent run. The agent has access to bash, file tools, and a custom `create_pr` tool.
2. **Session** — A new session is created per run, with the GitHub repo mounted at `/workspace/repo`.
3. **Stream** — The task is sent as a user message and events are streamed back in real time.
4. **Multi-turn** — When the agent goes idle you're prompted to reply or press Enter to finish. This lets you answer clarifying questions without restarting the pipeline.
5. **PR review** — After a PR is created you're asked whether to post a Claude review as a comment. The PR URL is always printed at the end.
6. **Cleanup** — If the run fails before a PR is created, any branch the agent pushed is automatically deleted.

## Project structure

```
├── main.py          # entry point: session, multi-turn stream loop
├── config.py        # dotenv load, env validation, constants
├── agent.py         # agent + environment creation and persistence
├── github.py        # create_pr and delete_branch helpers
├── reviewer.py      # fetches diff, calls Claude, posts PR review comment
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

Run from the project root with the venv activated:

```bash
python3 main.py "fix the bug in complete_task"
python3 main.py "add a search command that filters tasks by title keyword"
```

The pipeline is interactive — when the agent finishes a turn you'll be prompted to reply or press Enter to exit. If a PR is created you'll also be asked whether to post a Claude review.

**Resetting the agent:** delete `agent.json` to force a new agent and environment to be created on the next run (required after changing the system prompt in `agent.py`).

## Environment variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `GITHUB_TOKEN` | GitHub PAT with `repo` scope (for pushing branches and creating PRs) |
| `REPO_URL` | Full HTTPS URL of the target repo (defaults to the task manager repo) |
