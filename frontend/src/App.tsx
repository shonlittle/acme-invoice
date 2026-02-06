import { useState } from "react";
import "./App.css";
import BatchMetrics from "./components/BatchMetrics";
import ControlPanel from "./components/ControlPanel";
import ResultPanel from "./components/ResultPanel";
import type { BatchResult, PipelineResult, Status } from "./types";

export default function App() {
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [batchResult, setBatchResult] = useState<BatchResult | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [status, setStatus] = useState<Status>("idle");

  function handleResult(r: PipelineResult) {
    setResult(r);
    setBatchResult(null);
    setErrorMsg("");
  }

  function handleBatchResult(r: BatchResult) {
    setBatchResult(r);
    setResult(null);
    setErrorMsg("");
  }

  function handleError(msg: string) {
    setErrorMsg(msg);
  }

  function handleCloseBatch() {
    setBatchResult(null);
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🧾 Acme Invoice Processor</h1>
      </header>
      <main className="app-main">
        <ControlPanel
          onResult={handleResult}
          onBatchResult={handleBatchResult}
          onError={handleError}
          onStatusChange={setStatus}
          status={status}
        />
        {batchResult ? (
          <BatchMetrics batchResult={batchResult} onClose={handleCloseBatch} />
        ) : (
          <ResultPanel result={result} errorMsg={errorMsg} />
        )}
      </main>
    </div>
  );
}
