#!/usr/bin/env python3
"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: Generates a token usage and cost report across all indices from batch output files and token usage logs.
"""

import csv
import glob
import json
import os
import sys
from datetime import datetime

# ── Pricing (USD per 1M tokens) ──────────────────────────────────────────────
PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    # aliases
    "gpt-4o-2024-08-06": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini-2024-07-18": {"input": 0.15, "output": 0.60},
}

ROOT = os.path.dirname(__file__)

# Discover all ceo_data_dirs from indices_config.json
def _ceo_data_dirs() -> dict[str, str]:
    cfg_path = os.path.join(ROOT, "data", "indices_config.json")
    dirs: dict[str, str] = {}
    if os.path.exists(cfg_path):
        with open(cfg_path) as f:
            cfg = json.load(f)
        for key, val in cfg.items():
            d = val.get("ceo_data_dir", "")
            if d:
                dirs[key] = os.path.join(ROOT, d)
    # Fallback: always include default
    if not dirs:
        dirs["russell2000"] = os.path.join(ROOT, "sec_ceo_data")
    return dirs

CEO_DATA_DIRS = _ceo_data_dirs()
# Collect all token log paths
TOKEN_LOGS = {name: os.path.join(d, "token_usage.jsonl") for name, d in CEO_DATA_DIRS.items()}

# ── Estimation constants (derived from observed batch data) ──────────────────
# Each company averages ~6 ReAct turns on MODEL_STRONG.
# Per turn: avg ~4 500 input tokens (growing history) and ~250 output tokens.
# Each company also triggers ~2 MODEL_FAST extract() calls (fallback / search).
AVG_TURNS_PER_COMPANY = 6
AVG_INPUT_PER_TURN_STRONG = 4_500   # tokens
AVG_OUTPUT_PER_TURN_STRONG = 250    # tokens
AVG_FAST_CALLS_PER_COMPANY = 2
AVG_INPUT_PER_FAST_CALL = 1_500    # tokens
AVG_OUTPUT_PER_FAST_CALL = 200     # tokens


def cost(model: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICING.get(model, PRICING["gpt-4o"])
    return (input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000


# ── Section 1: actual logged usage ───────────────────────────────────────────
def load_actual_usage() -> list[dict]:
    rows = []
    for index_name, log_path in TOKEN_LOGS.items():
        if not os.path.exists(log_path):
            continue
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        r = json.loads(line)
                        r["index"] = index_name
                        rows.append(r)
                    except json.JSONDecodeError:
                        pass
    return rows


# ── Section 2: estimated usage from existing batch JSON files ─────────────────
def estimate_batch_usage() -> list[dict]:
    """
    For each completed batch file across all indices, estimate token usage
    based on company count and CEO timeline complexity.
    """
    rows = []
    for index_name, data_dir in CEO_DATA_DIRS.items():
        batch_files = sorted(glob.glob(os.path.join(data_dir, "agent_batch_*.json")))
        batch_files = [f for f in batch_files if "_progress" not in f]

        for bf in batch_files:
            batch_name = os.path.basename(bf)
            try:
                with open(bf) as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            n_companies = len(data)
            n_ceo_entries = sum(len(c.get("ceo_timeline", [])) for c in data)
            avg_ceos = n_ceo_entries / n_companies if n_companies else 2.5
            turn_multiplier = max(1.0, avg_ceos / 2.5)

            turns = int(n_companies * AVG_TURNS_PER_COMPANY * turn_multiplier)
            strong_input = turns * AVG_INPUT_PER_TURN_STRONG
            strong_output = turns * AVG_OUTPUT_PER_TURN_STRONG

            fast_calls = int(n_companies * AVG_FAST_CALLS_PER_COMPANY)
            fast_input = fast_calls * AVG_INPUT_PER_FAST_CALL
            fast_output = fast_calls * AVG_OUTPUT_PER_FAST_CALL

            mtime = datetime.fromtimestamp(os.path.getmtime(bf)).strftime("%Y-%m-%d")

            rows.append({
                "source": f"estimate:{index_name}/{batch_name}",
                "date": mtime,
                "index": index_name,
                "model": "gpt-4o",
                "input_tokens": strong_input,
                "output_tokens": strong_output,
                "companies": n_companies,
                "note": f"{n_companies} companies, {n_ceo_entries} CEO entries (estimated)",
            })
            rows.append({
                "source": f"estimate:{index_name}/{batch_name}",
                "date": mtime,
                "index": index_name,
                "model": "gpt-4o-mini",
                "input_tokens": fast_input,
                "output_tokens": fast_output,
                "companies": n_companies,
                "note": f"{n_companies} companies, {fast_calls} extract() calls (estimated)",
            })

    return rows


# ── Reporting ─────────────────────────────────────────────────────────────────
def build_report() -> tuple[list[dict], dict]:
    actual = load_actual_usage()
    estimated = estimate_batch_usage()

    rows: list[dict] = []

    for r in actual:
        model = r.get("model", "gpt-4o")
        inp = r.get("input_tokens", 0)
        out = r.get("output_tokens", 0)
        rows.append({
            "source": "actual",
            "date": r.get("ts", "")[:10],
            "index": r.get("index", ""),
            "model": model,
            "input_tokens": inp,
            "output_tokens": out,
            "cost_usd": round(cost(model, inp, out), 6),
            "companies": "",
            "note": "logged by llm.py",
        })

    for r in estimated:
        model = r["model"]
        inp = r["input_tokens"]
        out = r["output_tokens"]
        rows.append({
            "source": r["source"],
            "date": r["date"],
            "index": r.get("index", ""),
            "model": model,
            "input_tokens": inp,
            "output_tokens": out,
            "cost_usd": round(cost(model, inp, out), 6),
            "companies": r["companies"],
            "note": r["note"],
        })

    # Totals by index × model
    by_index: dict[str, dict] = {}
    for r in rows:
        idx = r.get("index") or "unknown"
        m = r["model"]
        key = f"{idx}/{m}"
        if key not in by_index:
            by_index[key] = {"index": idx, "model": m, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
        by_index[key]["input_tokens"] += r["input_tokens"]
        by_index[key]["output_tokens"] += r["output_tokens"]
        by_index[key]["cost_usd"] += r["cost_usd"]

    # Totals per model (across indices)
    by_model: dict[str, dict] = {}
    for r in rows:
        m = r["model"]
        if m not in by_model:
            by_model[m] = {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
        by_model[m]["input_tokens"] += r["input_tokens"]
        by_model[m]["output_tokens"] += r["output_tokens"]
        by_model[m]["cost_usd"] += r["cost_usd"]

    grand_total = {
        "input_tokens": sum(v["input_tokens"] for v in by_model.values()),
        "output_tokens": sum(v["output_tokens"] for v in by_model.values()),
        "cost_usd": sum(v["cost_usd"] for v in by_model.values()),
    }

    return rows, {"by_index": by_index, "by_model": by_model, "grand_total": grand_total}


def write_csv(rows: list[dict], path: str) -> None:
    fields = ["source", "date", "index", "model", "input_tokens", "output_tokens", "cost_usd", "companies", "note"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def print_summary(summary: dict) -> None:
    W = 68
    print("\n" + "=" * W)
    print("  TOKEN USAGE & COST REPORT")
    print("=" * W)

    # Per-index breakdown
    print(f"\n  {'Index':<14} {'Model':<18} {'Input Tokens':>14} {'Output Tokens':>14} {'Cost':>10}")
    print(f"  {'-'*14} {'-'*18} {'-'*14} {'-'*14} {'-'*10}")
    for vals in sorted(summary["by_index"].values(), key=lambda x: (x["index"], x["model"])):
        print(f"  {vals['index']:<14} {vals['model']:<18} {vals['input_tokens']:>14,} {vals['output_tokens']:>14,} ${vals['cost_usd']:>9.4f}")

    print(f"\n  {'Model':<33} {'Input Tokens':>14} {'Output Tokens':>14} {'Cost':>10}")
    print(f"  {'-'*33} {'-'*14} {'-'*14} {'-'*10}")
    for model, vals in summary["by_model"].items():
        print(f"  {model:<33} {vals['input_tokens']:>14,} {vals['output_tokens']:>14,} ${vals['cost_usd']:>9.4f}")
    print(f"  {'-'*33} {'-'*14} {'-'*14} {'-'*10}")
    gt = summary["grand_total"]
    print(f"  {'GRAND TOTAL':<33} {gt['input_tokens']:>14,} {gt['output_tokens']:>14,} ${gt['cost_usd']:>9.4f}")
    print(f"\n  All pre-existing batches are ESTIMATES (usage was not stored).")
    print(f"  Future runs log actual usage to <ceo_data_dir>/token_usage.jsonl")
    print("=" * W + "\n")


def main() -> None:
    out_path = "cost_report.csv"
    if "--out" in sys.argv:
        idx = sys.argv.index("--out")
        if idx + 1 < len(sys.argv):
            out_path = sys.argv[idx + 1]

    rows, summary = build_report()
    write_csv(rows, out_path)
    print_summary(summary)
    print(f"  Detailed CSV written to: {out_path}")


if __name__ == "__main__":
    main()
