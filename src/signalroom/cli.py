from __future__ import annotations

import argparse

from .config import CaseConfig
from .pipeline import build_case


def main() -> None:
    parser = argparse.ArgumentParser(prog="signalroom")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build", help="Build one evidence bundle")
    build.add_argument("--config", required=True)
    build.add_argument("--output-root", default="artifacts/cases")
    build.add_argument("--cache-dir", default="data/cache/statsbomb")
    args = parser.parse_args()
    if args.command == "build":
        config = CaseConfig.from_toml(args.config)
        result = build_case(config, args.output_root, args.cache_dir)
        print(f"Built {result}")


if __name__ == "__main__":
    main()
