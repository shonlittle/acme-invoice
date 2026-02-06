import { useState } from "react";
import "./App.css";
import ControlPanel from "./components/ControlPanel";
import ResultPanel from "./components/ResultPanel";
import type { PipelineResult, Status } from "./types";

export default function App() {
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [status, setStatus] = useState<Status>("idle");

  function handleResult(r: PipelineResult) {
    setResult(r);
    setErrorMsg("");
  }

  function handleError(msg: string) {
    setErrorMsg(msg);
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🧾 Acme Invoice Processor</h1>
      </header>
      <main className="app-main">
        <ControlPanel
          onResult={handleResult}
          onError={handleError}
          onStatusChange={setStatus}
          status={status}
        />
        <ResultPanel result={result} errorMsg={errorMsg} />
      </main>
    </div>
  );
}
