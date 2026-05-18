"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: CLI entry point for the CEO reason agent. Processes one or more batch JSON files, enriching each CEO entry with a reason and exit classification.

Usage:
  # Process default file (sec_ceo_data_sp500/agent_batch_001.json)
  python -m ceo_reason_agent.run

  # Specify input file
  python -m ceo_reason_agent.run --input sec_ceo_data_sp500/agent_batch_001.json

  # Write output to a separate file (default: overwrites input with _enriched suffix)
  python -m ceo_reason_agent.run --input agent_batch_001.json --output agent_batch_001_enriched.json

  # Process all batches in a directory
  python -m ceo_reason_agent.run --dir sec_ceo_data_sp500

  # Use a different model
  python -m ceo_reason_agent.run --model gpt-4o

  # Dry-run: process only first N companies
  python -m ceo_reason_agent.run --limit 5

Output:
  logs/ceo_reason_YYYYMMDD_HHMMSS_<uuid8>.log
  <output_path>.json  (enriched with reason + exit_classification fields)
"""

import argparse
import glob
import os
import sys
from pathlib import Path

# Allow running from project root as  python -m ceo_reason_agent.run
sys.path.insert(0, str(Path(__file__).parent.parent))

from ceo_reason_agent.logger import setup_logger
from ceo_reason_agent.processor import process_batch
from ceo_reason_agent.llm import MODEL


def _default_output(input_path: str) -> str:
    p = Path(input_path)
    return str(p.parent / (p.stem + "_enriched" + p.suffix))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enrich CEO batch JSON files with transition reasons and exit classifications."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--input", "-i",
        default="sec_ceo_data_sp500/agent_batch_001.json",
        help="Path to a single batch JSON file (default: sec_ceo_data_sp500/agent_batch_001.json)",
    )
    group.add_argument(
        "--dir", "-d",
        help="Directory containing agent_batch_*.json files — processes all of them.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output path (default: <input>_enriched.json). Ignored when --dir is used.",
    )
    parser.add_argument(
        "--model", "-m",
        default=MODEL,
        help=f"OpenAI model to use (default: {MODEL})",
    )
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=None,
        help="Process only the first N companies (useful for testing)",
    )
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory for log files (default: logs/)",
    )
    args = parser.parse_args()

    logger, log_file = setup_logger(log_dir=args.log_dir)

    # Build list of (input, output) pairs
    jobs: list[tuple[str, str]] = []

    if args.dir:
        pattern = os.path.join(args.dir, "agent_batch_*.json")
        # Exclude already-enriched files
        files = sorted(
            f for f in glob.glob(pattern)
            if "_enriched" not in f and "_progress" not in f
        )
        if not files:
            logger.error(f"No agent_batch_*.json files found in {args.dir}")
            sys.exit(1)
        logger.info(f"Found {len(files)} batch files in {args.dir}")
        for f in files:
            jobs.append((f, _default_output(f)))
    else:
        output = args.output or _default_output(args.input)
        jobs.append((args.input, output))

    logger.info(f"Jobs to process: {len(jobs)}")
    for inp, out in jobs:
        logger.info(f"  {inp}  →  {out}")
    logger.info("")

    for inp, out in jobs:
        logger.info(f"{'='*70}")
        logger.info(f"Processing: {inp}")
        logger.info(f"{'='*70}")
        try:
            process_batch(
                input_path=inp,
                output_path=out,
                model=args.model,
                logger=logger,
                limit=args.limit,
            )
        except Exception as exc:
            logger.exception(f"Fatal error processing {inp}: {exc}")

    logger.info(f"All done. Log: {log_file}")


if __name__ == "__main__":
    main()
