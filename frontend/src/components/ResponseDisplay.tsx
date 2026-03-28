import { AlertTriangle, FileStack, ShieldAlert, Sparkles } from "lucide-react";
import { RouterResponse } from "../types";
import { SafetyBadge, domainToTone, riskToTone } from "./SafetyBadge";

interface ResponseDisplayProps {
    result: RouterResponse;
}

function routerSummary(result: RouterResponse) {
    const domainLabel = result.classification.domain === "unknown" ? "unclear intent" : result.classification.domain;
    return `${domainLabel} query, ${result.classification.risk_level} risk.`;
}

export function ResponseDisplay({ result }: ResponseDisplayProps) {
    const { classification, safety_flags } = result;

    return (
        <div className="space-y-4">
            <div className="rounded-[2rem] border border-white/10 bg-white/5 p-5 shadow-xl shadow-black/10 backdrop-blur-xl sm:p-6">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                        <h3 className="mt-2 font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua',serif] text-3xl text-stone-50">
                            Routed response
                        </h3>
                    </div>

                    <div className="flex flex-wrap gap-2">
                        <SafetyBadge label={classification.domain} tone={domainToTone(classification.domain)} />
                        <SafetyBadge label={classification.risk_level} tone={riskToTone(classification.risk_level)} />
                        {(safety_flags.self_harm || safety_flags.illegal_request) && (
                            <SafetyBadge label="flagged" tone="danger" />
                        )}
                    </div>
                </div>

                <div className="mt-5 rounded-[1.5rem] border border-white/10 bg-black/20 p-5">
                    <div className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-stone-400">
                        <Sparkles className="h-3.5 w-3.5 text-amber-300" />
                        Routed answer
                    </div>
                    <p className="whitespace-pre-wrap break-words text-sm leading-7 text-stone-100 sm:text-[15px]">
                        {result.response}
                    </p>
                </div>

                <div className="mt-4 grid gap-3 lg:grid-cols-[minmax(0,1.3fr)_minmax(220px,0.7fr)]">
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                        <div className="flex items-start gap-3">
                            <FileStack className="mt-0.5 h-4 w-4 flex-shrink-0 text-cyan-300" />
                            <div>
                                <p className="text-sm font-medium text-stone-100">Routing summary</p>
                                <p className="mt-1 text-xs leading-6 text-stone-400">{routerSummary(result)}</p>
                            </div>
                        </div>
                    </div>

                    {classification.risk_level === "high" && (
                        <div className="rounded-2xl border border-rose-400/25 bg-rose-400/10 p-4">
                            <div className="flex items-start gap-3">
                                <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-rose-200" />
                                <div>
                                    <p className="text-sm font-medium text-rose-50">High-risk detected</p>
                                    <p className="mt-1 text-xs leading-6 text-rose-100/85">
                                        Do not rely only on this app for urgent situations.
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {result.disclaimers.length > 0 && (
                <div className="rounded-[2rem] border border-amber-300/20 bg-amber-300/10 p-5 backdrop-blur-xl">
                    <div className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-amber-100/80">
                        <ShieldAlert className="h-3.5 w-3.5" />
                        Important limits
                    </div>
                    <div className="space-y-3">
                        {result.disclaimers.map((disclaimer, index) => (
                            <p key={`${disclaimer}-${index}`} className="text-sm leading-6 text-amber-50/90">
                                {disclaimer}
                            </p>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
