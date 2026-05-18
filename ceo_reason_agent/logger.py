"""
__Title__      : CEO performance analysis
__Author__     : Jyothirmai Chandolu
__Employee_id__: 800342
__Version__    : 1
__Description__: UUID-named structured logger that records every processing step with token counts and estimated LLM costs.
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path


# ── Pricing (USD per 1M tokens) ──────────────────────────────────────────────
MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o":          {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini":     {"input": 0.15,  "output": 0.60},
    "gpt-4-turbo":     {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo":   {"input": 0.50,  "output": 1.50},
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["gpt-4o-mini"])
    return (input_tokens / 1_000_000) * pricing["input"] + \
           (output_tokens / 1_000_000) * pricing["output"]


def setup_logger(log_dir: str = "logs") -> tuple[logging.Logger, str]:
    """
    Create a UUID-named log file and return (logger, log_file_path).
    Each run gets its own file: logs/ceo_reason_YYYYMMDD_<uuid8>.log
    """
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    run_id = uuid.uuid4().hex[:8]
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"ceo_reason_{date_str}_{run_id}.log")

    logger = logging.getLogger(f"ceo_reason.{run_id}")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler — full detail
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Console handler — INFO and above only
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    logger.info(f"Run ID      : {run_id}")
    logger.info(f"Log file    : {log_file}")
    logger.info(f"Started at  : {datetime.now(timezone.utc).isoformat()}")
    logger.info("-" * 70)

    return logger, log_file


def log_llm_call(
    logger: logging.Logger,
    step: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    extra: str = "",
) -> None:
    cost = estimate_cost(model, input_tokens, output_tokens)
    msg = (
        f"[LLM] {step} | model={model} | "
        f"in={input_tokens:,} out={output_tokens:,} tokens | "
        f"cost=${cost:.6f}"
    )
    if extra:
        msg += f" | {extra}"
    logger.debug(msg)


def log_step(logger: logging.Logger, ticker: str, ceo_name: str, step: str, detail: str = "") -> None:
    base = f"[{ticker}] {ceo_name[:30]:<30} | {step}"
    if detail:
        base += f" | {detail}"
    logger.debug(base)


def log_summary(
    logger: logging.Logger,
    total: int,
    processed: int,
    skipped: int,
    errors: int,
    total_input_tokens: int,
    total_output_tokens: int,
    model: str,
) -> None:
    total_cost = estimate_cost(model, total_input_tokens, total_output_tokens)
    logger.info("=" * 70)
    logger.info("RUN SUMMARY")
    logger.info(f"  Companies processed : {total}")
    logger.info(f"  CEO entries updated : {processed}")
    logger.info(f"  Skipped (no URL)    : {skipped}")
    logger.info(f"  Errors              : {errors}")
    logger.info(f"  Total input tokens  : {total_input_tokens:,}")
    logger.info(f"  Total output tokens : {total_output_tokens:,}")
    logger.info(f"  Estimated cost      : ${total_cost:.4f} (model: {model})")
    logger.info("=" * 70)
