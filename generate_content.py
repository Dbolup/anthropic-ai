#!/usr/bin/env python3
"""CLI entrypoint for the AI product content generation script.

Usage examples::

    # Generate content for all products in the default sample file
    python generate_content.py

    # Specify a custom input file and output directory
    python generate_content.py --input data/sample_products.json --output-dir data/output

    # Use a different Claude model
    python generate_content.py --model claude-opus-4-5

    # Pretty-print progress and save results
    python generate_content.py --verbose

Run ``python generate_content.py --help`` for the full option list.
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from product_content_generator import ProductContentGenerator
from product_content_generator.models import Product

DEFAULT_INPUT = Path(__file__).parent / "data" / "sample_products.json"
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "data" / "output"
DEFAULT_MODEL = "claude-opus-4-5"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate AI product descriptions and feature copy using Claude.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to the JSON file containing structured product data.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where generated content files will be saved.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Claude model identifier to use for generation.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Maximum tokens to generate per product.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds to wait between consecutive API calls.",
    )
    parser.add_argument(
        "--skip-errors",
        action="store_true",
        help="Log errors and continue rather than aborting on first failure.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging.",
    )
    return parser.parse_args(argv)


def load_products(path: Path) -> list[Product]:
    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)
    return [Product.from_dict(item) for item in raw]


def save_results(
    results: list[dict],
    output_dir: Path,
    run_id: str,
) -> tuple[Path, Path]:
    """Persist generation results to disk.

    Saves two files:
    * ``generated_content_<run_id>.json`` – full structured output.
    * ``generated_content_<run_id>_summary.jsonl`` – one JSON object per
      line, containing only the product identifier and generated text, for
      easy side-by-side blind review against a human-written baseline.

    Returns paths to both files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    full_path = output_dir / f"generated_content_{run_id}.json"
    with full_path.open("w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)

    summary_path = output_dir / f"generated_content_{run_id}_summary.jsonl"
    with summary_path.open("w", encoding="utf-8") as fh:
        for item in results:
            summary = {
                "product_id": item["product_id"],
                "product_name": item["product_name"],
                "description": item["description"],
                "feature_copy": item["feature_copy"],
            }
            fh.write(json.dumps(summary, ensure_ascii=False) + "\n")

    return full_path, summary_path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("generate_content")

    # ------------------------------------------------------------------ Load
    if not args.input.exists():
        logger.error("Input file not found: %s", args.input)
        return 1

    logger.info("Loading products from %s", args.input)
    products = load_products(args.input)
    logger.info("Loaded %d product(s)", len(products))

    # ---------------------------------------------------------------- Generate
    generator = ProductContentGenerator(
        model=args.model,
        max_tokens=args.max_tokens,
        delay=args.delay,
    )

    results: list[dict] = []
    total = len(products)
    errors = 0

    for idx, content in enumerate(
        generator.generate_batch(products, skip_errors=args.skip_errors), start=1
    ):
        results.append(content.to_dict())
        logger.info(
            "[%d/%d] ✓ %s – %s",
            idx,
            total,
            content.product_id,
            content.product_name,
        )
        if args.verbose:
            logger.debug("  Description: %s", content.description[:120])

    successful = len(results)
    errors = total - successful

    if not results:
        logger.error("No content was generated.")
        return 1

    # ------------------------------------------------------------------- Save
    run_id = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    full_path, summary_path = save_results(results, args.output_dir, run_id)

    logger.info("")
    logger.info("──────────────────────────────────────────")
    logger.info("Generation complete")
    logger.info("  Products processed : %d / %d", successful, total)
    if errors:
        logger.info("  Errors (skipped)   : %d", errors)
    total_tokens = sum(r["usage"]["total_tokens"] for r in results)
    logger.info("  Total tokens used  : %d", total_tokens)
    logger.info("  Full output        : %s", full_path)
    logger.info("  Review summary     : %s", summary_path)
    logger.info("──────────────────────────────────────────")

    return 0


if __name__ == "__main__":
    sys.exit(main())
