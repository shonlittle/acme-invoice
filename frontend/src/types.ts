/** TypeScript types matching the backend PipelineResult JSON shape. */

export interface LineItem {
  item: string;
  quantity: number;
  unit_price: number | null;
  amount: number | null;
}

export interface Invoice {
  vendor: string;
  amount: number;
  line_items: LineItem[];
  due_date: string | null;
  invoice_number: string | null;
  vendor_address: string | null;
  subtotal: number | null;
  tax_rate: number | null;
  tax_amount: number | null;
  currency: string;
  payment_terms: string | null;
  revision: string | null;
}

export interface ValidationFinding {
  code: string;
  severity: string;
  message: string;
  item_name: string | null;
  requested_qty: number | null;
  available_qty: number | null;
}

export interface InitialDecision {
  approved: boolean;
  reasons: string[];
  timestamp: string;
}

export interface ReflectionResult {
  critique_notes: string;
  revised: boolean;
  llm_backend: string;
  revised_reasons: string[] | null;
}

export interface ApprovalDecision {
  approved: boolean;
  decision_policy: string;
  reasons: string[];
  severity_summary: Record<string, number>;
  initial_decision: InitialDecision;
  reflection: ReflectionResult | null;
  final_decision_timestamp: string;
}

export interface PaymentResult {
  status: string;
  vendor: string;
  amount: number;
  payment_reference_id: string;
  timestamp: string;
  reason: string | null;
}

export interface PipelineResult {
  invoice_path: string;
  invoice: Invoice | null;
  validation_findings: ValidationFinding[];
  approval_decision: ApprovalDecision | null;
  payment_result: PaymentResult | null;
  errors: string[];
}

export interface SampleFile {
  filename: string;
  path: string;
}

export interface SamplesResponse {
  samples: SampleFile[];
}

export type Status = "idle" | "loading" | "success" | "error";

export interface BatchSummary {
  total: number;
  files_processed: number;
  duplicates_found: number;
  approved: number;
  rejected: number;
  revised: number;
  approval_rate: number;
  revision_rate: number;
  findings_by_severity: Record<string, number>;
  findings_by_code: Record<string, number>;
}

export interface DuplicateGroup {
  invoice_number: string;
  files: string[];
  kept: string;
  reason: string;
}

export interface BatchResult {
  results: PipelineResult[];
  summary: BatchSummary;
  duplicate_groups: DuplicateGroup[];
}
