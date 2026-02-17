import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000
});

export interface RouterResponse {
    response: string;
    classification: {
        domain: string;
        risk_level: string;
        illegal_request: boolean;
        self_harm: boolean;
        needs_disclaimer: boolean;
        reasoning: string;
    };
    disclaimers: string[];
    safety_flags: {
        high_risk: boolean;
        illegal_request: boolean;
        self_harm: boolean;
    };
    request_id: string;
}

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
