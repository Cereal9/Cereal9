#!/usr/bin/env python3
"""Render profile stat cards as SVG in the palette defined by assets/STYLE.md.

Queries the GitHub GraphQL API and writes four files:
  assets/stats-dark.svg   assets/stats-light.svg
  assets/langs-dark.svg   assets/langs-light.svg

Run locally with:  GH_TOKEN=$(gh auth token) python3 scripts/build_stats.py
The stats workflow runs the same command on a schedule.

Token scope decides what the cards show. The default GITHUB_TOKEN in Actions can
only see public repositories, which hides any work living in private ones. Add a
classic PAT with repo and read:user scope as the PROFILE_TOKEN secret to count
private work too.
"""

import json
import os
import sys
import urllib.request
from collections import Counter

USER = os.environ.get("GH_USER", "Cereal9")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

SANS = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', Ubuntu, "
        "Helvetica, Arial, sans-serif")

THEMES = {
    "dark": {
        "bg": "#0D1117", "border": "#21262D", "title": "#00B4D8",
        "text": "#C9D1D9", "muted": "#8B949E", "track": "#161B22",
        "ramp": ["#00B4D8", "#48CAE4", "#0077B6", "#90E0EF", "#023E8A"],
    },
    "light": {
        "bg": "#FFFFFF", "border": "#D0D7DE", "title": "#0077B6",
        "text": "#1F2328", "muted": "#57606A", "track": "#F6F8FA",
        "ramp": ["#0077B6", "#00B4D8", "#023E8A", "#48CAE4", "#0096C7"],
    },
}

QUERY = """
query($login:String!) {
  user(login:$login) {
    followers { totalCount }
    repositories(ownerAffiliations:OWNER, first:100, isFork:false) {
      totalCount
      nodes {
        stargazerCount
        languages(first:10, orderBy:{field:SIZE, direction:DESC}) {
          edges { size node { name } }
        }
      }
    }
    pullRequests { totalCount }
    issues { totalCount }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar { totalContributions }
    }
  }
}
"""


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": f"{USER}-profile-stats",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        sys.exit(f"GraphQL error: {payload['errors']}")
    return payload["data"]["user"]


def summarize(user):
    repos = user["repositories"]
    langs = Counter()
    stars = 0
    for node in repos["nodes"]:
        stars += node["stargazerCount"]
        for edge in node["languages"]["edges"]:
            langs[edge["node"]["name"]] += edge["size"]
    contrib = user["contributionsCollection"]
    return {
        "contributions": contrib["contributionCalendar"]["totalContributions"],
        "commits": contrib["totalCommitContributions"],
        "repos": repos["totalCount"],
        "stars": stars,
        "prs": user["pullRequests"]["totalCount"],
        "followers": user["followers"]["totalCount"],
        "langs": langs,
    }


def human(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + "m"
    if n >= 1_000:
        return f"{n / 1_000:.1f}".rstrip("0").rstrip(".") + "k"
    return str(n)


def shell(theme, width, height, title):
    t = THEMES[theme]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{title}">\n'
        f'  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="4.5" '
        f'fill="{t["bg"]}" stroke="{t["border"]}"/>\n'
        f'  <g font-family="{SANS}">\n'
        f'    <text x="25" y="34" font-size="18" font-weight="600" '
        f'fill="{t["title"]}">{title}</text>\n'
    )


def stats_card(theme, s):
    t = THEMES[theme]
    cells = [
        ("Contributions", s["contributions"]), ("Commits", s["commits"]),
        ("Repositories", s["repos"]), ("Stars", s["stars"]),
        ("Pull Requests", s["prs"]), ("Followers", s["followers"]),
    ]
    svg = shell(theme, 400, 165, "GitHub Stats")
    for i, (label, value) in enumerate(cells):
        x = 25 + (i % 2) * 190
        y = 70 + (i // 2) * 33
        svg += (
            f'    <text x="{x}" y="{y}" font-size="20" font-weight="600" '
            f'fill="{t["text"]}">{human(value)}</text>\n'
            f'    <text x="{x}" y="{y + 15}" font-size="11" letter-spacing="0.4" '
            f'fill="{t["muted"]}">{label.upper()}</text>\n'
        )
    return svg + "  </g>\n</svg>\n"


def langs_card(theme, s):
    t = THEMES[theme]
    total = sum(s["langs"].values()) or 1
    top = s["langs"].most_common(5)
    shown = sum(v for _, v in top)
    rows = [(name, size / total * 100) for name, size in top]
    if total - shown > 0:
        rows.append(("Other", (total - shown) / total * 100))

    svg = shell(theme, 400, 165, "Top Languages")
    svg += (f'    <clipPath id="bar-{theme}"><rect x="25" y="50" width="350" '
            f'height="10" rx="5"/></clipPath>\n')
    svg += (f'    <rect x="25" y="50" width="350" height="10" rx="5" '
            f'fill="{t["track"]}"/>\n    <g clip-path="url(#bar-{theme})">\n')

    offset = 25.0
    for i, (_, pct) in enumerate(rows):
        seg = 350 * pct / 100
        color = t["ramp"][i] if i < len(t["ramp"]) else t["muted"]
        svg += (f'      <rect x="{offset:.1f}" y="50" width="{seg:.1f}" '
                f'height="10" fill="{color}"/>\n')
        offset += seg
    svg += "    </g>\n"

    for i, (name, pct) in enumerate(rows):
        x = 25 + (i % 2) * 190
        y = 92 + (i // 2) * 24
        color = t["ramp"][i] if i < len(t["ramp"]) else t["muted"]
        label = name if len(name) <= 12 else name[:12]
        svg += (
            f'    <rect x="{x}" y="{y - 9}" width="9" height="9" rx="2" fill="{color}"/>\n'
            f'    <text x="{x + 17}" y="{y}" font-size="13" font-weight="600" '
            f'fill="{t["text"]}">{label}</text>\n'
            f'    <text x="{x + 120}" y="{y}" font-size="13" text-anchor="end" '
            f'fill="{t["muted"]}">{pct:.1f}%</text>\n'
        )
    return svg + "  </g>\n</svg>\n"


def main():
    if not TOKEN:
        sys.exit("set GH_TOKEN or GITHUB_TOKEN")
    s = summarize(fetch())
    for theme in THEMES:
        for name, svg in (("stats", stats_card(theme, s)),
                          ("langs", langs_card(theme, s))):
            path = os.path.join(OUT, f"{name}-{theme}.svg")
            with open(path, "w") as fh:
                fh.write(svg)
            print(f"wrote {path}")
    print(f"contributions={s['contributions']} commits={s['commits']} "
          f"repos={s['repos']} stars={s['stars']}")


if __name__ == "__main__":
    main()
