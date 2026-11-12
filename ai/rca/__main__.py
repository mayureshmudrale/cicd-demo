"""Standalone RCA run: python -m ai.rca --service idea-board-backend --minutes 5

Not wired into any pipeline yet (that lands with the sim harness / CI
features); this is the same `analyze()` a future workflow step will call.
"""
import argparse
import time

from .analyze import analyze


def main() -> None:
    """Parses CLI args, runs `analyze` over the trailing window, prints the report."""
    parser = argparse.ArgumentParser(description="Root cause analysis over a recent time window")
    parser.add_argument("--service", default="idea-board-backend")
    parser.add_argument("--minutes", type=int, default=5)
    args = parser.parse_args()

    end = int(time.time())
    start = end - args.minutes * 60
    report = analyze(args.service, start, end)
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
