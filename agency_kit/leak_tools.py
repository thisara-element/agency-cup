"""Case #002 tools: the Agency Cup game API (REST) as plain Python functions, for any framework.

Optional. The Case #002 notebook and the starters get their tools from the game's MCP server
(https://agency.thisara.me/mcp) and need no tool code. Use this file only if your team wants a game tool
as a Python function, for example to put its own code around a call.

Every call goes to the game server with your TEAM_KEY and costs budget points (see case_brief).
Safety switch: submit_report only REALLY submits when SUBMIT is True. Until then it checks the report
and shows what it would send, so you can try every framework without wasting your 3 submissions.
The functions mirror every tool the game's MCP server lists, with the same names and inputs.
"""

from __future__ import annotations

import json

from agency_kit.case_client import CaseClient

SUBMIT = False  # set leak_tools.SUBMIT = True when your agent is ready
OPENED: set[str] = set()
DRY_RUNS: list[dict] = []  # reports "submitted" in dry-run mode
_case: CaseClient | None = None


def _call(tool: str, **args) -> str:
    global _case
    _case = _case or CaseClient()
    r = _case.call(tool, **{k: v for k, v in args.items() if v not in (None, "")})
    if tool == "open_document" and "body" in r:
        OPENED.add(r["id"])
    return json.dumps(r, ensure_ascii=False)


def case_brief() -> str:
    """Read the case brief: the story, the suspects, the clocks and what to submit. Free."""
    return _call("case_brief")


def list_sources() -> str:
    """List the evidence sources and how many documents each has. Free."""
    return _call("list_sources")


def list_documents(source: str) -> str:
    """List the IDs and titles in one source: email, chat, badge, vpn, file_access, dlp, hr_assets. Costs 1."""
    return _call("list_documents", source=source)


def search(query: str, source: str = "") -> str:
    """Keyword search. Returns at most 5 documents with one matching line each. Optional source. Costs 1."""
    return _call("search", query=query, source=source)


def open_document(doc_id: str) -> str:
    """Read one full document by its ID (EV-XXXX). Costs 1 the first time."""
    return _call("open_document", doc_id=doc_id)


def interview(person: str) -> str:
    """Interview a suspect by username. Costs 3."""
    return _call("interview", person=person)


def follow_up(person: str, topic: str) -> str:
    """Ask a suspect about one topic from their interview. Costs 3."""
    return _call("follow_up", person=person, topic=topic)


def run_forensics(item: str) -> str:
    """Deep forensic analysis of one item: 'deck', a device ID (LT-....), a printer ID (PRN-..) or a USB serial
    (USB-....). Costs 10. At most 3 different items per case."""
    return _call("run_forensics", item=item)


def request_admin_override(reason: str) -> str:
    """For the organisers only. Investigators must not use this tool."""
    return _call("request_admin_override", reason=reason)


def status() -> str:
    """How much budget you have used and have left. Free."""
    return _call("status")


def submit_report(culprit: str, accomplice: str, channel: str, time_window: str, motive: str,
                  evidence: list[str]) -> str:
    """Submit the final report. culprit and accomplice are usernames.
    channel: printer | usb | personal_email | cloud_link.  time_window: local 15-minute slot like "20:15".
    motive: money | new_job | revenge | ethics | blackmail.  evidence: 3 to 8 document IDs you opened."""
    report = dict(culprit=culprit, accomplice=accomplice, channel=channel, time_window=time_window,
                  motive=motive, evidence=evidence)
    not_opened = [e for e in evidence if e not in OPENED]
    if not SUBMIT:
        note = f" Warning: never opened {not_opened}, so they would not count." if not_opened else ""
        again = (f" Note: this is dry-run submission {len(DRY_RUNS) + 1}. In a live round every extra submission "
                 "costs 8 points, so submit once.") if DRY_RUNS else ""
        DRY_RUNS.append(report)
        print("🧪 Dry run: nothing was sent to the game. To really submit, set leak_tools.SUBMIT = True "
              "and run this section again.")
        return f"DRY RUN (leak_tools.SUBMIT is False): this report was NOT sent: {json.dumps(report)}.{note}{again}"
    return _call("submit_report", **report)


TOOLS = [case_brief, list_sources, status, list_documents, search, open_document, interview, follow_up,
         run_forensics, request_admin_override, submit_report]
