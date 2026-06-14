const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

const TOKEN_KEY = "careinsight.token";

export const tokenStore = {
  get: (): string | null => localStorage.getItem(TOKEN_KEY),
  set: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

export class ApiError extends Error {
  constructor(public status: number, message: string, public body?: unknown) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = tokenStore.get();
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const resp = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  if (resp.status === 401) {
    tokenStore.clear();
    throw new ApiError(401, "Unauthorized");
  }
  if (!resp.ok) {
    let body: unknown;
    try { body = await resp.json(); } catch { body = await resp.text(); }
    throw new ApiError(resp.status, `Request failed: ${resp.status}`, body);
  }
  if (resp.status === 204) return undefined as unknown as T;
  const contentType = resp.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return resp.json();
  }
  return resp.blob() as unknown as T;
}

export const api = {
  get: <T>(p: string) => request<T>(p),
  post: <T>(p: string, body?: unknown) =>
    request<T>(p, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
};

export interface UserMe {
  id: string;
  email: string;
  full_name: string;
  role: string;
  hospital_id: string;
}

export interface Patient {
  id: string;
  mrn: string;
  first_name: string;
  last_name: string;
  dob: string;
  sex: string;
}

export interface PatientCreate {
  mrn: string;
  first_name: string;
  last_name: string;
  dob: string;
  sex: string;
}

export interface PatientList {
  items: Patient[];
  total: number;
  page: number;
  page_size: number;
}

export interface RiskSummary {
  prediction_id: string;
  probability: number;
  risk_tier: string;
  threshold_used: number;
  model_name: string;
  model_version: string;
  generated_at: string;
}

export interface RiskFactor {
  feature_name: string;
  humanized_label: string;
  shap_value: number;
  rank: number;
}

export interface RiskExplanation {
  prediction_id: string;
  factors: RiskFactor[];
}

export interface Recommendation {
  text: string;
  category: string | null;
  source: string;
}

export interface PopulationPatientRow {
  patient_id: string;
  first_name: string;
  last_name: string;
  mrn: string;
  department: string;
  prediction_id: string;
  probability: number;
  risk_tier: string;
  top_factor: string | null;
}

export interface PopulationResponse {
  patients: PopulationPatientRow[];
  high_count: number;
  medium_count: number;
  low_count: number;
  total: number;
}

export interface FeatureImportanceItem {
  feature_name: string;
  humanized_label: string;
  avg_importance: number;
}

export interface ModelStatsResponse {
  algorithm: string;
  version: string;
  trained_at: string | null;
  cv_auc: number | null;
  test_auc: number | null;
  total_predictions: number;
  tier_distribution: { High: number; Medium: number; Low: number };
  top_features: FeatureImportanceItem[];
}
