export type Domain = "medical" | "legal" | "general" | "unknown";
export type RiskLevel = "low" | "medium" | "high";

export interface ClassificationOutput {
    domain: Domain;
    risk_level: RiskLevel;
    needs_disclaimer: boolean;
    self_harm: boolean;
    illegal_request: boolean;
    reasoning: string;
    confidence: number;
    triggered_terms: string[];
    alternative_domains: Record<string, number>;
    explanation: string;
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
    sources: SourceCitation[];
    pipeline_trace: string[];
}

export interface SourceCitation {
    title: string;
    source: string;
    domain?: Domain | null;
    snippet: string;
    score?: number | null;
}

export interface HistoryItem {
    id: string;
    query: string;
    result: RouterResponse;
    timestamp: string;
}

export interface FeedbackSummary {
    total: number;
    by_rating: Array<{ rating: "up" | "down"; count: number }>;
    negative_feedback_queue: Array<{
        timestamp: string;
        request_id: string;
        query_text: string;
        response_text: string;
        rating: "up" | "down";
    }>;
}
