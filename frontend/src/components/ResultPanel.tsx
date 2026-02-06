import type { PipelineResult } from "../types";
import MetricsPanel from "./MetricsPanel";
import RawJsonView from "./RawJsonView";
import SummaryCards from "./SummaryCards";

interface Props {
  result: PipelineResult | null;
  errorMsg: string;
}

export default function ResultPanel({ result, errorMsg }: Props) {
  if (errorMsg) {
    return (
      <div className="result-panel">
        <h2>📊 Results</h2>
        <div className="error-box">{errorMsg}</div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="result-panel">
        <h2>📊 Results</h2>
        <p className="placeholder">
          Select an invoice and click Run to see results.
        </p>
      </div>
    );
  }

  return (
    <div className="result-panel">
      <h2>📊 Results — {result.invoice?.invoice_number ?? "Unknown"}</h2>
      <SummaryCards result={result} />
      <MetricsPanel result={result} />
      <RawJsonView result={result} />
    </div>
  );
}
