from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

USER = "MishanyAG"
TEMPLATE = Path("assets/mishanya-os-template.svg")
OUT = Path("assets/mishanya-os-final.svg")


def api_get(url: str):
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "mishanya-os",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def get_weekly_public_commits() -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    since = cutoff.isoformat().replace("+00:00", "Z")

    repos = api_get(
        f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&sort=pushed"
    )

    commits = 0
    for repo in repos:
        if repo.get("private"):
            continue

        pushed_at = repo.get("pushed_at")
        if pushed_at:
            pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            if pushed < cutoff:
                continue

        params = urlencode({
            "author": USER,
            "since": since,
            "per_page": 100,
        })
        url = f"https://api.github.com/repos/{repo['full_name']}/commits?{params}"

        try:
            repo_commits = api_get(url)
        except HTTPError as exc:
            if exc.code in (409, 422):
                continue
            raise

        if isinstance(repo_commits, list):
            commits += len(repo_commits)

    return commits


def mood(count: int) -> tuple[str, str]:
    if count <= 2:
        return "😴", "hibernating peacefully"
    if count <= 7:
        return "🙂", "reasonable human activity"
    if count <= 14:
        return "😅", "okay, we're coding"
    if count <= 24:
        return "😰", "one last commit was a lie"
    return "🫠", "PLEASE STOP"


def render(count: int) -> str:
    face, status = mood(count)
    capped = min(count, 25)
    bar_width = max(8, int(705 * min(count / 25, 1.0)))

    sweat = ""
    if count >= 8:
        sweat = """<circle cx="832" cy="489" r="4" fill="#58a6ff">
      <animate attributeName="cy" values="489;515;489" dur="1.45s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="1;0;1" dur="1.45s" repeatCount="indefinite"/>
    </circle>"""

    svg = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "{{COUNT}}": str(count),
        "{{STATUS}}": status,
        "{{FACE}}": face,
        "{{SWEAT}}": sweat,
        "{{BAR_WIDTH}}": str(bar_width),
        "{{COUNT_CAPPED}}": str(capped),
    }
    for key, value in replacements.items():
        svg = svg.replace(key, value)
    return svg


def main() -> None:
    count = get_weekly_public_commits()
    OUT.write_text(render(count), encoding="utf-8")
    print(f"updated {OUT} with {count} public commits")


if __name__ == "__main__":
    main()
