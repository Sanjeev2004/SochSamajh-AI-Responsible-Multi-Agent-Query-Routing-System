import axios from "axios";
import { RouterResponse } from "../types";

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
    timeout: 30000
});

export async function getHealth() {
    const response = await api.get("/api/health");
    return response.data as { status: string; model: string; langsmith_project?: string };
}

export async function routeQuery(query: string): Promise<RouterResponse> {
    const response = await api.post("/api/route", { query });
    return response.data as RouterResponse;
}
