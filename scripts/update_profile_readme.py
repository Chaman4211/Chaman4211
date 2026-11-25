#!/usr/bin/env python3
"""Refresh the public repository portfolio section in the profile README."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USERNAME = "Chaman4211"
README_PATH = Path("README.md")
START = "<!-- AUTO-REPOSITORIES:START -->"
END = "<!-- AUTO-REPOSITORIES:END -->"
API_URL = f"https://api.github.com/users/{USERNAME}/repos?type=public&sort=updated&direction=desc&per_page=100"


def fetch_repositories() -> list[dict]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Chaman4211-profile-readme-updater",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(API_URL, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        repositories = json.loads(response.read().decode("utf-8"))

    # Keep the portfolio focused on original, active public repositories.
    return [
        repo for repo in repositories
        if not repo.get("fork") and not repo.get("archived")
        and repo.get("name") != USERNAME
    ]


def build_section(repositories: list[dict]) -> str:
    if not repositories:
        return "_No public project repositories were returned by the GitHub API._"

    rows = [
        "| Repository | Description | Language | ⭐ Stars | Last updated |",
        "|---|---|---:|---:|---|",
    ]
    for repo in repositories:
        name = repo["name"]
        url = repo["html_url"]
        description = (repo.get("description") or "No description added yet.")
        description = " ".join(description.split()).replace("|", "\\|")
        if len(description) > 110:
            description = description[:107].rstrip() + "..."
        language = repo.get("language") or "—"
        stars = repo.get("stargazers_count", 0)
        updated_at = repo.get("pushed_at") or repo.get("updated_at")
        if updated_at:
            try:
                updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                date_text = updated.astimezone(timezone.utc).strftime("%d %b %Y")
            except ValueError:
                date_text = "—"
        else:
            date_text = "—"
        rows.append(
            f"| [**{name}**]({url}) | {description} | {language} | {stars} | {date_text} |"
        )

    generated_at = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    return "\n".join(rows) + f"\n\n<sub>Automatically refreshed: {generated_at} · Showing {len(repositories)} public, non-fork, non-archived repositories.</sub>"


def main() -> None:
    readme = README_PATH.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        raise SystemExit("README auto-repository markers are missing; refusing to overwrite content.")

    before, remainder = readme.split(START, 1)
    _, after = remainder.split(END, 1)
    replacement = f"{START}\n{build_section(fetch_repositories())}\n{END}"
    new_readme = before + replacement + after
    if new_readme != readme:
        README_PATH.write_text(new_readme, encoding="utf-8")
        print("README repository portfolio updated.")
    else:
        print("README repository portfolio is already up to date.")


if __name__ == "__main__":
    main()
