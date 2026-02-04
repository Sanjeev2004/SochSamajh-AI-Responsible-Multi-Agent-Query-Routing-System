import { AlertTriangle } from "lucide-react";
import { RouterResponse } from "../types";
import { SafetyBadge, domainToTone, riskToTone } from "./SafetyBadge";

interface ResponseDisplayProps {
    result: RouterResponse;
}

export function ResponseDisplay({ result }: ResponseDisplayProps) {
    const { classification, safety_flags } = result;

    return (
        <div className="space-y-4">
            {/* Badges */}
            <div className="flex flex-wrap gap-2">
                <SafetyBadge label={classification.domain} tone={domainToTone(classification.domain)} />
                <SafetyBadge label={classification.risk_level} tone={riskToTone(classification.risk_level)} />
                {(safety_flags.self_harm || safety_flags.illegal_request) && (
                    <SafetyBadge label="Flagged" tone="danger" />
                )}
            </div>

            {/* Response */}
            <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
                <p className="text-sm leading-relaxed text-slate-100">{result.response}</p>
            </div>

            {/* Disclaimers */}
            {result.disclaimers.length > 0 && (
                <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3">
                    <p className="text-xs text-amber-100 leading-relaxed">{result.disclaimers[0]}</p>
                </div>
            )}

            {/* High Risk Warning */}
            {classification.risk_level === "high" && (
                <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 flex gap-2">
                    <AlertTriangle className="h-4 w-4 text-rose-400 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-rose-100">
                        High-risk query detected. Contact emergency services if needed.
                    </p>
                </div>
            )}
        </div>
    );
}
