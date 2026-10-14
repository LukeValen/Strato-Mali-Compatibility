#!/usr/bin/env python3
"""Build a static, reviewed compatibility feed from GitHub Issues."""
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REPO = "LukeValen/Strato-Mali-Compatibility"
APPROVAL_LABEL = "compatibility-approved"
ISSUE_URL = re.compile(r"https://github\.com/LukeValen/Strato-Mali-Compatibility/issues/\d+\Z")
TITLE_ID = re.compile(r"[0-9A-F]{16}\Z")
STATUS = {"Playable": "playable", "In-game": "ingame", "Boots": "boots", "Nothing": "nothing", "Unplayable": "unplayable"}
HEADINGS = {"Game": "title", "Jogo": "title", "Title ID": "titleId", "Mali GPU": "gpu", "GPU Mali": "gpu",
            "Vulkan driver": "driver", "Driver Vulkan": "driver", "Strato Mali version": "emulatorVersion",
            "Versão do Strato Mali": "emulatorVersion", "Status": "status", "Rating": "stars", "Nota": "stars",
            "Notes": "notes", "Observações": "notes"}


def parse_body(body):
    """Parse the headings rendered by GitHub's issue form, not the issue title."""
    values = {}
    current = None
    for line in body.splitlines():
        match = re.fullmatch(r"### (.+)", line.strip())
        if match:
            current = HEADINGS.get(match.group(1))
            if current:
                values[current] = ""
        elif current:
            values[current] += line + "\n"
    return {key: value.strip() for key, value in values.items()}


def parse_issue(issue):
    if issue.get("pull_request") or not any(label.get("name") == APPROVAL_LABEL for label in issue.get("labels", [])):
        return None
    values = parse_body(issue.get("body") or "")
    title_id = values.get("titleId", "").removeprefix("0x").upper()
    url = issue.get("html_url", "")
    star_match = re.fullmatch(r"([0-5]) (?:estrelas?|stars?)", values.get("stars", ""))
    status = STATUS.get(values.get("status"))
    if not (TITLE_ID.fullmatch(title_id) and ISSUE_URL.fullmatch(url) and star_match and status):
        return None
    title = values.get("title", "")
    gpu = values.get("gpu", "")
    driver = values.get("driver", "")
    version = values.get("emulatorVersion", "")
    notes = values.get("notes", "")
    if not (1 <= len(title) <= 120 and 1 <= len(gpu) <= 100 and 1 <= len(driver) <= 120 and
            1 <= len(version) <= 80 and len(notes) <= 1000 and notes != "_No response_"):
        return None
    created = issue.get("created_at", "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", created):
        return None
    return {"titleId": title_id, "title": title, "gpu": gpu, "driver": driver,
            "emulatorVersion": version, "status": status, "stars": int(star_match.group(1)),
            "notes": notes, "date": created[:10], "url": url}


def fetch_approved(token):
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required for publication")
    issues = []
    for page in range(1, 101):
        query = urlencode({"state": "all", "labels": APPROVAL_LABEL, "per_page": 100, "page": page})
        request = Request(f"https://api.github.com/repos/{REPO}/issues?{query}", headers={
            "Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "Strato-Mali-Compatibility-Pages"})
        with urlopen(request, timeout=30) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise RuntimeError("GitHub returned an invalid issue list")
        issues.extend(batch)
        if len(batch) < 100:
            return issues
    raise RuntimeError("More than 10,000 approved issues; refusing an incomplete list")


def build(issues, destination):
    reviews = [parsed for issue in issues if (parsed := parse_issue(issue)) is not None]
    reviews.sort(key=lambda review: (review["titleId"], review["date"], int(review["url"].rsplit("/", 1)[1])))
    payload = {"generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), "reviews": reviews}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Published {len(reviews)} reviewed reports from {len(issues)} labeled issues")


if __name__ == "__main__":
    build(fetch_approved(os.environ.get("GITHUB_TOKEN")), Path(sys.argv[1] if len(sys.argv) > 1 else "dist/data/reviews.json"))
