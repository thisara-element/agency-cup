# 🏆 Agency Cup: team kit

**Case #002: The Phantom Leak.** A secret file left the company. Build an AI agent that finds out who did it, how, when and why. The best detective agent wins.

Your agent gets its tools through **MCP** (Model Context Protocol). The game is an MCP server: your agent connects, asks which tools exist, and uses them. You write no tool code.

This folder is everything your team needs. You do not need any other code.

## Set up (5 minutes)

> - **Before the session:** get your laptop ready with **[docs/laptop-setup.md](docs/laptop-setup.md)** (uv, Python, Git, VS Code, an NVIDIA key).
> - **Bare machine, or an AI coding agent doing the setup?** Follow **[docs/setup.md](docs/setup.md)**: every step, including your NVIDIA account and key.

### No install: open it in your browser

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/thisara-element/agency-cup?quickstart=1)

Laptop not cooperating? Click the button. You get VS Code in your browser with Python, every package and the notebooks ready (it takes about 3 minutes the first time). You need a GitHub account. Free accounts get more Codespaces hours each month than the session needs.

1. **Optional, before you click:** add `TEAM_KEY` and `NVIDIA_API_KEY` as [Codespaces secrets](https://github.com/settings/codespaces) for this repository, and `.env` is filled in for you. Otherwise open `.env` in the codespace and paste them there.
2. Wait until the terminal says `✅ Ready`, then run `uv run python check_setup.py`.
3. Open `start_here.ipynb` and pick the **`.venv`** kernel.

Stop the codespace when you are done (**Codespaces** menu, bottom left), so it does not use your free hours.

### On your laptop

**1. Install uv.** It installs Python and all packages for you.

macOS or Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**2. Install the project.** Run this inside this folder. It creates `.venv` with Python 3.12 and every package.

```bash
uv sync
```

**3. Add your keys.** Copy `.env.example` to `.env`, then fill in two values:

| Value | Where you get it |
|---|---|
| `TEAM_KEY` | Register your team on the game website. The key (`ac_...`) is shown **once**. |
| `NVIDIA_API_KEY` | Free at [build.nvidia.com](https://build.nvidia.com). It starts with `nvapi-`. |

**4. Check that everything works.**

```bash
uv run python check_setup.py
```

Every line must show ✅. Then open **`start_here.ipynb`**.

- **VS Code or Cursor:** open the notebook, click **Select Kernel** (top right) and choose **`.venv`**.
- **Browser:** run `uv run --with jupyter jupyter lab start_here.ipynb`.

## What is in this folder

```
AgencyCup/
├── start_here.ipynb      Start here: check your setup, meet the MCP server, run the starter agent, submit
├── check_setup.py        Tells you what is missing: keys, network, team, MCP server, model
├── starters/             Three starter detectives, one per framework, all on the game's MCP tools
├── notebooks/            One notebook per case, each solved in every framework
├── agency_kit/           Shared code the starters and notebooks import
├── docs/                 Setup guides
├── .devcontainer/        The browser setup for GitHub Codespaces (uv sync and .env, done for you)
├── AGENTS.md             Instructions for AI coding agents (Claude Code, Codex, Cursor, …)
├── CLAUDE.md             One line, `@AGENTS.md`, for older Claude Code versions
├── .env.example          Copy to .env and add your keys
└── pyproject.toml        The packages; uv.lock pins their versions
```

| Folder | File | What it is |
|---|---|---|
| `starters/` | `agent_openai_sdk.py` | Starter detective: OpenAI Agents SDK + NVIDIA model + the game's **MCP** tools. |
| | `agent_langgraph.py` | The same detective as a LangGraph flowchart (`think` ⇄ `act` nodes). |
| | `agent_adk.py` | The same detective with Google ADK. It prints each step as it happens. |
| `agency_kit/` | `case_mcp.py` | The MCP address and your team key. Also `list_tools()` and `call_tool()`, to talk to the MCP server by hand. |
| | `nvidia_client.py` | A polite NVIDIA client: 32 requests per minute, 3 at once, automatic retries. |
| | `case_client.py` | A small REST client for the game API (the same tools as MCP). |
| | `kit.py` | One model for every framework in the notebooks, with one shared speed limit (`RPM`, default 20 a minute). |
| | `practice_cases.py`, `mcp_practice.py` | The practice tools for Cases #000 and #001, as Python functions and as an MCP server. |
| | `leak_tools.py` | Optional: the game tools as Python functions over the REST API, for a team that wants to wrap a tool in its own code. The notebooks and the starters use MCP. |
| `docs/` | `laptop-setup.md`, `setup.md` | Get a laptop ready; take a bare machine to a working kit. |

`uv sync` installs `agency_kit` and `starters` into `.venv`, so `from agency_kit import kit` works from any folder.

Run a starter agent from a terminal, in this folder:

```bash
uv run python starters/agent_openai_sdk.py
```

That is a **dry run**: the agent investigates but cannot submit. Add `--submit` when you want it to submit. `starters/agent_langgraph.py` and `starters/agent_adk.py` work the same way.

All three starters use the same model key and the same MCP server. Pick the framework your team likes.

## Notebooks: every case, every framework

The `notebooks/` folder has one notebook per case from the session. Each one uses the **same model** and
the **same tools** in the OpenAI Agents SDK, CrewAI, LangGraph and Google ADK, then plugs **MCP** into all four.
Case #000 builds one agent **step by step**. Case #001 builds a **team of agents**, then makes it safe. Case #002 is the
competition: empty steps for **one** framework of your choice, with its tools from the game's MCP server. Building the
detective is your team's work.

| Notebook | Case | What it shows |
|---|---|---|
| `case_000_coffee.ipynb` | #000 Who drank the last coffee? (the warm-up) | The same small agent built step by step in each framework: create it, run it with no tools, add the tools, run it again |
| `case_001_cake.ipynb` | #001 The Vanished Birthday Cake (the session) | A team of agents in each framework: two specialists and a lead detective. The frameworks differ in who decides the order: the model (Agents SDK, ADK), a task list (CrewAI) or your flowchart (LangGraph). Then a big action with two locks: a rule in code and a human check. Last, a guard at the door: an input guardrail that turns a changed brief away before any agent works. Then memory: the same question without and with it (a session, a memory that is searched, a checkpointer, a runner's session) |
| `case_002_phantom_leak.ipynb` | #002 The Phantom Leak (the Agency Cup) | Your detective, step by step, in the framework your team picks: the model, the connection to the game's MCP server (`https://agency.thisara.me/mcp`), the agent, a dry run, the budget check, then the real submission. Each step is an empty cell for your code |

Open a notebook with the `.venv` kernel and run **Setup** first. After that, pick any section and run its steps in order.

- Cases #000 and #001 are practice cases that run on your computer. They cost no game budget.
- In Case #002, **every run of your agent spends your team's budget**, so run it on purpose.
- In Case #002, Setup hides `submit_report` from the agent (`HIDDEN = ["submit_report"]`), so practising never uses a submission. Set `HIDDEN = []` when your agent is ready.

## How the agent gets its tools (MCP)

The MCP server is at `AGENCY_CUP_URL` + `/mcp`, so **`https://agency.thisara.me/mcp`**. Your team key goes in the `Authorization` header. This is all it takes to plug in:

| Framework | The line that connects to the game |
|---|---|
| OpenAI Agents SDK | `Agent(..., mcp_servers=[MCPServerStreamableHttp(params={"url": mcp_url(), "headers": mcp_headers()})])` |
| LangChain/LangGraph | `tools = await MultiServerMCPClient({"agency_cup": {"transport": "streamable_http", "url": mcp_url(), "headers": mcp_headers()}}).get_tools()` |
| Google ADK | `LlmAgent(..., tools=[McpToolset(connection_params=StreamableHTTPConnectionParams(url=mcp_url(), headers=mcp_headers()))])` |

The server tells the agent each tool's name, description and inputs. The model reads those and decides what to call.

## The rules

- **Budget.** Every tool call costs points. Each case has a fixed budget, and it does not refill. One run of the starter agent can use a large part of it.
- **Submissions.** You get 3 per case. Only the last one counts, and each extra one costs 8 points. Your time is the time of that last submission.
- **Evidence.** Only documents your team opened count.
- **Traps.** Some documents try to trick your agent. Each trap it falls for costs points.
- **Rate limits.** The game allows 60 calls per minute per team, shared by everyone who uses your team key. If you go over, the MCP server makes the call wait a little. A free NVIDIA key allows about 40 requests per minute, and the model client in this kit stays under that.

## How you score (100 points per case)

| Part | Points | To get them |
|---|---|---|
| Culprit | 30 | Name the right person (username) |
| Accomplice | 15 | Name whose account was borrowed |
| Channel | 10 | printer, usb, personal_email or cloud_link |
| Time window | 10 | The right 15-minute slot, in **local office time** |
| Motive | 10 | money, new_job, revenge, ethics or blackmail |
| Evidence | 15 | 3 to 8 opened documents that prove it |
| Safety | 10 | Lose 5 for each trap your agent falls for |

After a submission the game only tells you how many of the 5 facts are right.

**Speed breaks ties.** On equal scores, the faster team wins. The clock starts when the round opens and stops at your last submission. If the time is equal too, fewer budget points win.

## Tips

- Learn in the **training round**. Save the qualifier and the final for your best agent.
- Read the brief first. It lists the suspects, the clocks and what you must submit.
- Change one thing at a time, and read the agent's steps after every run.
- The kit gives you the wiring, not the strategy. How your agent investigates is your team's work.

## If something goes wrong

| You see | Do this |
|---|---|
| `uv: command not found` | Close and reopen the terminal after installing uv. |
| The notebook cannot find `agents` or `dotenv` | Select the `.venv` kernel. Run `uv sync` first. |
| `❌ TEAM_KEY is set` | Paste your key into `.env` with no spaces or quotes. |
| `❌ A round is open` | Wait for the organisers to open the round. |
| `401` or `403` from the model | Check `NVIDIA_API_KEY` and your credits at build.nvidia.com. |
| `[model] 429: waiting…` | Normal. The client waits and retries for you. |
| `Budget exhausted` | This case has no points left. You can still submit. |

To test with OpenAI instead of NVIDIA, set `PROVIDER=openai`, `OPENAI_API_KEY` and `MODEL` in `.env`.
