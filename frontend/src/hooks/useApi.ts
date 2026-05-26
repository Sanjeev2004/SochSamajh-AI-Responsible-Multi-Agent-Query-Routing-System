import axios from "axios";
import type { FeedbackSummary, HealthResponse, RouterResponse } from "../types";

export const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
});

export async function getHealth() {
    try {
        const response = await api.get("/api/health");
        return response.data as HealthResponse;
    } catch {
        return { status: "error" };
    }
}

export async function routeQuery(query: string, userContext?: string): Promise<RouterResponse> {
    const response = await api.post("/api/route", { query, user_context: userContext });
    return response.data as RouterResponse;
}

export async function uploadDocument(file: File): Promise<string> {
    const formData = new FormData();
    formData.append("file", file);
    const response = await api.post("/api/upload", formData);
    return response.data.text;
}

export async function sendFeedback(requestId: string, query: string, response: string, rating: "up" | "down") {
    await api.post("/api/feedback", {
        request_id: requestId,
        query,
        response,
        rating,
    });
}

export async function getFeedbackSummary(): Promise<FeedbackSummary> {
    const response = await api.get("/api/feedback/summary");
    return response.data as FeedbackSummary;
}

// ── Streaming ──────────────────────────────────────────────────────────────────

export interface StreamCallbacks {
    onMetadata: (data: any) => void;
    onToken: (text: string) => void;
    onDone: (data: { request_id: string; full_text: string; sources: any[] }) => void;
    onError: (message: string) => void;
}

/**
 * Connects to /api/route/stream and fires callbacks for each SSE event.
 * Returns an AbortController so the caller can cancel mid-stream.
 */
export function routeQueryStream(
    query: string,
    userContext: string | null,
    callbacks: StreamCallbacks
): AbortController {
    const controller = new AbortController();

    (async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/route/stream`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query, user_context: userContext }),
                signal: controller.signal,
            });

            if (!response.ok || !response.body) {
                const errorText = await response.text().catch(() => "Unknown error");
                callbacks.onError(`Server error ${response.status}: ${errorText}`);
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                // SSE events are separated by double newlines
                const parts = buffer.split("\n\n");
                buffer = parts.pop() ?? "";

                for (const part of parts) {
                    const line = part.startsWith("data: ") ? part.slice(6) : part;
                    if (!line.trim()) continue;
                    try {
                        const event = JSON.parse(line);
                        if (event.type === "metadata") callbacks.onMetadata(event);
                        else if (event.type === "token") callbacks.onToken(event.text);
                        else if (event.type === "done") callbacks.onDone(event);
                        else if (event.type === "error") callbacks.onError(event.message);
                    } catch {
                        // malformed JSON chunk — ignore
                    }
                }
            }
        } catch (err: any) {
            if (err.name !== "AbortError") {
                callbacks.onError(err.message ?? "Stream connection failed.");
            }
        }
    })();

    return controller;
}
