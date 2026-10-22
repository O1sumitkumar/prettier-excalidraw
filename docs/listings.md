# Where to list prettier-excalidraw

Directories and marketplaces where Claude Code skills and plugins are listed, as
checked on 2026-10-22. Nothing has been submitted yet; the texts below are ready to
paste. "Last activity" is the repository's last push (GitHub API) or the site's own
refresh claim.

Install commands used in every text:

```
/plugin marketplace add Raihan-009/prettier-excalidraw
/plugin install prettier-excalidraw@prettier-excalidraw
```

Repo: https://github.com/Raihan-009/prettier-excalidraw

## Summary

| # | Directory | URL | How to submit | What it needs | Last activity / maintained? |
|---|---|---|---|---|---|
| 1 | Anthropic plugin directory (claude.ai / claude.com Marketplace, Cowork + Claude Code) | https://claude.com/docs/plugins/submit → portal https://claude.ai/directory/manage | Web form in the developer portal: "Submit new" → "Plugin bundle" | Public GitHub repo, `.claude-plugin/plugin.json` (present, v0.4.0), README (listing text is taken from both), `claude plugin validate .` passing, data-handling answers, contact email, four acknowledgements; GitHub account connected to claude.ai with push rights | Yes. Official; `anthropics/claude-plugins-official` pushed 2026-10-22 |
| 2 | Anthropic community marketplace (`anthropics/claude-plugins-community`, installs as `@claude-community`) | https://github.com/anthropics/claude-plugins-community | Same form as #1 (`clau.de/plugin-directory-submission` → claude.com/docs/directory/publish). Direct PRs are auto-closed | Same as #1; passes automated security scan, then approval | Yes. Read-only mirror synced nightly; pushed 2026-10-22; 4.7k stars |
| 3 | skills.sh (Vercel, open agent-skills ecosystem; what `find-skills` and `npx skills find` search) | https://skills.sh | No form. Skills are indexed from the GitHub repo once people install with `npx skills add Raihan-009/prettier-excalidraw`; ranked by install count | `skills/<name>/SKILL.md` with `name` + `description` frontmatter (present) | Yes. `vercel-labs/skills` pushed 2026-10-19, 36k stars; leaderboard has 24h "Trending" tab |
| 4 | awesome-claude-code (hesreallyhim) | https://github.com/hesreallyhim/awesome-claude-code | GitHub issue form only (`recommend-resource.yml`); PRs are not accepted; one resource per issue, must be filed by a human via the web UI | Repo ≥ 14 days old with commits after day one, or ≥ 100 stars; open source; a bot checks the license; category "Skills"; 10–500 char neutral description | Yes. Pushed 2026-10-22; 56k stars |
| 5 | awesome-claude-skills (ComposioHQ) | https://github.com/ComposioHQ/awesome-claude-skills | Pull request titled "Add [Skill Name] skill" | Their CONTRIBUTING asks for a skill *folder* with a `SKILL.md` vendored into the repo plus a README bullet under one of five categories ("Development" or "Productivity & Organization"); must be a real, tested use case with attribution | Yes. Pushed 2026-09-18; 78k stars |
| 6 | awesome-agent-skills (VoltAgent; "1000+ agent skills") | https://github.com/VoltAgent/awesome-agent-skills | Pull request (contribution rules not verified; the old `awesome-claude-skills` URL redirects here) | A README bullet with link and one-line description | Yes. Pushed 2026-10-20; 36k stars |
| 7 | awesome-claude-skills (BehiSecc) | https://github.com/BehiSecc/awesome-claude-skills | Fork + pull request | README bullet `- [name](url) - one sentence` under "Development & Code Tools" (where the other diagram skill lives); 14 categories, no CONTRIBUTING.md | Yes. Pushed 2026-09-21; 10k stars |
| 8 | awesome-claude-skills (travisvn) | https://github.com/travisvn/awesome-claude-skills | Pull request reviewed by the maintainer | README bullet | Stale: last push 2026-04-28 (six months); 15k stars |
| 9 | awesome-claude-skills (karanb192) | https://github.com/karanb192/awesome-claude-skills | Pull request | README bullet; "50+ verified" list, MIT | Yes but small. Pushed 2026-10-02; 558 stars |
| 10 | claudemarketplaces.com (independent, "not affiliated with Anthropic") | https://claudemarketplaces.com | No form. Crawls GitHub daily for `.claude-plugin/marketplace.json` and `SKILL.md`; manual editor sweeps; "Feedback" link in the footer | Public repo with the plugin/marketplace manifests (present) | Yes. Claims daily refresh; 2,734 marketplaces, 23.7k skills listed; run by mertbuilds.com |
| 11 | OpenSkillIndex | https://openskillindex.com | No form found. Weekly crawl; per-skill source + content hash | Public `SKILL.md` | Appears live (weekly crawl claim); operator not named; could not verify how new repos enter the crawl |

Not a venue: `anthropics/skills` (182k stars) is Anthropic's own example-skills repo and
its marketplace, not a third-party directory.

## Submission texts

### 1 / 2. Anthropic plugin directory and community marketplace

Portal: https://claude.ai/directory/manage → "Submit new" → "Plugin bundle". Run
`claude plugin validate .` from the repo root first. Listing name and short
description are read from `.claude-plugin/plugin.json` and the README, so the text
below is for the "description" / notes fields where the form asks for them.

> prettier-excalidraw turns a plain-language request into an Excalidraw architecture
> diagram that already looks like one careful person drew it: no sketchy lines, one
> font, one arrow style, a small palette of light fills that mean something, regions
> that contain their children, logos sized to their boxes, and arrows never hidden
> behind a box. It also lints and fixes existing `.excalidraw` files without moving
> anything. Standard-library Python only, no network needed beyond optional logo
> fetches from Simple Icons.
>
> Install in Claude Code:
> `/plugin marketplace add Raihan-009/prettier-excalidraw` then
> `/plugin install prettier-excalidraw@prettier-excalidraw`
>
> Repo: https://github.com/Raihan-009/prettier-excalidraw

Data-handling answers, for the form: reads no personal data, stores nothing, sends
nothing to third-party services except an optional HTTPS fetch of SVG logos from
simpleicons.org and of fonts from the Excalidraw GitHub repo (cached locally); not
intended for under-18s.

### 3. skills.sh

Nothing to submit. The skill is picked up once installed through the Skills CLI;
the text below is for a README or announcement that points people there.

> prettier-excalidraw is a Claude Code skill that builds clean, consistent Excalidraw
> architecture diagrams from a short JSON spec or a plain-language request, and lints
> or restyles existing `.excalidraw` files. One font, hollow-triangle elbow arrows,
> light colour-coded boxes, tinted regions, correct z-order and real logos.
>
> `npx skills add Raihan-009/prettier-excalidraw` (any agent), or in Claude Code:
> `/plugin marketplace add Raihan-009/prettier-excalidraw` then
> `/plugin install prettier-excalidraw@prettier-excalidraw`
>
> Repo: https://github.com/Raihan-009/prettier-excalidraw

### 4. awesome-claude-code (issue form)

Fields: Display Name `prettier-excalidraw`; Category `Skills`; Link
`https://github.com/Raihan-009/prettier-excalidraw`; Author Name `Raihan Islam`;
Author Link `https://github.com/Raihan-009`. The description must be neutral, not
address the reader, 10–500 characters, and the repo must be at least 14 days old
with commits after its first day (or have 100 stars) before filing. The repo was
created 2026-10-21, so the earliest filing date is 2026-11-04.

> Builds Excalidraw architecture diagrams from a JSON spec in a measured, consistent
> house style (one font, elbow arrows with hollow heads, light semantic fills, tinted
> regions, sized logos, correct z-order) and lints or fixes existing `.excalidraw`
> files against the same rules. Ships as a Claude Code plugin with standard-library
> Python scripts.

Install (for the issue body, if asked):
`/plugin marketplace add Raihan-009/prettier-excalidraw` then
`/plugin install prettier-excalidraw@prettier-excalidraw`.

### 5. ComposioHQ/awesome-claude-skills (PR)

Their guide expects a vendored copy of `skills/prettier-excalidraw/` as a folder in
the list repo plus this README line under **Development** (alphabetical), PR title
"Add prettier-excalidraw skill":

```markdown
- [prettier-excalidraw](./prettier-excalidraw/) - Build, lint and restyle Excalidraw architecture diagrams in a clean, consistent house style from a JSON spec or a plain-language request. Inspired by [Raihan Islam](https://github.com/Raihan-009).
```

PR description:

> Adds prettier-excalidraw, a skill that makes Excalidraw architecture diagrams look
> like one careful person drew them: one font, one arrow style, light fills with
> meaning, regions that contain their children, logos sized to their boxes, arrows
> never hidden. Used by platform and backend engineers who draw system diagrams for
> design docs; tested in Claude Code. Source and Claude Code plugin:
> https://github.com/Raihan-009/prettier-excalidraw (install with
> `/plugin marketplace add Raihan-009/prettier-excalidraw` then
> `/plugin install prettier-excalidraw@prettier-excalidraw`).

### 6 / 7 / 8 / 9. Other awesome lists (PR, one README bullet)

Entry line (adjust the heading to the list's nearest category: "Development & Code
Tools" on BehiSecc, "Development" or "Productivity" elsewhere):

```markdown
- [prettier-excalidraw](https://github.com/Raihan-009/prettier-excalidraw) - Build, lint and restyle Excalidraw architecture diagrams in a clean, consistent house style: one font, hollow-triangle elbow arrows, light colour-coded boxes, tinted regions, sized logos and correct z-order.
```

PR description:

> Adds prettier-excalidraw, a Claude Code skill and plugin for Excalidraw
> architecture diagrams. It builds a `.excalidraw` from a small JSON spec, and lints
> or fixes existing files against a style measured from real diagrams, without
> moving anything. Install: `/plugin marketplace add Raihan-009/prettier-excalidraw`
> then `/plugin install prettier-excalidraw@prettier-excalidraw`.
> Repo: https://github.com/Raihan-009/prettier-excalidraw

### 10 / 11. claudemarketplaces.com and OpenSkillIndex

No submission step; both crawl public GitHub repos. If the plugin has not appeared
after a week, use the site's Feedback link with:

> Please index prettier-excalidraw, a Claude Code skill/plugin that builds and lints
> Excalidraw architecture diagrams in a consistent house style. Marketplace manifest
> at `.claude-plugin/marketplace.json`, skill at `skills/prettier-excalidraw/SKILL.md`.
> Install: `/plugin marketplace add Raihan-009/prettier-excalidraw` then
> `/plugin install prettier-excalidraw@prettier-excalidraw`.
> Repo: https://github.com/Raihan-009/prettier-excalidraw

## Not verified

- Whether skills.sh indexes a repo before anyone installs it; the site documents no
  submission path, only install-count ranking.
- VoltAgent/awesome-agent-skills contribution rules (only the redirect, star count
  and push date were checked).
- ComposioHQ's list may accept link-only entries in practice; its CONTRIBUTING asks
  for a vendored skill folder.
- OpenSkillIndex's operator and how new repos enter its weekly crawl.
- The claude.ai developer portal needs a signed-in account (returns 403 to anonymous
  requests), so its form fields are taken from the docs page, not the live form.
