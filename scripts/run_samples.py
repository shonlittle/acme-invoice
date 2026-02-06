#!/usr/bin/env python3
"""
Run pipeline on multiple sample invoices and print summary table.

Usage:
    python3 scripts/run_samples.py
"""

import glob
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.runner import run_pipeline


def main():
    """Run pipeline on all sample invoices and print summary."""
    # Find all supported invoice files
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
    for path in sorted(invoice_files):
        try:
            result = run_pipeline(path)
            results.append(
                {
                    "file": Path(path).name,
                    "vendor": result.invoice.vendor if result.invoice else "N/A",
                    "total": result.invoice.amount if result.invoice else 0.0,
                    "items": (len(result.invoice.line_items) if result.invoice else 0),
                    "errors": len(result.validation_findings),
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
                }
            )
        except Exception as e:
            results.append(
                {
                    "file": Path(path).name,
                    "vendor": "ERROR",
                    "total": 0.0,
                    "items": 0,
                    "errors": 999,
                    "approved": False,
                    "paid": False,
                }
            )
            print(f"ERROR processing {Path(path).name}: {e}")

    # Print summary table
    print(f"\n{'='*90}")
    print("SUMMARY")
    print(f"{'='*90}\n")
    print(
        f"{'File':<30} {'Vendor':<25} {'Total':>10} {'Items':>6} {'Errors':>7} {'Approved':>9} {'Paid':>5}"
    )
    print("-" * 90)

    for r in results:
        approved_str = str(r["approved"]) if r["approved"] is not None else "N/A"
        paid_str = "Yes" if r["paid"] else "No"
        print(
            f"{r['file']:<30} {r['vendor']:<25} ${r['total']:>9.2f} {r['items']:>6} {r['errors']:>7} {approved_str:>9} {paid_str:>5}"
        )

    print(f"\n{'='*90}")
    print(f"Total files processed: {len(results)}")
    print(
        f"Successful parses: {sum(1 for r in results if r['vendor'] != 'ERROR' and r['vendor'] != 'PARSE_ERROR')}"
    )
    print(
        f"Parse errors: {sum(1 for r in results if r['vendor'] in ['ERROR', 'PARSE_ERROR'])}"
    )
    print(f"Validation errors: {sum(r['errors'] for r in results)}")

    # Approval metrics
    approved_count = sum(1 for r in results if r["approved"] is True)
    rejected_count = sum(1 for r in results if r["approved"] is False)
    pending_count = sum(1 for r in results if r["approved"] is None)

    # Payment metrics
    paid_count = sum(1 for r in results if r["paid"] is True)

    if len(results) > 0:
        print(
            f"Approval rate: {approved_count}/{len(results)} ({approved_count/len(results)*100:.1f}%)"
        )
        print(
            f"Rejection rate: {rejected_count}/{len(results)} ({rejected_count/len(results)*100:.1f}%)"
        )
        print(
            f"Pending rate: {pending_count}/{len(results)} ({pending_count/len(results)*100:.1f}%)"
        )
        if approved_count > 0:
            print(
                f"Payment rate: {paid_count}/{approved_count} approved invoices paid ({paid_count/approved_count*100:.1f}%)"
            )
        else:
            print(f"Payment rate: {paid_count}/0 approved invoices paid (0.0%)")

    print(f"{'='*90}\n")


if __name__ == "__main__":
    main()
