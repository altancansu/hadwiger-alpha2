"""The `alpha2` CLI — argparse subcommands, thin dispatch, zero new deps (V5).

A thin controller (`corpus/manifest.py:main` + every `repro/*.main()` analog): it validates
input via argparse `choices`/`type=` (ASVS V5 — `--family` in {known pools}, `--n` a positive
int, `--seed` an int) and DELEGATES to `battery.pipeline.run_candidate`. No math, no runbook
orchestration lives here. The registered entry point (`pyproject.toml [project.scripts]`) calls
`alpha2.cli:main`. Raises-only; no `assert` on the CLI path (survives ``python -O``).
"""
import argparse
import json

from alpha2.battery import pipeline


def _positive_int(value):
    parsed = int(value)   # argparse wraps ValueError as an ArgumentTypeError itself
    if parsed < 1:
        raise argparse.ArgumentTypeError(f"must be a positive int, got {parsed}")
    return parsed


def build_parser():
    """The argparse parser: `alpha2 battery --family ... --n ... --seed ...`."""
    parser = argparse.ArgumentParser(
        prog="alpha2", description="The alpha=2 kill battery."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    battery = sub.add_parser(
        "battery", help="run the 7-step runbook on one candidate (deterministic in n, seed)"
    )
    battery.add_argument(
        "--family", choices=pipeline.FAMILIES, required=True,
        help="candidate pool (V5: restricted to known pools)",
    )
    battery.add_argument("--n", type=_positive_int, required=True, help="order n (positive int)")
    battery.add_argument("--seed", type=int, required=True, help="RNG seed (int)")
    battery.add_argument(
        "--budget-heuristic", type=float, default=None,
        help="step-3 heuristic time budget in seconds (config, echoed into the log)",
    )
    battery.add_argument(
        "--budget-had2", type=float, default=None,
        help="step-4 exact had_2 time budget in seconds (per backend)",
    )
    battery.add_argument(
        "--budget-had3", type=float, default=None,
        help="step-5 had_3 escalation time budget in seconds",
    )
    battery.set_defaults(func=_run_battery)
    return parser


def _run_battery(args):
    """Dispatch the `battery` subcommand: build Budgets, run, print a JSON summary line."""
    defaults = pipeline.Budgets()
    budgets = pipeline.Budgets(
        heuristic=(args.budget_heuristic if args.budget_heuristic is not None
                   else defaults.heuristic),
        had2=(args.budget_had2 if args.budget_had2 is not None else defaults.had2),
        had3=(args.budget_had3 if args.budget_had3 is not None else defaults.had3),
    )
    result = pipeline.run_candidate(args.family, args.n, args.seed, budgets=budgets)
    print(json.dumps(result, sort_keys=True))
    return result


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    main()
