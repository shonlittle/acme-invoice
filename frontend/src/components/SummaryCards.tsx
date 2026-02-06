import type { PipelineResult } from "../types";

interface Props {
  result: PipelineResult;
}

export default function SummaryCards({ result }: Props) {
  const inv = result.invoice;
  const approval = result.approval_decision;
  const payment = result.payment_result;
  const findings = result.validation_findings;

  const errorCount = findings.filter((f) => f.severity === "ERROR").length;
  const warnCount = findings.filter((f) => f.severity === "WARN").length;
  const revisionLabel = inv?.revision ? `🔄 Yes (${inv.revision})` : "No";

  return (
    <div className="summary-cards">
      <div className="card">
        <div className="card-label">Vendor</div>
        <div className="card-value">{inv?.vendor ?? "—"}</div>
      </div>

      <div className="card">
        <div className="card-label">Total Amount</div>
        <div className="card-value">
          {inv ? `$${inv.amount.toLocaleString()}` : "—"}
        </div>
      </div>

      <div className="card">
        <div className="card-label">Due Date</div>
        <div className="card-value">{inv?.due_date ?? "—"}</div>
      </div>

      <div className="card">
        <div className="card-label">Findings</div>
        <div className="card-value">
          {findings.length} total
          {errorCount > 0 && (
            <span className="badge badge-error"> {errorCount} ERR</span>
          )}
          {warnCount > 0 && (
            <span className="badge badge-warn"> {warnCount} WARN</span>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-label">Approved?</div>
        <div className="card-value">
          {approval ? (
            <span className={approval.approved ? "text-ok" : "text-fail"}>
              {approval.approved ? "✅ Yes" : "❌ No"}
            </span>
          ) : (
            "—"
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-label">Revised?</div>
        <div className="card-value">{revisionLabel}</div>
      </div>

      <div className="card">
        <div className="card-label">Payment</div>
        <div className="card-value">
          {payment ? (
            <span
              className={payment.status === "PAID" ? "text-ok" : "text-neutral"}
            >
              {payment.status}
            </span>
          ) : (
            "—"
          )}
        </div>
      </div>

      {result.errors.length > 0 && (
        <div className="card card-wide">
          <div className="card-label">Errors</div>
          <div className="card-value text-fail">{result.errors.join("; ")}</div>
        </div>
      )}
    </div>
  );
}
