# Governance — Rural Connectivity Mapper

This document describes the governance model for the Rural Connectivity Mapper project. Our goal is transparent, community-driven decision-making that keeps the project sustainable and welcoming.

## 1. Principles

1. **Openness** — All design decisions, roadmaps, and financials are public.
2. **Meritocratic participation** — Influence grows with sustained, quality contributions.
3. **Community first** — The primary stakeholders are rural communities, not vendors.
4. **Consensus-seeking** — Decisions are made through discussion; voting is the last resort.

## 2. Roles & Responsibilities

### 2.1 Project Lead (Benevolent Dictator for now)

| Who | Responsibility |
|-----|---------------|
| **Daniel Azevedo Novais** (`@daniel-azezedo-novais`) | Final say on architecture, releases, and community health |

The project currently follows a **Benevolent Dictator** model. As the community grows, we will transition to a **Steering Committee** (see §6 — Evolution Path).

### 2.2 Maintainers

Maintainers have commit and release rights. They are listed in [CODEOWNERS](.github/CODEOWNERS).

**How to become a maintainer:**
1. Sustained contributions (code, docs, reviews) over 3+ months.
2. Nomination by an existing maintainer.
3. Approval by the Project Lead (or future Steering Committee).

### 2.3 Committers

Committers can approve and merge pull requests in their area of expertise but cannot cut releases.

**How to become a committer:**
1. At least 5 merged PRs with good quality.
2. Demonstrated understanding of the project's architecture and conventions.
3. Nomination by a maintainer.

### 2.4 Contributors

Anyone who submits a PR, opens an issue, improves documentation, or participates in discussions. All contributors are recognized in the [Contributors](#8-recognition) section.

### 2.5 Community Members

Anyone who uses the project, reports bugs, asks questions, or provides feedback. Community members are essential to the project's success and are welcome to participate in all public discussions.

## 3. Decision-Making Process

### 3.1 Everyday Decisions

- Bug fixes, small improvements, documentation updates → **Maintainer approval** via PR review.
- No formal vote required.

### 3.2 Significant Decisions

For architecture changes, new data sources, breaking API changes, or governance updates:

1. **Proposal** — Open a GitHub Discussion (category: "RFC") or create an ADR (see [docs/adr/](docs/adr/)).
2. **Discussion period** — Minimum 7 calendar days for community feedback.
3. **Consensus** — Maintainers seek consensus. If none is reached, the Project Lead decides.
4. **Record** — Decision is recorded as an ADR and linked in the PR.

### 3.3 Voting (last resort)

If consensus cannot be reached:
- Each maintainer gets one vote.
- Simple majority wins (ties broken by Project Lead).
- Votes are public and recorded in the relevant issue/discussion.

## 4. Contribution Workflow

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full developer workflow. Summary:

1. Fork → branch → implement → test → PR.
2. All PRs require at least **1 maintainer review**.
3. Significant changes require an **ADR** or **RFC discussion**.
4. CI must pass (linting, types, tests).
5. Conventional commits are required.

## 5. Release Process

| Type | Cadence | Who |
|------|---------|-----|
| **Patch** (`x.y.Z`) | As needed (bug/security fixes) | Any maintainer |
| **Minor** (`x.Y.0`) | Monthly or milestone-based | Project Lead or release manager |
| **Major** (`X.0.0`) | Announced 30 days ahead; requires RFC | Project Lead + maintainer consensus |

Releases follow [Semantic Versioning 2.0.0](https://semver.org/). Each release is tagged (`vX.Y.Z`) and automatically published via the GitHub Actions [release workflow](.github/workflows/release.yml).

### Changelog

Every release includes auto-generated release notes. Significant changes are also documented in [CHANGELOG.md](CHANGELOG.md).

## 6. Evolution Path

As the project grows, governance will evolve:

| Community Size | Governance Model | Trigger |
|---------------|------------------|---------|
| 1–3 active contributors | **Benevolent Dictator** (current) | — |
| 4–10 active contributors | **Maintainer Council** (3–5 members) | 3+ sustained contributors |
| 10+ active contributors | **Steering Committee** + Working Groups | Community vote to adopt charter |
| Foundation-ready | **Open Source Foundation** (e.g., Linux Foundation, NumFOCUS) | Formal application + sponsor |

## 7. Code of Conduct

All participants must follow our [Code of Conduct](CODE_OF_CONDUCT.md). Violations are handled by the Project Lead (or future Conduct Committee).

## 8. Recognition

We value every contribution. Contributors are recognized through:

- **GitHub Contributors graph** (automatic)
- **Release notes** (PRs cited)
- **CONTRIBUTORS.md** (opt-in hall of fame)
- **Committer/Maintainer promotion** (sustained contributors)

## 9. Communication Channels

| Channel | Purpose |
|---------|---------|
| **GitHub Issues** | Bug reports, feature requests |
| **GitHub Discussions** | RFCs, Q&A, community conversations |
| **Pull Requests** | Code review, technical discussion |
| **ADRs** (`docs/adr/`) | Architecture decision records |

## 10. Amendments

This governance document can be amended through the standard RFC process (§3.2). Changes require at least 14 days of discussion and maintainer consensus.

---

*Last updated: 2026-04-08*
