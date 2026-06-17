// Browser uses same-origin /api (proxied by Next.js → FastAPI).
// Server-side calls can hit the backend directly.
const API_BASE =
  typeof window !== "undefined"
    ? ""
    : process.env.API_BACKEND_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type Domain = {
  id: string;
  label: string;
  category: string;
  description: string;
  compliance: string[];
  typical_systems: string[];
};

export type RfpSummary = {
  rfp_id: string;
  title: string;
  status: string;
  domain_id?: string;
  domain_label?: string;
  category?: string;
  organization?: string;
  created_at?: string;
  updated_at?: string;
  has_docx?: boolean;
  download_url?: string | null;
};

export type RfpDetail = RfpSummary & {
  content?: string;
  analysis?: string;
  proposal?: string;
  company_name?: string;
};

function formatApiError(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: string }).msg);
        }
        return JSON.stringify(item);
      })
      .join("; ");
  }
  return fallback;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  const isLongRunning =
    path.includes("/generate") ||
    path.includes("/analyze") ||
    (path.includes("/chat") && init?.method === "POST");
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
      signal: isLongRunning ? AbortSignal.timeout(300_000) : init?.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "TimeoutError") {
      throw new Error("Request timed out. Bedrock may still be processing — please wait and retry.");
    }
    throw new Error(
      "Cannot reach the API server. Open a terminal and run: ./start-api.sh"
    );
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(formatApiError(err.detail, res.statusText || "Request failed"));
  }
  return res.json();
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),
  domains: () => request<Domain[]>("/api/domains"),
  listRfps: () => request<RfpSummary[]>("/api/rfps"),
  getRfp: (id: string) => request<RfpDetail>(`/api/rfps/${id}`),
  generateRfp: (body: {
    title: string;
    domain_id: string;
    organization: string;
    project_summary: string;
    budget_range?: string;
    timeline?: string;
  }) =>
    request<RfpDetail & { content: string }>("/api/rfps/generate", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  analyzeRfp: (id: string) =>
    request<{ analysis: string }>(`/api/rfps/${id}/analyze`, { method: "POST" }),
  proposeRfp: (id: string, body: { company_name: string; company_profile: string }) =>
    request<{ proposal: string }>(`/api/rfps/${id}/propose`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getChat: (id: string) =>
    request<{ role: string; content: string; created_at: string }[]>(
      `/api/rfps/${id}/chat`
    ),
  sendChat: (id: string, message: string) =>
    request<{ reply: string }>(`/api/rfps/${id}/chat`, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),
  downloadUrl: (id: string) => `/api/rfps/${id}/download`,
};
