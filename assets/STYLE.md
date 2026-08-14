# Profile Visual Style

One palette, one card shape, one type scale. Every surface in the README is built
from the tokens below, so generated cards and hand-made SVGs read as one system.

## Color

| Token | Dark | Light | Used for |
| :--- | :--- | :--- | :--- |
| Surface | `#0D1117` | `#FFFFFF` | card and banner backgrounds |
| Surface raised | `#161B22` | `#F6F8FA` | badges, chips |
| Border | `#21262D` | `#D0D7DE` | every card outline, 1px |
| Text | `#C9D1D9` / `#E6EDF3` | `#1F2328` | headings, values |
| Muted | `#8B949E` | `#57606A` | labels, secondary copy |
| Accent | `#00B4D8` | `#0077B6` | titles, rings, markers |
| Accent light | `#48CAE4` | `#0096C7` | badge logos, highlights |
| Accent deep | `#023E8A` | `#023E8A` | gradient anchor |

Accent ramp: `#023E8A` to `#0077B6` to `#00B4D8` to `#48CAE4` to `#90E0EF`.
Gradients move along that ramp only, never across hues.

## Shape and spacing

- Cards: 1px border, radius 4.5 (matches github-readme-stats defaults)
- Banner: radius 14, 5px accent bar on the left edge
- Card padding: 25px; row rhythm: 25px
- All stat cards render at `height="170"` so rows line up

## Type

- Identity and headings in the banner: system monospace, 44px bold, 3px tracking
- Card titles: system sans, 18px, weight 600, accent color
- Labels: 13px weight 600 in text color; values 13px regular in muted

## Badges

Uniform shields.io chips instead of brand colors:
`style=flat-square`, `labelColor=161B22`, `color=161B22`, `logoColor=48CAE4`.
The LinkedIn badge is the one filled accent chip, so it reads as the primary action.

## Theme handling

Every image ships a dark and light variant behind a `<picture>` element keyed to
`prefers-color-scheme`. Editing a color means editing it in three places: this file,
the two SVG variants, and the card query strings in the README.

## Cards and where they come from

| Card | Source | Palette control |
| :--- | :--- | :--- |
| GitHub stats | `scripts/build_stats.py`, refreshed daily by Actions | built from these tokens |
| Top languages | `scripts/build_stats.py`, refreshed daily by Actions | built from these tokens |
| Current focus | hand-written `assets/focus-*.svg` | built from these tokens |
| Banner | hand-written `assets/banner-*.svg` | built from these tokens |
| Streak | `streak-stats.demolab.com` | full hex control via query string |
| Activity graph | `github-readme-activity-graph.vercel.app` | full hex control via query string |
| Snake | `Platane/snk` action, published to the `output` branch | snake and dot colors from the accent ramp |
| Badges | `img.shields.io` | uniform chips, see above |

Four of the eight are generated inside this repo, which is deliberate. The widely
used `github-readme-stats.vercel.app` returns `DEPLOYMENT_PAUSED` and
`github-profile-trophy.vercel.app` returns `402 Payment Required`, so any card that
depends on someone else's free Vercel quota can disappear without warning.

## Regenerating the stat cards

    GH_TOKEN=$(gh auth token) python3 scripts/build_stats.py

`.github/workflows/stats.yml` runs the same command daily at 06:17 UTC and commits
the SVGs only when the numbers change. `.github/workflows/snake.yml` regenerates the
contribution snake nightly and pushes it to the `output` branch.

Adding a metric means editing the `cells` list in `stats_card`. The card is a fixed
400 by 165 with a two column by three row grid, so a seventh metric needs the grid
geometry adjusted, not just a new entry.

## A note on token scope

The stats workflow falls back to the built-in `GITHUB_TOKEN`, which can only see
public repositories. On this account that produces a misleading language card,
because the C and firmware work sits in private repos while the public ones are
coursework and a website, so HTML and CSS float to the top.

To count private work, create a classic personal access token with `repo` and
`read:user` scope, save it as a repository secret named `PROFILE_TOKEN`, and rerun
the workflow. The script picks it up automatically.
