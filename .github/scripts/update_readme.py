#!/usr/bin/env python3
"""Update README.md with recent GitHub activity and a last-updated timestamp.

Run by the scheduled GitHub Actions workflow. It reads the public event feed
for the configured user and injects the results between the marker comments.
"""

import datetime
import re
import sys
import urllib.request
import urllib.error
import json

USERNAME = "alvaschul"
README = "README.md"
EVENTS_URL = f"https://api.github.com/users/{USERNAME}/events/public"
MAX_EVENTS = 5

START_ACTIVITY = "<!--START_SECTION:recent_activity-->"
END_ACTIVITY = "<!--END_SECTION:recent_activity-->"
START_UPDATED = "<!--START_SECTION:last_updated-->"
END_UPDATED = "<!--END_SECTION:last_updated-->"


def fetch_events():
    req = urllib.request.Request(
        EVENTS_URL,
        headers={"User-Agent": "readme-updater", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def format_event(event):
    repo = event.get("repo", {}).get("name", "unknown/unknown")
    etype = event.get("type", "Event")
    link = f"https://github.com/{repo}"
    created = event.get("created_at", "")[:10]
    return f"- [{repo}]({link}) &mdash; {etype} _{created}_"


def build_activity(events):
    items = []
    for ev in events[:MAX_EVENTS]:
        try:
            items.append(format_event(ev))
        except Exception:  # noqa: BLE001 - skip malformed entries
            continue
    if not items:
        return "\n_No recent public activity._\n"
    return "\n" + "\n".join(items) + "\n"


def replace_section(text, start, end, content):
    pattern = re.compile(
        re.escape(start) + r".*?" + re.escape(end), re.DOTALL
    )
    replacement = start + content + end
    if pattern.search(text):
        return pattern.sub(replacement, text)
    return text


def main():
    with open(README, encoding="utf-8") as f:
        text = f.read()

    try:
        events = fetch_events()
        activity = build_activity(events)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as exc:
        print(f"Warning: could not fetch events ({exc}); keeping existing section.")
        activity = None

    if activity is not None:
        text = replace_section(text, START_ACTIVITY, END_ACTIVITY, activity)

    today = datetime.date.today().isoformat()
    updated = f'\n<p align="center"><sub>Last updated: {today}</sub></p>\n'
    text = replace_section(text, START_UPDATED, END_UPDATED, updated)

    with open(README, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"README updated on {today}.")


if __name__ == "__main__":
    sys.exit(main())
