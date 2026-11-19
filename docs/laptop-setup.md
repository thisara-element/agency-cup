# Get your laptop ready (before the session)

Please do this **before** the session. It takes about 15 minutes on **macOS, Linux or Windows 10/11**, even on a laptop
with nothing installed. Anything you already have is detected and skipped.

You will finish with:

- **uv** and **Python 3.12**
- **Git**
- **VS Code** (or Cursor) with the Python and Jupyter extensions
- a free **NVIDIA API key**, tested and saved somewhere safe

You can follow this guide yourself, or hand it to an AI coding agent (Claude Code, Codex, Cursor, …).

- 🤖 steps: an AI agent can do them.
- 👤 steps: **you** must do them (accounts, passwords, emails, API keys, installer windows).

**Which terminal?** macOS: the **Terminal** app. Linux: any terminal. Windows: **PowerShell** (Start menu → type
"PowerShell"), not Command Prompt.

## Rules for AI agents

1. **Find the OS first.** Run `uname -s`: `Darwin` is macOS, `Linux` is Linux. If `uname` is not found, or
   `$env:OS` prints `Windows_NT`, it is Windows. Run the **macOS / Linux** blocks in bash or zsh, and the **Windows**
   blocks in PowerShell.
2. **Check before you install.** Run Step 0 first and skip every step whose line shows `[ok]`. Each step also starts
   with its own **Check**. Run it again after installing.
3. If `sudo` asks for a password, or an installer opens a window, stop and ask the human to do that part.
4. **Never** create accounts, type passwords, solve CAPTCHAs or read verification emails.
5. **Never** ask for, print, store or log the API key. The human types it into a hidden prompt (Step 6).
6. Install Python only through `uv` (Step 2). Do not use pip, Homebrew Python, conda or pyenv for it.
7. If a step fails, show the human the error and the fix you suggest before you change anything else on the machine.

## Step 0 🤖 See what is already installed

macOS / Linux:

```bash
cd ~   # run from your home folder, so a project's own Python does not count
has()  { command -v "$1" >/dev/null 2>&1; }
show() { if [ "$1" = 0 ]; then echo "[ok]      $2"; else echo "[missing] $2"; fi; }
MAC_CODE="/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"

has uv; show $? "uv"
uv python find 3.12 >/dev/null 2>&1; show $? "Python 3.12"
if [ "$(uname -s)" = Darwin ] && [ "$(command -v git)" = /usr/bin/git ]; then
  xcode-select -p >/dev/null 2>&1; show $? "Git"   # on macOS, /usr/bin/git is only a stub until the developer tools are installed
else
  git --version >/dev/null 2>&1; show $? "Git"
fi
{ has code || has cursor || [ -x "$MAC_CODE" ] || [ -d /Applications/Cursor.app ]; }; show $? "VS Code or Cursor"
exts=$( { code --list-extensions || "$MAC_CODE" --list-extensions || cursor --list-extensions; } 2>/dev/null )
echo "$exts" | grep -qix ms-python.python && echo "$exts" | grep -qix ms-toolsai.jupyter; show $? "Python and Jupyter extensions"
```

Windows (PowerShell):

```powershell
cd ~   # run from your home folder, so a project's own Python does not count
function Has($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }
function Show($ok, $name) { if ($ok) { "[ok]      $name" } else { "[missing] $name" } }

Show (Has uv) "uv"
Show ((Has uv) -and $(uv python find 3.12 *> $null; $LASTEXITCODE -eq 0)) "Python 3.12"
Show (Has git) "Git"
Show ((Has code) -or (Has cursor) -or (Test-Path "$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe") -or (Test-Path "$env:ProgramFiles\Microsoft VS Code\Code.exe")) "VS Code or Cursor"
$exts = if (Has code) { code --list-extensions } elseif (Has cursor) { cursor --list-extensions } else { @() }
Show (($exts -contains "ms-python.python") -and ($exts -contains "ms-toolsai.jupyter")) "Python and Jupyter extensions"
```

Each line says `[ok]` or `[missing]`. Do only the steps for the `[missing]` lines, in order:

| Line | Step |
|---|---|
| uv | 1 |
| Python 3.12 | 2 |
| Git | 3 |
| VS Code or Cursor, extensions | 4 |

Steps 5 and 6 (the NVIDIA key) are for everyone.

## Step 1 🤖 Install uv

uv installs and manages Python for you.

**Check:** `uv --version` prints a version number. If it does, skip to Step 2.

**Installed but "command not found"?** It is probably only missing from this terminal's PATH:

- macOS / Linux: `[ -x "$HOME/.local/bin/uv" ] && source "$HOME/.local/bin/env"`
- Windows: refresh the PATH (see the box below), then check again.

**Install.** macOS / Linux:

```bash
if command -v curl >/dev/null 2>&1; then curl -LsSf https://astral.sh/uv/install.sh | sh
else wget -qO- https://astral.sh/uv/install.sh | sh; fi
source "$HOME/.local/bin/env"
```

Linux with neither `curl` nor `wget`: install `curl` with your package manager first (same commands as Git in Step 3).

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then refresh the PATH and check again.

> **Windows: refresh the PATH.** After any install, a running PowerShell does not see the new command. Run this line
> (or close and reopen PowerShell):
>
> ```powershell
> $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
> ```

## Step 2 🤖 Install Python 3.12

**Check:** `uv python find 3.12` prints a path. If it does, skip to Step 3. (uv uses a Python 3.12 you already have.)

**Install** (the same on all three):

```bash
uv python install 3.12
```

**Check again:** `uv run --python 3.12 python --version` prints `Python 3.12.x`.

## Step 3 🤖 Install Git

**Check:**

- macOS: `xcode-select -p` prints a folder, or `command -v git` prints a path other than `/usr/bin/git`.
- Linux and Windows: `git --version` prints a version number.

If it does, skip to Step 4.

**Install:**

- **macOS:** run `xcode-select --install`. 👤 A window opens: click **Install** and wait until it finishes
  (a few minutes). If Homebrew is installed (`brew --version` works), `brew install git` also works.
- **Linux:** use your package manager. Find it with `command -v apt-get dnf pacman zypper`:

  | Package manager | Command |
  |---|---|
  | `apt-get` (Debian, Ubuntu, Mint) | `sudo apt-get update && sudo apt-get install -y git` |
  | `dnf` (Fedora, RHEL) | `sudo dnf install -y git` |
  | `pacman` (Arch, Manjaro) | `sudo pacman -S --noconfirm git` |
  | `zypper` (openSUSE) | `sudo zypper install -y git` |

- **Windows:** if `winget --version` works, run
  `winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements`,
  then refresh the PATH. No `winget`? 👤 Download and run the installer from [git-scm.com](https://git-scm.com),
  keeping the default options, then reopen PowerShell.

**Check again** with the same check as above.

## Step 4 🤖👤 Install VS Code and two extensions

Cursor works too. If you use Cursor, put `cursor` wherever this step says `code`.

**Check the editor:** `code --version` prints a version. On macOS, the app can also exist without the `code` command:
`ls "/Applications/Visual Studio Code.app"`. If the editor is there, skip to **Extensions**.

**Install the editor:**

- **macOS:** if `brew --version` works, run `brew install --cask visual-studio-code`. Otherwise 👤 download it from
  [code.visualstudio.com](https://code.visualstudio.com), unzip it and drag it into **Applications**.
- **Linux:** if `snap --version` works, run `sudo snap install code --classic`. Otherwise 👤 download the `.deb`
  (Debian, Ubuntu) or `.rpm` (Fedora, openSUSE) from [code.visualstudio.com](https://code.visualstudio.com) and open it.
- **Windows:** if `winget --version` works, run
  `winget install --id Microsoft.VisualStudioCode -e --source winget --accept-package-agreements --accept-source-agreements`,
  then refresh the PATH. Otherwise 👤 download the installer from [code.visualstudio.com](https://code.visualstudio.com).

**VS Code is installed but `code` is not found:**

- macOS: use the full path instead of `code`:
  `"/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"`. Or open VS Code, press `Cmd+Shift+P` and run
  **Shell Command: Install 'code' command in PATH**.
- Windows: refresh the PATH. If it is still missing, use `& "$env:LOCALAPPDATA\Programs\Microsoft VS Code\bin\code.cmd"`
  instead of `code`.
- Linux: open a new terminal.

**Extensions.** Check:

- macOS / Linux: `code --list-extensions | grep -Eix 'ms-python\.python|ms-toolsai\.jupyter'` prints both names.
- Windows: `code --list-extensions | Select-String -Pattern '^(ms-python\.python|ms-toolsai\.jupyter)$'` prints both names.

Install whichever is missing (the same on all three):

```bash
code --install-extension ms-python.python
code --install-extension ms-toolsai.jupyter
```

**Check again** with the same check.

## Step 5 👤 Create an NVIDIA account and an API key

**Check:** do you already have an NVIDIA API key that starts with `nvapi-`? Then skip to Step 6.

1. Open [build.nvidia.com](https://build.nvidia.com) and click **Login** (top right).
2. Enter your email. If you have no NVIDIA account, follow **Create account**, then confirm the verification email
   NVIDIA sends you.
3. On build.nvidia.com, open your profile menu (top right), choose **API Keys**, then **Generate API Key**.
   If you cannot find it, open any model page and click **Get API Key**.
4. Copy the key. It starts with `nvapi-`. Save it in a password manager or another safe place: you may only see it once.

**Do not share your key with anyone, and do not paste it into a chat.** It is free, but it is yours.

## Step 6 🤖👤 Test your key

🤖 Create a file called `check_nvidia.py` in your home folder (`~/check_nvidia.py` on macOS and Linux,
`$HOME\check_nvidia.py` in Windows PowerShell) with exactly this content. If the file already exists, replace it.

```python
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = ["openai>=2.0"]
# ///
"""Checks Python 3.12 and your NVIDIA API key with one tiny request. It never prints or saves the key."""

import getpass
import os
import sys

from openai import APIConnectionError, APIStatusError, OpenAI

MODEL = "nvidia/nemotron-3-ultra-550b-a55b"

key = os.environ.get("NVIDIA_API_KEY") or getpass.getpass("Paste your NVIDIA API key (it stays hidden), then Enter: ")
key = key.strip()
if not key.startswith("nvapi-"):
    sys.exit("❌ That does not look like an NVIDIA key. It should start with nvapi- (see step 5).")

client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=key, max_retries=2, timeout=120)
try:
    reply = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": "Reply with exactly: ready"}])
except APIStatusError as e:
    hints = {401: "the key is wrong. Copy it again (step 5).",
             403: "the key is wrong, or it has no access or credits. Copy it again (step 5), "
                  "then check your account at build.nvidia.com.",
             404: f"the model {MODEL} was not found. Tell the organisers.",
             429: "too many requests. Wait one minute and run this again."}
    sys.exit(f"❌ NVIDIA said {e.status_code}: {hints.get(e.status_code, str(e)[:200])}")
except APIConnectionError:
    sys.exit("❌ Could not reach integrate.api.nvidia.com. Check your internet connection, VPN or firewall.")

print(f"✅ Python {sys.version.split()[0]} works, and your NVIDIA key works.")
print(f"   {MODEL} said: {(reply.choices[0].message.content or '').strip()!r}")
```

👤 Run it **in your own terminal**, not through an AI agent. The commands are the same on all three:

```bash
cd ~
uv run check_nvidia.py
```

Paste your key when it asks, then press Enter. Nothing shows while you paste. That is normal.
(Windows: if `Ctrl+V` does nothing, right-click to paste.)

The first run takes a little longer, because uv downloads what the script needs. The model may also take up to a
minute to answer.

**Check:** the output starts with `✅ Python 3.12.` and says `your NVIDIA key works`.

## You are ready

Run Step 0 again. You are ready when:

- [ ] every line shows `[ok]`
- [ ] `uv run check_nvidia.py` showed ✅, and your key is saved somewhere safe

On the day, bring your laptop charged, and make sure you can reach the internet. You will get everything else in the session.
