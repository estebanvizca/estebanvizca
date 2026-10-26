#!/usr/bin/env python3
"""Generate assets/github-analytics.svg from the public GitHub API.

No third-party service: the card is committed to the repo, so it can never
render as a broken external image. Run by .github/workflows/analytics.yml
monthly, or by hand with `python3 scripts/generate_analytics.py`.

Set GITHUB_TOKEN to raise the API rate limit (optional when run locally).
"""

import json
import os
import urllib.request
from datetime import datetime, timezone

USER = "estebanvizca"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "github-analytics.svg")

# Repos that are infrastructure rather than portfolio projects.
NON_PROJECT = {USER, f"{USER}.github.io"}

API = "https://api.github.com"


def get(path):
    req = urllib.request.Request(
        API + path,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USER}-analytics",
            **(
                {"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}"}
                if os.environ.get("GITHUB_TOKEN")
                else {}
            ),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main():
    user = get(f"/users/{USER}")
    repos = []
    page = 1
    while True:
        batch = get(f"/users/{USER}/repos?per_page=100&page={page}&sort=updated")
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    languages = {}
    project_repos = []
    stars = 0

    for repo in repos:
        if repo.get("fork"):
            continue
        stars += repo.get("stargazers_count", 0)
        if repo["name"] not in NON_PROJECT:
            project_repos.append(repo)
        try:
            for name, size in get(f"/repos/{USER}/{repo['name']}/languages").items():
                languages[name] = languages.get(name, 0) + size
        except Exception as error:  # keep the card even if one repo fails
            print(f"warning: languages for {repo['name']}: {error}")

    total_bytes = sum(languages.values()) or 1
    top = sorted(languages.items(), key=lambda item: item[1], reverse=True)[:4]

    public_repos = user.get("public_repos", len(repos))
    project_count = len(project_repos)
    lang_count = len(languages)

    # ---------- SVG ----------
    width, height = 1000, 244
    bar_x, bar_w = 596, 296
    rows = []
    for index, (name, size) in enumerate(top):
        pct = size / total_bytes * 100
        y = 104 + index * 30
        w = max(4, round(bar_w * size / total_bytes))
        rows.append(
            f'<text x="520" y="{y + 8}" class="lang">{esc(name)}</text>'
            f'<rect x="{bar_x}" y="{y}" width="{bar_w}" height="7" rx="3.5" fill="#1b2637"/>'
            f'<rect x="{bar_x}" y="{y}" width="{w}" height="7" rx="3.5" fill="url(#bar)"/>'
            f'<text x="956" y="{y + 8}" class="pct" text-anchor="end">{pct:.1f}%</text>'
        )

    stats = [
        (44, "PUBLIC REPOSITORIES", f"{public_repos:02d}"),
        (206, "PROJECT REPOSITORIES", f"{project_count:02d}"),
        (368, "LANGUAGES", f"{lang_count:02d}"),
    ]
    stat_svg = "".join(
        f'<text x="{x}" y="114" class="value">{esc(value)}</text>'
        f'<text x="{x}" y="140" class="caption">{esc(label)}</text>'
        for x, label, value in stats
    )

    updated = datetime.now(timezone.utc).strftime("%b %Y")

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t">
  <title id="t">GitHub analytics for {USER}: {public_repos} public repositories, {project_count} project repositories, {lang_count} languages. Main language: {esc(top[0][0]) if top else "n/a"}.</title>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0b1220"/>
      <stop offset="1" stop-color="#0d1728"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#14b8a6" stop-opacity="0.13"/>
      <stop offset="1" stop-color="#14b8a6" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#2dd4bf"/>
      <stop offset="1" stop-color="#8b5cf6"/>
    </linearGradient>
    <linearGradient id="line" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#14b8a6" stop-opacity="0.7"/>
      <stop offset="0.6" stop-color="#8b5cf6" stop-opacity="0.35"/>
      <stop offset="1" stop-color="#8b5cf6" stop-opacity="0"/>
    </linearGradient>
    <style>
      .label {{ font: 600 10px "Inter", "Segoe UI", Helvetica, Arial, sans-serif; letter-spacing: 1.8px; fill: #64748b; }}
      .value {{ font: 800 42px "Inter", "Segoe UI", Helvetica, Arial, sans-serif; letter-spacing: -1.5px; fill: #f1f5f9; }}
      .caption {{ font: 600 9.5px "Inter", "Segoe UI", Helvetica, Arial, sans-serif; letter-spacing: 1.4px; fill: #7c8ba1; }}
      .lang {{ font: 500 11.5px "Inter", "Segoe UI", Helvetica, Arial, sans-serif; fill: #cbd5e1; }}
      .pct {{ font: 500 11px "JetBrains Mono", ui-monospace, Menlo, monospace; fill: #94a3b8; }}
      .head {{ font: 500 10.5px "JetBrains Mono", ui-monospace, Menlo, monospace; letter-spacing: 1.2px; fill: #64748b; }}
    </style>
  </defs>

  <rect width="{width}" height="{height}" rx="14" fill="url(#bg)" stroke="#1f2a3a"/>
  <rect width="{width}" height="{height}" rx="14" fill="url(#glow)"/>

  <text x="44" y="42" class="head">GITHUB ANALYTICS</text>
  <text x="956" y="42" class="head" text-anchor="end">@{USER.upper()}</text>

  {stat_svg}

  <line x1="470" y1="70" x2="470" y2="176" stroke="#1f2a3a"/>

  <text x="520" y="72" class="label">LANGUAGES BY CODE VOLUME</text>
  {"".join(rows)}

  <line x1="0" y1="{height - 2}" x2="{width}" y2="{height - 2}" fill="none" stroke="url(#line)" stroke-width="2"/>
  <text x="44" y="222" class="caption">UPDATED {updated.upper()} · PUBLIC DATA ONLY · NO THIRD-PARTY SERVICES</text>
</svg>
'''

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as handle:
        handle.write(svg)

    print(
        f"wrote {OUT} — {public_repos} repos, {project_count} projects, "
        f"{lang_count} languages, {len(top)} bars"
    )


if __name__ == "__main__":
    main()
