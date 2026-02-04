import { AlertTriangle, ClipboardCheck } from "lucide-react";
import { RouterResponse } from "../types";
import { SafetyBadge, domainToTone, riskToTone } from "./SafetyBadge";

interface ResponseDisplayProps {
    result: RouterResponse;
}

export function ResponseDisplay({ result }: ResponseDisplayProps) {
    const { classification, safety_flags } = result;

    return (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
            <div className="flex flex-wrap gap-2">
                <SafetyBadge label={`Domain: ${classification.domain}`} tone={domainToTone(classification.domain)} />
                <SafetyBadge label={`Risk: ${classification.risk_level}`} tone={riskToTone(classification.risk_level)} />
                {safety_flags.self_harm && <SafetyBadge label="Self-harm flag" tone="danger" />}
                {safety_flags.illegal_request && <SafetyBadge label="Illegal request flag" tone="danger" />}
            </div>

            <div className="mt-4 space-y-4">
                <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-4 text-sm text-slate-100">
                    {result.response}
                </div>

                {result.disclaimers.length > 0 && (
                    <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-100">
                        <div className="flex items-center gap-2 font-semibold">
                            <ClipboardCheck className="h-4 w-4" />
                            Disclaimers & Safety Notes
                        </div>
                        <ul className="mt-2 list-disc space-y-1 pl-5">
                            {result.disclaimers.map((note, index) => (
                                <li key={`${note}-${index}`}>{note}</li>
                            ))}
                        </ul>
                    </div>
                )}

                {classification.risk_level === "high" && (
                    <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-4 text-sm text-rose-100">
                        <div className="flex items-center gap-2 font-semibold">
                            <AlertTriangle className="h-4 w-4" />
                            High-risk query detected
                        </div>
                        <p className="mt-2 text-sm">
                            If this relates to personal safety, please contact local emergency services or trusted support.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
