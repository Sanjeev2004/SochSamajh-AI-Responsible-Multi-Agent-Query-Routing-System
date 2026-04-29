import axios from "axios";
import type { FeedbackSummary, RouterResponse } from "../types";

export const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000
});

export async function getHealth() {
    try {
        const response = await api.get("/api/health");
        return response.data as { status: string; model: string; langsmith_project?: string };
    } catch {
        return { status: "error", model: "unknown" };
    }
}

export async function routeQuery(query: string): Promise<RouterResponse> {
    const response = await api.post("/api/route", { query });
    return response.data as RouterResponse;
}

export async function sendFeedback(requestId: string, query: string, response: string, rating: "up" | "down") {
    await api.post("/api/feedback", {
        request_id: requestId,
        query,
        response,
        rating
    });
}

export async function getFeedbackSummary(): Promise<FeedbackSummary> {
    const response = await api.get("/api/feedback/summary");
    return response.data as FeedbackSummary;
}
