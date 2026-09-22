from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

USER = "MishanyAG"
OUT = Path("assets/activity.svg")


def get_weekly_public_commits() -> int:
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "mishanya-os",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(
        f"https://api.github.com/users/{USER}/events/public?per_page=100",
        headers=headers,
    )

    with urlopen(request, timeout=20) as response:
        events = json.load(response)

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    commits = 0

    for event in events:
        if event.get("type") != "PushEvent":
            continue

        created_at = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
        if created_at < cutoff:
            continue

        commits += len(event.get("payload", {}).get("commits", []))

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
    capacity = 25
    fill = min(count / capacity, 1.0)
    full_width = 790
    bar_width = max(8, int(full_width * fill))

    sweat = ""
    if count >= 8:
        sweat = """
        <circle cx="849" cy="52" r="4" fill="#58a6ff">
          <animate attributeName="cy" values="52;77;52" dur="1.5s" repeatCount="indefinite"/>
          <animate attributeName="opacity" values="1;0;1" dur="1.5s" repeatCount="indefinite"/>
        </circle>
        """

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="150" viewBox="0 0 900 150">
  <rect width="900" height="150" rx="18" fill="#0d1117"/>
  <rect x="1" y="1" width="898" height="148" rx="17" fill="none" stroke="#30363d"/>

  <g font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace">
    <text x="30" y="42" font-size="18" fill="#8b949e">weekly public commits</text>
    <text x="30" y="82" font-size="27" fill="#f0f6fc">{count}</text>
    <text x="78" y="82" font-size="18" fill="#8b949e">{status}</text>

    <text x="805" y="82" font-size="35">{face}</text>
    {sweat}

    <rect x="30" y="108" width="{full_width}" height="14" rx="7" fill="#21262d"/>
    <rect x="30" y="108" width="{bar_width}" height="14" rx="7" fill="#238636">
      <animate attributeName="width" from="8" to="{bar_width}" dur="0.9s" fill="freeze"/>
    </rect>

    <text x="830" y="120" font-size="13" fill="#8b949e">{min(count, capacity)}/{capacity}</text>
  </g>
</svg>"""


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    count = get_weekly_public_commits()
    OUT.write_text(render(count), encoding="utf-8")
    print(f"updated {OUT} with {count} commits")


if __name__ == "__main__":
    main()
