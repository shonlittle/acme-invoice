import { useState } from "react";
import type { PipelineResult } from "../types";

interface Props {
  result: PipelineResult;
}

export default function RawJsonView({ result }: Props) {
  const [open, setOpen] = useState(false);

  return (
    <div className="raw-json">
      <button className="toggle-btn" onClick={() => setOpen(!open)}>
        {open ? "▼" : "▶"} Raw JSON
      </button>
      {open && (
        <pre className="json-pre">{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
}
