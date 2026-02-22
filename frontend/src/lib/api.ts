import type { ChatMessage, ChatResponse, SearchParams, SearchResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function searchProviders(
  params: SearchParams
): Promise<SearchResponse> {
  const url = new URL(`${API_URL}/api/search`);
  url.searchParams.set("q", params.q);
  url.searchParams.set("lat", String(params.lat));
  url.searchParams.set("lng", String(params.lng));
  url.searchParams.set("radius_meters", String(params.radius_meters));

  const res = await fetch(url.toString());
  if (!res.ok) {
    throw new Error(`Search failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function sendChatMessage(
  messages: ChatMessage[]
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });
  if (!res.ok) {
    throw new Error(`Chat failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function checkReplies(): Promise<{ replies_processed: number }> {
  const res = await fetch(`${API_URL}/api/inquiries/check-replies`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error(`Check replies failed: ${res.status}`);
  }
  return res.json();
}

export async function sendInquiry(
  providerId: string,
  serviceType: string
): Promise<{ status: string }> {
  const res = await fetch(`${API_URL}/api/inquiries`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      provider_id: providerId,
      service_type: serviceType,
    }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Inquiry failed: ${res.status}`);
  }
  return res.json();
}
