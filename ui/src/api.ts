export interface ChatResponse {
  reply: string;
  session_id: string;
  property_name: string;
}

export interface HealthResponse {
  status: string;
  property: string;
  documents_loaded: number;
}

const BASE_URL = "/api/v1";

export async function sendMessage(
  message: string,
  sessionId?: string
): Promise<ChatResponse> {
  const body: Record<string, string> = { message };
  if (sessionId) body.session_id = sessionId;

  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API error ${res.status}: ${detail}`);
  }

  return res.json();
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error("Backend unreachable");
  return res.json();
}
