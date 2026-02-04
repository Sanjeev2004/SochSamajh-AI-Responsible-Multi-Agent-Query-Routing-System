export type Domain = "medical" | "legal" | "general" | "unknown";
export type RiskLevel = "low" | "medium" | "high";

export interface ClassificationOutput {
    domain: Domain;
    risk_level: RiskLevel;
    needs_disclaimer: boolean;
    self_harm: boolean;
    illegal_request: boolean;
    reasoning: string;
}

export interface SafetyFlags {
    self_harm: boolean;
    illegal_request: boolean;
    high_risk: boolean;
}

export interface RouterResponse {
    response: string;
    classification: ClassificationOutput;
    disclaimers: string[];
    safety_flags: SafetyFlags;
    request_id: string;
}

export interface HistoryItem {
    id: string;
    query: string;
    result: RouterResponse;
    timestamp: string;
}
