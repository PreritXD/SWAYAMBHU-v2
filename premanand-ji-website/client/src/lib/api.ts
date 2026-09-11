/**
 * SWAYAMBHU v2 API Client for Premanand Ji Website
 * Connects the frontend to the FastAPI RAG backend for spiritual Q&A,
 * citations with exact YouTube timestamps, and continuous feedback.
 */

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface CrossChannelAlias {
  channel: string;
  video_id: string;
  video_title?: string;
  timestamp_sec: number;
  timestamp_formatted: string;
}

export interface Citation {
  video_id: string;
  title: string;
  channel: string;
  start_sec: number;
  end_sec: number;
  timestamp_start: string;
  timestamp_end: string;
  url: string;
  relevance_score: number;
  excerpt: string;
  cross_channel_aliases?: CrossChannelAlias[];
}

export interface ChatDisclaimer {
  text: string;
  is_official_channel: boolean;
}

export interface ChatRequest {
  message: string;
  query?: string;
  history?: ChatMessage[];
  session_id?: string;
  channel_filter?: string | null;
  use_council?: boolean;
}

export interface ChatResponse {
  answer: string;
  is_grounded: boolean;
  refusal_reason?: string | null;
  citations: Citation[];
  disclaimer: ChatDisclaimer;
  normalized_query?: string | null;
  rewritten_query?: string | null;
  latency_ms: number;
  model_used: string;
  llm_provider?: string | null;
  use_council: boolean;
  council_deliberation?: Record<string, unknown> | null;
  case_category?: string | null;
}

export interface FeedbackRequest {
  query: string;
  answer: string;
  flagged: boolean;
  note?: string;
}

export interface FeedbackResponse {
  status: string;
  feedback_id: string;
  message: string;
}

export interface HealthResponse {
  status: string;
  app_env: string;
  vector_store: string;
  llm_provider: string;
  timestamp: string;
}

// Configurable API base; defaults to relative URL which is proxied by Vite dev server
const PRIMARY_API_BASE = import.meta.env.VITE_BACKEND_URL || "";
const FALLBACK_API_BASE = "http://127.0.0.1:8000";

async function fetchWithFallback(endpoint: string, options: RequestInit): Promise<Response> {
  // First attempt via primary base (relative / proxy)
  try {
    const res = await fetch(`${PRIMARY_API_BASE}${endpoint}`, options);
    // If it's a 404 or 502/503 and we didn't specify a custom base, try direct localhost:8000 fallback
    if (!res.ok && res.status >= 502 && !PRIMARY_API_BASE) {
      return await fetch(`${FALLBACK_API_BASE}${endpoint}`, options);
    }
    return res;
  } catch (error) {
    if (!PRIMARY_API_BASE) {
      // Network failure on relative path (e.g., if proxy not running), try direct backend port
      return await fetch(`${FALLBACK_API_BASE}${endpoint}`, options);
    }
    throw error;
  }
}

/**
 * Send a question to the spiritual RAG engine
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetchWithFallback("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    let errorDetail = "सत्संग शोध में त्रुटि आई। कृपया पुनः प्रयास करें।";
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = errorJson.detail;
      }
    } catch {
      errorDetail = `सर्वर त्रुटि (${response.status}): सेवा अस्थायी रूप से अनुपलब्ध है।`;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Submit user rating or flag an inaccurate answer
 */
export async function sendFeedback(feedback: FeedbackRequest): Promise<FeedbackResponse> {
  const response = await fetchWithFallback("/api/feedback", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(feedback),
  });

  if (!response.ok) {
    throw new Error("प्रतिक्रिया दर्ज नहीं की जा सकी।");
  }

  return response.json();
}

/**
 * Check backend service health & active model provider
 */
export async function checkBackendHealth(): Promise<HealthResponse> {
  const response = await fetchWithFallback("/api/health", {
    method: "GET",
  });

  if (!response.ok) {
    throw new Error("Backend service is offline");
  }

  return response.json();
}
