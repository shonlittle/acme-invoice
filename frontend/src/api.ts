/** API client — fetch-based, no external dependencies. */

import type { BatchResult, PipelineResult, SamplesResponse } from "./types";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export async function fetchHealth(): Promise<{ status: string }> {
  const res = await fetch(`${BASE}/api/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function fetchSamples(): Promise<SamplesResponse> {
  const res = await fetch(`${BASE}/api/samples`);
  if (!res.ok) throw new Error(`Failed to fetch samples: ${res.status}`);
  return res.json();
}

export async function processSample(
  sampleName: string,
): Promise<PipelineResult> {
  const res = await fetch(`${BASE}/api/process-sample`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sample_name: sampleName }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function processUpload(file: File): Promise<PipelineResult> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/api/process`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Upload failed: ${res.status}`);
  }
  return res.json();
}

export async function runAll(): Promise<BatchResult> {
  const res = await fetch(`${BASE}/api/run-all`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Run all failed: ${res.status}`);
  }
  return res.json();
}
