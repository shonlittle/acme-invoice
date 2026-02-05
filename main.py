#!/usr/bin/env python3
"""
Invoice Processing Pipeline - CLI Entrypoint

Usage:
    python main.py --invoice_path=data/invoices/invoice_1001.txt

Outputs:
- Structured logs to console
- Final PipelineResult as JSON to console
- Optional: Result JSON to out/ directory
"""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from pipeline.runner import run_pipeline


def serialize_result(result) -> dict:
    """
    Convert PipelineResult to JSON-serializable dict.

    Handles dataclass serialization recursively.
    """

    def convert(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return {k: convert(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [convert(item) for item in obj]
        return obj

    return convert(result)


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Invoice Processing Pipeline")
    parser.add_argument(
        "--invoice_path",
        type=str,
        required=True,
        help="Path to invoice file to process",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="out",
        help="Directory to save result JSON (default: out)",
    )
    parser.add_argument(
        "--save_result",
        action="store_true",
        help="Save result JSON to output directory",
    )

    args = parser.parse_args()

    # Validate invoice path exists
    invoice_path = Path(args.invoice_path)
    if not invoice_path.exists():
        print(f"ERROR: Invoice file not found: {args.invoice_path}")
        sys.exit(1)

    # Run pipeline
    print(f"\n{'='*60}")
    print(f"Processing invoice: {args.invoice_path}")
    print(f"{'='*60}\n")

    result = run_pipeline(str(invoice_path))

    # Convert to JSON
    result_dict = serialize_result(result)
    result_json = json.dumps(result_dict, indent=2)

    # Print final result
    print(f"\n{'='*60}")
    print("PIPELINE RESULT")
    print(f"{'='*60}\n")
    print(result_json)
    print()

    # Save to file if requested
    if args.save_result:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)

        output_filename = f"{invoice_path.stem}_result.json"
        output_path = output_dir / output_filename

        with open(output_path, "w") as f:
            f.write(result_json)

        print(f"Result saved to: {output_path}\n")

    # Exit with error code if pipeline had errors
    if result.errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
