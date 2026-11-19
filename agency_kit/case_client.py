"""A tiny REST client for the Agency Cup game API (no MCP needed).

    case = CaseClient()                 # reads AGENCY_CUP_URL and TEAM_KEY
    case.call("case_brief")
    case.call("search", query="Nova_Launch_Deck_v7", source="dlp")

It waits and retries when the game API says 429 (60 calls per minute per team).
It also remembers documents you already opened, so a second read does not use a call.
A remembered document comes back with "cost": 0 and the budget you have NOW.
"""

from __future__ import annotations

import os
import re
import time

import httpx

GAME_URL = "https://agency.thisara.me"  # the Agency Cup website; AGENCY_CUP_URL in .env replaces it


def game_url() -> str:
    """The address of the game website, with no slash at the end."""
    return (os.environ.get("AGENCY_CUP_URL") or GAME_URL).rstrip("/")


class CaseClient:
    def __init__(self, base_url: str | None = None, team_key: str | None = None):
        self.base_url = (base_url or game_url()).rstrip("/")
        key = team_key or os.environ.get("TEAM_KEY")
        if not key:
            raise SystemExit("Set TEAM_KEY in your .env (you get it when you register your team).")
        self.http = httpx.Client(base_url=self.base_url, headers={"Authorization": f"Bearer {key}"}, timeout=30)
        self.cache: dict[str, dict] = {}     # document ID -> the document (id, source, title, body)
        self.budget_left: int | None = None  # the newest budget the game told us

    def call(self, tool: str, **args) -> dict:
        doc_id = str(args.get("doc_id") or "").strip().upper()
        if tool == "open_document" and doc_id in self.cache:
            # Free and instant. Never replay the old answer as it was: its cost and budget are out of date.
            return {"ok": True, "cost": 0, "budget_left": self.budget_left, **self.cache[doc_id], "cached": True}
        for attempt in range(6):
            r = self.http.post(f"/api/tools/{tool}", json=args)
            if r.status_code in (429, 423):  # rate limited, or round paused
                m = re.search(r"(?:after|in) (\d+)", r.text)
                wait = int(m.group(1)) if m else 2 ** attempt
                print(f"[case] {r.status_code}: waiting {wait} s")
                time.sleep(wait)
                continue
            data = r.json()
            if isinstance(data.get("budget_left"), int):
                self.budget_left = data["budget_left"]
            if tool == "open_document" and data.get("ok"):
                self.cache[data["id"]] = {k: data[k] for k in ("id", "source", "title", "body")}
            return data
        return {"ok": False, "error": "Gave up after several retries."}
