import type { BatchResult } from "../types";

interface Props {
  batchResult: BatchResult;
  onClose: () => void;
}

export default function BatchMetrics({ batchResult, onClose }: Props) {
  const { summary } = batchResult;

  return (
    <div className="batch-metrics">
      <div className="batch-header">
        <h2>📊 Batch Processing Results</h2>
        <button className="close-btn" onClick={onClose}>
          ✕
        </button>
      </div>

      <div className="batch-summary-cards">
        <div className="batch-card">
          <div className="batch-card-label">Unique Invoices</div>
          <div className="batch-card-value">{summary.total}</div>
        </div>

        <div className="batch-card">
          <div className="batch-card-label">Files Processed</div>
          <div className="batch-card-value">{summary.files_processed}</div>
        </div>

        <div className="batch-card">
          <div className="batch-card-label">Duplicates</div>
          <div className="batch-card-value">{summary.duplicates_found}</div>
        </div>

        <div className="batch-card">
          <div className="batch-card-label">Approved</div>
          <div className="batch-card-value text-ok">{summary.approved}</div>
        </div>

        <div className="batch-card">
          <div className="batch-card-label">Rejected</div>
          <div className="batch-card-value text-fail">{summary.rejected}</div>
        </div>

        <div className="batch-card">
          <div className="batch-card-label">Revised</div>
          <div className="batch-card-value">{summary.revised}</div>
        </div>

        <div className="batch-card">
          <div className="batch-card-label">Approval Rate</div>
          <div className="batch-card-value">{summary.approval_rate}%</div>
        </div>

        <div className="batch-card">
          <div className="batch-card-label">Revision Rate</div>
          <div className="batch-card-value">{summary.revision_rate}%</div>
        </div>
      </div>

      <div className="batch-section">
        <h3>Findings by Severity</h3>
        <div className="metrics-badges">
          {Object.entries(summary.findings_by_severity).map(
            ([severity, count]) =>
              count > 0 && (
                <span
                  key={severity}
                  className={`badge badge-${severity.toLowerCase()}`}
                >
                  {severity}: {count}
                </span>
              ),
          )}
        </div>
      </div>

      <div className="batch-section">
        <h3>Findings by Code</h3>
        {Object.keys(summary.findings_by_code).length > 0 ? (
          <table className="metrics-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Count</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(summary.findings_by_code)
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
          <p className="no-data">No findings across all invoices</p>
        )}
      </div>

      {batchResult.duplicate_groups.length > 0 && (
        <div className="batch-section">
          <h3>🔄 Duplicate Invoices Detected</h3>
          <table className="metrics-table">
            <thead>
              <tr>
                <th>Invoice Number</th>
                <th>Files Found</th>
                <th>Kept</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {batchResult.duplicate_groups.map((dup) => (
                <tr key={dup.invoice_number}>
                  <td>{dup.invoice_number}</td>
                  <td>
                    {dup.files.map((file, idx) => (
                      <div key={idx}>
                        {file === dup.kept ? (
                          <span className="text-ok">✓ {file}</span>
                        ) : (
                          <span className="text-neutral">{file}</span>
                        )}
                      </div>
                    ))}
                  </td>
                  <td>{dup.kept}</td>
                  <td className="text-neutral">{dup.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="batch-section">
        <h3>Individual Results ({batchResult.results.length})</h3>
        <p className="batch-note">
          Select a sample invoice above to view individual result details.
        </p>
      </div>
    </div>
  );
}
