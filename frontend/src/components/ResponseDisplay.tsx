import { AlertTriangle, Sparkles } from "lucide-react";
import { RouterResponse } from "../types";
import { SafetyBadge, domainToTone, riskToTone } from "./SafetyBadge";

interface ResponseDisplayProps {
    result: RouterResponse;
}

export function ResponseDisplay({ result }: ResponseDisplayProps) {
    const { classification, safety_flags } = result;

    return (
        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-400">
            <div className="flex flex-wrap gap-2">
                <SafetyBadge label={classification.domain} tone={domainToTone(classification.domain)} />
                <SafetyBadge label={classification.risk_level} tone={riskToTone(classification.risk_level)} />
                {(safety_flags.self_harm || safety_flags.illegal_request) && (
                    <SafetyBadge label="Flagged" tone="danger" />
                )}
            </div>

            <div className="relative rounded-xl overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/20 via-slate-700/20 to-violet-500/20 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <div className="relative rounded-xl bg-gradient-to-br from-slate-900/80 to-slate-800/50 backdrop-blur border border-slate-700/50 p-5 hover:border-indigo-500/30 transition-all duration-300">
                    <div className="flex items-start gap-3">
                        <Sparkles className="h-4 w-4 text-indigo-400 flex-shrink-0 mt-0.5 opacity-60" />
                        <p className="text-sm leading-relaxed text-slate-100 whitespace-pre-wrap break-words">
                            {result.response}
                        </p>
                    </div>
                </div>
            </div>

            {result.disclaimers.length > 0 && (
                <div className="rounded-xl border border-amber-500/30 bg-gradient-to-r from-amber-500/10 to-orange-500/5 backdrop-blur p-4 animate-in fade-in duration-500">
                    {result.disclaimers.map((disclaimer, index) => (
                        <p key={`${disclaimer}-${index}`} className="text-xs text-amber-100 leading-relaxed">
                            {disclaimer}
                        </p>
                    ))}
                </div>
            )}

            {classification.risk_level === "high" && (
                <div className="rounded-xl border border-rose-500/50 bg-gradient-to-r from-rose-500/20 to-red-500/10 backdrop-blur p-4 flex gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
                    <AlertTriangle className="h-5 w-5 text-rose-300 flex-shrink-0 mt-0.5 animate-pulse" />
                    <p className="text-xs text-rose-100 font-medium">
                        High-risk query detected. Contact emergency services if needed.
                    </p>
                </div>
            )}
        </div>
    );
}
