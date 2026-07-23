# Remote Compute — running Phase 8+ sweeps at scale

**Purpose.** Phases 8+ (sum-free Cayley break-hunt, TFP showpieces, inflation pools, adversarial
search) need large instance-level parallelism. Development and small-scale tests run on the
author's Mac; the heavy sweeps run on a **rented remote Linux box** driven over SSH from the Mac.
The box is compute muscle only — no Claude Code, no dev work — a byte-faithful replica of the
pinned environment.

> **The live SSH endpoint is intentionally NOT in this (public) repo.** It is ephemeral (the box is
> rented; IP/port change on re-rent) and publishing an SSH address is poor hygiene. The current
> endpoint lives in the **gitignored `.compute-box`** file at the repo root (and in the author's
> local assistant memory). To reconnect after a re-rent, update `.compute-box`.

## Box requirements
- Ubuntu x86-64 (24.04 or 22.04), **plain public IP with key-based SSH** (avoid vast.ai — NAT'd
  instances route SSH through a proxy and cost hours; Hetzner / DigitalOcean / Vultr "just work").
- ≥16 cores to start (the confirmable break window n≈31–200 is modest); more cores = wider sweep.
- The author's SSH public key pasted in at instance creation so `ssh root@<ip>` works first try.

## Provision (one command, ~5–10 min)
From the box shell (or `ssh … "…"` from the Mac):
```bash
git clone https://github.com/altancansu/hadwiger-alpha2.git
bash hadwiger-alpha2/scripts/setup.sh
```
`scripts/setup.sh` is idempotent. Known Ubuntu gotchas it/we handle: nauty installs binaries
**prefixed** (`nauty-geng` → symlink to `geng`); pinned **Python 3.12.13 needs a current `uv`**
(reinstall via the astral script if stale); test tools need **`uv sync --all-extras --all-groups`**
(not just `--extra nauty`).

## Verify the box is a faithful replica
```bash
cd hadwiger-alpha2 && uv run pytest -q -m "not slow"
```
Must pass, including the **296-corpus byte-fingerprint** — that test is the proof this box
reproduces the canonical Linux x86_64 reference platform.

## Run a sweep (drive from the Mac)
```bash
cd hadwiger-alpha2 && git pull --ff-only && uv sync --all-extras --all-groups
tmux new -s sweep            # detach: Ctrl-b d | reattach: tmux attach -t sweep
uv run pytest -n "$(nproc)" -m slow        # generation / has_cdm: full cores
# CP-SAT-heavy stages: back off -n to fit RAM (watch htop)
```

## Discipline (non-negotiable)
- Instance-level parallelism only. **`num_workers=1` + pinned seed on ANY reported
  impossibility / INFEASIBLE / RESISTANT verdict** (CP-SAT #3590/#3842/#4839).
- **Deterministic solver budgets** (`max_deterministic_time` for CP-SAT, `maxNodes`/`det_nodes`
  for CBC) — never wall-clock — so DECIDED-vs-RESISTANT is a function of `(n, seed)`, not machine
  speed. Mandatory on shared/variable CPUs.
- The box is rented and bills hourly. **Stop it when idle**; re-provision in minutes with the steps
  above.

## Loop summary
Implement/test on the Mac → `git push` → box `git pull && uv sync --all-extras --all-groups` →
run sweep in `tmux` → results committed/pulled back to the Mac.
