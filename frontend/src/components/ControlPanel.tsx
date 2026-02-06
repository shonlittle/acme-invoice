import { useEffect, useState } from "react";
import { fetchSamples, processSample, processUpload, runAll } from "../api";
import type { BatchResult, PipelineResult, SampleFile, Status } from "../types";

interface Props {
  onResult: (result: PipelineResult) => void;
  onBatchResult: (result: BatchResult) => void;
  onError: (msg: string) => void;
  onStatusChange: (status: Status) => void;
  status: Status;
}

export default function ControlPanel({
  onResult,
  onBatchResult,
  onError,
  onStatusChange,
  status,
}: Props) {
  const [samples, setSamples] = useState<SampleFile[]>([]);
  const [selectedSample, setSelectedSample] = useState("");
  const [file, setFile] = useState<File | null>(null);

  useEffect(() => {
    fetchSamples()
      .then((data) => setSamples(data.samples))
      .catch(() => {
        /* samples will be empty */
      });
  }, []);

  const isLoading = status === "loading";

  async function handleRun() {
    onStatusChange("loading");
    try {
      let result: PipelineResult;
      if (file) {
        result = await processUpload(file);
      } else if (selectedSample) {
        result = await processSample(selectedSample);
      } else {
        onError("Please upload a file or select a sample invoice.");
        onStatusChange("error");
        return;
      }
      onResult(result);
      onStatusChange("success");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      onError(msg);
      onStatusChange("error");
    }
  }

  async function handleRunAll() {
    onStatusChange("loading");
    try {
      const result = await runAll();
      onBatchResult(result);
      onStatusChange("success");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      onError(msg);
      onStatusChange("error");
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    if (f) setSelectedSample("");
  }

  function handleSampleChange(e: React.ChangeEvent<HTMLSelectElement>) {
    setSelectedSample(e.target.value);
    if (e.target.value) setFile(null);
  }

  return (
    <div className="control-panel">
      <h2>📄 Input</h2>

      <label className="field-label">Upload Invoice</label>
      <input
        type="file"
        accept=".pdf,.txt,.csv,.json,.xml"
        onChange={handleFileChange}
        disabled={isLoading}
      />

      <div className="divider">— OR —</div>

      <label className="field-label">Select Sample</label>
      <select
        value={selectedSample}
        onChange={handleSampleChange}
        disabled={isLoading}
      >
        <option value="">Choose a sample…</option>
        {samples.map((s) => (
          <option key={s.filename} value={s.filename}>
            {s.filename}
          </option>
        ))}
      </select>

      <button
        className="run-btn"
        onClick={handleRun}
        disabled={isLoading || (!file && !selectedSample)}
      >
        {isLoading ? "⏳ Processing…" : "▶ Run Pipeline"}
      </button>

      <button
        className="run-btn run-all-btn"
        onClick={handleRunAll}
        disabled={isLoading}
      >
        {isLoading ? "⏳ Processing…" : "▶ Run All Samples"}
      </button>

      <div className={`status status-${status}`}>
        {status === "idle" && "Ready"}
        {status === "loading" && "Processing invoice…"}
        {status === "success" && "✅ Complete"}
        {status === "error" && "❌ Error"}
      </div>
    </div>
  );
}
