# Setup: from a bare machine to a working kit

This guide takes a computer with **nothing installed** (no Python, no Git) to a working Agency Cup kit.
A person can follow it, and so can an AI coding agent (Claude Code, Codex, Cursor, …).

- **Agent:** do the steps marked 🤖 yourself. When you reach a step marked 👤, stop and ask the human to do it.
- **Human:** you do the 👤 steps: anything with an account, a password, an email or an API key.

## Rules for AI agents

1. Run every command from the repository root (the folder that holds `pyproject.toml`).
2. After each step, run its **Check**. Go on only when the check passes.
3. **Never** create accounts, type passwords, solve CAPTCHAs or read verification emails. Those are 👤 steps.
4. **Never** print, echo, log or commit an API key. Do not `cat .env`. `.env` is in `.gitignore`. Keep it there.
5. Do not install Python, pip, conda or any framework by hand. `uv` does all of it (step 2).
6. Do not run the starter agents (`starters/agent_*.py`) or the Case #002 notebook unless the human asks: they spend the team's game budget.

## Step 1 🤖 Get the code (skip if you are already in the repo)

Either download the ZIP from GitHub (**Code → Download ZIP**) and unzip it, or clone it:

```bash
git clone https://github.com/thisara-element/agency-cup.git
cd agency-cup
```

No Git? On macOS, the first `git` command offers to install it (Xcode Command Line Tools). On Windows, get it from
[git-scm.com](https://git-scm.com). Or use the ZIP.

**Check:** `pyproject.toml` and `uv.lock` are in the current folder.

## Step 2 🤖 Install uv

`uv` installs Python 3.12 and every package for you.

macOS or Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
```

No `curl`? Use `wget -qO- https://astral.sh/uv/install.sh | sh` instead.

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
```

The second line in each block puts `uv` on the PATH of the current shell. A human can close and reopen the terminal instead.

**Check:** `uv --version` prints a version.

## Step 3 🤖 Install Python and all packages

```bash
uv sync
```

This downloads Python 3.12 (from `.python-version`), creates `.venv` and installs the exact versions in `uv.lock`.
It needs internet and a few hundred MB of disk.

**Check:** `uv run python -c "import agents, langgraph, crewai, google.adk; print('ok')"` prints `ok`.

## Step 4 👤 Create an NVIDIA account and an API key

The kit's model runs on NVIDIA's free API. **The human does this step.**

1. Open [build.nvidia.com](https://build.nvidia.com) and click **Login** (top right).
2. Enter your email. If you have no NVIDIA account, follow **Create account**: name, password, then confirm the
   verification email NVIDIA sends you.
3. Back on build.nvidia.com, open your profile menu (top right) and choose **API Keys**, then **Generate API Key**.
   If you cannot find it, open any model page and click **Get API Key**.
4. Copy the key. It starts with `nvapi-`. You may only see it once, so keep it somewhere safe.

The free tier allows about 40 requests a minute. The kit stays under that limit by itself.

## Step 5 👤 Get your team key

Register your team on the game website (the `AGENCY_CUP_URL` in `.env.example`). The team key starts with `ac_` and is
shown **once**. Copy it.

## Step 6 🤖👤 Create `.env`

🤖 The agent copies the template:

```bash
cp .env.example .env
```

On Windows PowerShell: `Copy-Item .env.example .env`

👤 The human opens `.env` in an editor and replaces the two placeholders, with no spaces or quotes:

```
TEAM_KEY=ac_...
NVIDIA_API_KEY=nvapi-...
```

Agents: ask the human to paste the keys into the file themselves. Do not ask them to paste keys into the chat.

## Step 7 🤖 Check everything

```bash
uv run python check_setup.py
```

It never prints your keys. Every line should show ✅. If a line shows ❌, it prints the fix under it.

- `❌ TEAM_KEY is set` or `❌ NVIDIA_API_KEY is set`: step 6 is not done. Ask the human.
- `❌ A round is open`: not a setup problem. The organisers have not opened a round yet. Everything else can still pass.
- `❌ Your model answers` with 401/403: the NVIDIA key is wrong or out of credits. Ask the human to check step 4.

## Step 8 👤 Open the notebooks

- **VS Code or Cursor:** install the **Python** and **Jupyter** extensions. Open `start_here.ipynb`, click
  **Select Kernel** (top right) and choose **`.venv`**.
- **Browser, no editor:**

  ```bash
  uv run --with jupyter jupyter lab start_here.ipynb
  ```

Then read [`README.md`](../README.md) for the rules, the scoring and the other notebooks in `notebooks/`.
