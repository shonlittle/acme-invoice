import type { PipelineResult } from "../types";

interface Props {
  result: PipelineResult;
}

export default function MetricsPanel({ result }: Props) {
  const findings = result.validation_findings;
  const approval = result.approval_decision;

  // Group findings by code
  const findingsByCode: Record<string, number> = {};
  findings.forEach((f) => {
    findingsByCode[f.code] = (findingsByCode[f.code] || 0) + 1;
  });

  // Group findings by severity
  const findingsBySeverity: Record<string, number> = {};
  findings.forEach((f) => {
    findingsBySeverity[f.severity] = (findingsBySeverity[f.severity] || 0) + 1;
  });

  return (
    <div className="metrics-panel">
      <h3>📈 Detailed Metrics</h3>

      <div className="metrics-section">
        <h4>Findings by Severity</h4>
        {Object.keys(findingsBySeverity).length > 0 ? (
          <div className="metrics-badges">
            {Object.entries(findingsBySeverity).map(([severity, count]) => (
              <span
                key={severity}
                className={`badge badge-${severity.toLowerCase()}`}
              >
                {severity}: {count}
              </span>
            ))}
          </div>
        ) : (
          <p className="no-data">No findings</p>
        )}
      </div>

      <div className="metrics-section">
        <h4>Findings by Code</h4>
        {Object.keys(findingsByCode).length > 0 ? (
          <table className="metrics-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Count</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(findingsByCode)
                .sort(([, a], [, b]) => b - a)
                .map(([code, count]) => (
                  <tr key={code}>
                    <td>{code}</td>
                    <td>{count}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        ) : (
          <p className="no-data">No findings</p>
        )}
      </div>

      {approval && (
        <div className="metrics-section">
          <h4>Approval Details</h4>
          <table className="metrics-table">
            <tbody>
              <tr>
                <td>Policy</td>
                <td>{approval.decision_policy}</td>
              </tr>
              <tr>
                <td>Status</td>
                <td className={approval.approved ? "text-ok" : "text-fail"}>
                  {approval.approved ? "✅ Approved" : "❌ Rejected"}
                </td>
              </tr>
              <tr>
                <td>Revised?</td>
                <td>{approval.reflection?.revised ? "🔄 Yes" : "No"}</td>
              </tr>
              {approval.reflection?.revised && (
                <tr>
                  <td>LLM Backend</td>
                  <td>{approval.reflection.llm_backend}</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <div className="metrics-section">
        <h4>Line Items</h4>
        <p className="metrics-stat">
          Total: {result.invoice?.line_items.length ?? 0} items
        </p>
      </div>
    </div>
  );
}
