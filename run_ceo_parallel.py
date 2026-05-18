"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Runs CEO agent batches in parallel across multiple subprocess workers for any stock index.
"""

import json
import math
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


BATCH_SIZE = 100


def load_indices_config() -> dict:
    cfg_path = Path(__file__).parent / "data/indices_config.json"
    if cfg_path.exists():
        with open(cfg_path) as f:
            return json.load(f)
    return {}


def count_tickers(tickers_csv: str) -> int:
    import csv
    with open(tickers_csv, newline="") as f:
        return sum(1 for row in csv.DictReader(f) if row.get("ticker", "").strip())


def run_batch(index_key: str, batch_num: int) -> tuple[int, int]:
    """Run one batch as a subprocess. Returns (batch_num, returncode)."""
    cmd = [
        sys.executable, "-m", "ceo_agent.run",
        "--index", index_key,
        "--batch-num", str(batch_num),
        "batch",
    ]
    print(f"  [batch {batch_num}] Starting...")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return batch_num, result.returncode


def main() -> None:
    args = sys.argv[1:]

    # --index
    index_key = "russell2000"
    if "--index" in args:
        pos = args.index("--index")
        if pos + 1 < len(args):
            index_key = args[pos + 1].lower().strip()

    # --batches (e.g. --batches 1,3,5)
    explicit_batches: list[int] = []
    if "--batches" in args:
        pos = args.index("--batches")
        if pos + 1 < len(args):
            explicit_batches = [int(x) for x in args[pos + 1].split(",") if x.strip().isdigit()]

    # --workers (default: all batches in parallel)
    max_workers = None
    if "--workers" in args:
        pos = args.index("--workers")
        if pos + 1 < len(args):
            try:
                max_workers = int(args[pos + 1])
            except ValueError:
                pass

    # Resolve config
    cfg = load_indices_config()
    if cfg and index_key in cfg:
        idx_cfg = cfg[index_key]
        tickers_csv = idx_cfg.get("tickers_csv", "output.csv")
        index_name = idx_cfg.get("name", index_key)
    else:
        tickers_csv = "output.csv"
        index_name = index_key

    total_tickers = count_tickers(tickers_csv)
    total_batches = math.ceil(total_tickers / BATCH_SIZE)

    if explicit_batches:
        batch_nums = explicit_batches
    else:
        batch_nums = list(range(1, total_batches + 1))

    workers = max_workers or len(batch_nums)

    print("=" * 60)
    print(f"Parallel CEO Agent — {index_name}")
    print(f"Tickers    : {total_tickers}")
    print(f"Batches    : {batch_nums}")
    print(f"Workers    : {workers} concurrent")
    print("=" * 60)
    print()

    failed = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_batch, index_key, bn): bn for bn in batch_nums}
        for future in as_completed(futures):
            bn, rc = future.result()
            if rc == 0:
                print(f"  [batch {bn}] DONE ✓")
            else:
                print(f"  [batch {bn}] FAILED (exit {rc})")
                failed.append(bn)

    print()
    if failed:
        print(f"Failed batches: {failed}")
        print(f"Re-run: python run_ceo_parallel.py --index {index_key} --batches {','.join(map(str, failed))}")
    else:
        print("All batches complete. Rebuilding companies.json...")
        subprocess.run([
            sys.executable, "-m", "ceo_agent.run",
            "--index", index_key, "rebuild",
        ], cwd=Path(__file__).parent)
        print("Done.")


if __name__ == "__main__":
    main()
