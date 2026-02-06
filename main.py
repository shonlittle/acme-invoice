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
        required=False,
        help="Path to invoice file to process",
    )
    parser.add_argument(
        "--run_all",
        action="store_true",
        help="Run pipeline on all sample invoices in data/invoices/",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="out",
        help="Directory to save result JSON (default: out)",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.run_all and not args.invoice_path:
        parser.error("Either --invoice_path or --run_all must be specified")

    if args.run_all and args.invoice_path:
        parser.error("Cannot specify both --invoice_path and --run_all")

    # Handle --run_all mode
    if args.run_all:
        import glob
        from pathlib import Path

        invoice_files = (
            glob.glob("data/invoices/*.json")
            + glob.glob("data/invoices/*.csv")
            + glob.glob("data/invoices/*.txt")
            + glob.glob("data/invoices/*.pdf")
        )

        print(f"\n{'='*90}")
        print(f"Running pipeline on {len(invoice_files)} sample invoices")
        print(f"{'='*90}\n")

        results = []
        for invoice_path in sorted(invoice_files):
            try:
                result = run_pipeline(invoice_path)

                # Save result to output directory
                output_dir = Path(args.output_dir)
                output_dir.mkdir(exist_ok=True)

                invoice_id = Path(invoice_path).stem
                output_path = output_dir / f"{invoice_id}.json"

                result_dict = serialize_result(result)
                with open(output_path, "w") as f:
                    json.dump(result_dict, f, indent=2)

                results.append(
                    {
                        "file": Path(invoice_path).name,
                        "vendor": result.invoice.vendor if result.invoice else "N/A",
                        "amount": result.invoice.amount if result.invoice else 0.0,
                        "approved": (
                            result.approval_decision.approved
                            if result.approval_decision
                            else None
                        ),
                        "paid": (
                            result.payment_result.status == "PAID"
                            if result.payment_result
                            else False
                        ),
                        "errors": len(result.errors),
                    }
                )
            except Exception as e:
                print(f"ERROR processing {Path(invoice_path).name}: {e}")
                results.append(
                    {
                        "file": Path(invoice_path).name,
                        "vendor": "ERROR",
                        "amount": 0.0,
                        "approved": False,
                        "paid": False,
                        "errors": 999,
                    }
                )

        # Print summary
        print(f"\n{'='*90}")
        print("SUMMARY")
        print(f"{'='*90}\n")
        print(f"{'File':<30} {'Vendor':<25} {'Amount':>10} {'Approved':>9} {'Paid':>5}")
        print("-" * 90)

        for r in results:
            approved_str = str(r["approved"]) if r["approved"] is not None else "N/A"
            paid_str = "Yes" if r["paid"] else "No"
            print(
                f"{r['file']:<30} {r['vendor']:<25} ${r['amount']:>9.2f} {approved_str:>9} {paid_str:>5}"
            )

        print(f"\n{'='*90}")
        print(f"Total files processed: {len(results)}")
        print(f"Results saved to: {args.output_dir}/")
        print(f"{'='*90}\n")

        return

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

    # Always save to output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    output_filename = f"{invoice_path.stem}.json"
    output_path = output_dir / output_filename

    with open(output_path, "w") as f:
        f.write(result_json)

    print(f"Result saved to: {output_path}\n")

    # Exit with error code if pipeline had errors
    if result.errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
