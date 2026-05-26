import { AlertTriangle, FileSearch, FileStack, GitBranch, ShieldAlert, Sparkles, Paperclip } from "lucide-react";
import { RouterResponse } from "../types";
import { SafetyBadge, domainToTone, riskToTone } from "./SafetyBadge";

interface ResponseDisplayProps {
    result: RouterResponse;
    query?: string;
    attachedFile?: string;
    /** Live token stream — null when streaming is complete */
    streamingText?: string | null;
}

function routerSummary(result: RouterResponse) {
    const domainLabel = result.classification.domain === "unknown" ? "unclear intent" : result.classification.domain;
    return `${domainLabel} query, ${result.classification.risk_level} risk.`;
}

    export function ResponseDisplay({ result, query, attachedFile, streamingText }: ResponseDisplayProps) {
    const { classification, safety_flags } = result;
    const confidencePercent = Math.round((classification.confidence ?? 0) * 100);
    const trace = result.pipeline_trace ?? [];
    const sources = result.sources ?? [];
    const triggeredTerms = classification.triggered_terms ?? [];

    return (
        <div className="space-y-4">
            <div className="rounded-2xl border border-border bg-surface p-5 sm:p-6 shadow-sm">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                        <h3 className="mt-2 font-display text-2xl font-semibold tracking-tight text-stone-100">
                            Routed response
                        </h3>
                        {query && (
                            <p className="mt-2 text-sm text-stone-400">
                                <span className="font-medium text-stone-500">Query:</span> {query}
                            </p>
                        )}
                        {attachedFile && (
                            <p className="mt-1 flex items-center gap-1.5 text-sm text-stone-400">
                                <Paperclip className="h-3.5 w-3.5" />
                                <span className="font-medium text-stone-500">Document:</span> {attachedFile}
                            </p>
                        )}
                    </div>

                    <div className="flex flex-wrap gap-2">
                        <SafetyBadge label={classification.domain} tone={domainToTone(classification.domain)} />
                        <SafetyBadge label={classification.risk_level} tone={riskToTone(classification.risk_level)} />
                        <SafetyBadge label={`${confidencePercent}% confidence`} tone={confidencePercent >= 75 ? "success" : "warning"} />
                        {(safety_flags.self_harm || safety_flags.illegal_request) && (
                            <SafetyBadge label="flagged" tone="danger" />
                        )}
                    </div>
                </div>

                <div className="mt-6 rounded-xl bg-deep p-5 border border-border">
                    <div className="mb-3 flex items-center gap-2 text-[10px] font-medium uppercase tracking-widest text-stone-500">
                        <Sparkles className="h-3.5 w-3.5" />
                        Routed answer
                        {streamingText !== null && streamingText !== undefined && (
                            <span className="ml-2 inline-flex items-center gap-1 rounded bg-surface-hover px-2 py-0.5 text-[10px] text-stone-300">
                                Generating...
                            </span>
                        )}
                    </div>
                    <p className="whitespace-pre-wrap break-words text-[15px] leading-relaxed text-stone-200">
                        {streamingText !== null && streamingText !== undefined
                            ? streamingText || (
                                <span className="inline-flex items-center gap-1.5 text-stone-600">
                                    Generating response...
                                </span>
                              )
                            : result.response}
                        {streamingText !== null && streamingText !== undefined && streamingText.length > 0 && (
                            <span className="ml-1 inline-block h-4 w-1 animate-pulse bg-stone-400" />
                        )}
                    </p>
                </div>

                <div className="mt-4 grid gap-3 lg:grid-cols-[minmax(0,1.3fr)_minmax(220px,0.7fr)]">
                    <div className="rounded-xl border border-border bg-deep p-4">
                        <div className="flex items-start gap-3">
                            <FileStack className="mt-0.5 h-4 w-4 flex-shrink-0 text-stone-400" />
                            <div>
                                <p className="text-sm font-medium text-stone-200">Routing summary</p>
                                <p className="mt-1 text-xs leading-5 text-stone-400">{routerSummary(result)}</p>
                                <p className="mt-2 text-xs leading-5 text-stone-500">
                                    {classification.explanation || classification.reasoning}
                                </p>
                            </div>
                        </div>
                    </div>

                    {classification.risk_level === "high" && (
                        <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4">
                            <div className="flex items-start gap-3">
                                <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-rose-400" />
                                <div>
                                    <p className="text-sm font-medium text-rose-200">High-risk detected</p>
                                    <p className="mt-1 text-xs leading-5 text-rose-300/80">
                                        Do not rely only on this app for urgent situations.
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <div className="mt-4 grid gap-3 lg:grid-cols-3">
                    <div className="rounded-xl border border-border bg-deep p-4">
                        <div className="mb-3 flex items-center gap-2 text-[10px] font-medium uppercase tracking-widest text-stone-500">
                            <GitBranch className="h-3.5 w-3.5" />
                            Trace
                        </div>
                        <p className="break-words text-xs leading-5 text-stone-400">
                            {trace.length > 0 ? trace.join(" -> ") : "Trace unavailable"}
                        </p>
                    </div>

                    <div className="rounded-xl border border-border bg-deep p-4">
                        <div className="mb-3 flex items-center gap-2 text-[10px] font-medium uppercase tracking-widest text-stone-500">
                            <FileSearch className="h-3.5 w-3.5" />
                            Evidence
                        </div>
                        {triggeredTerms.length > 0 ? (
                            <div className="flex flex-wrap gap-2">
                                {triggeredTerms.slice(0, 6).map((term) => (
                                    <span key={term} className="rounded-md border border-border bg-surface px-2 py-1 text-[11px] text-stone-300">
                                        {term}
                                    </span>
                                ))}
                            </div>
                        ) : (
                            <p className="text-xs leading-5 text-stone-500">No specific trigger terms matched.</p>
                        )}
                    </div>

                    <div className="rounded-xl border border-border bg-deep p-4">
                        <div className="mb-3 flex items-center gap-2 text-[10px] font-medium uppercase tracking-widest text-stone-500">
                            <Sparkles className="h-3.5 w-3.5" />
                            Scores
                        </div>
                        <div className="space-y-2">
                            {Object.entries(classification.alternative_domains ?? {}).map(([domain, score]) => (
                                <div key={domain} className="flex items-center justify-between gap-3 text-xs text-stone-400">
                                    <span className="capitalize">{domain}</span>
                                    <span>{Math.round(Number(score) * 100)}%</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {sources.length > 0 && (
                <div className="rounded-2xl border border-border bg-surface p-5 shadow-sm">
                    <div className="mb-4 flex items-center gap-2 text-[10px] font-medium uppercase tracking-widest text-stone-500">
                        <FileSearch className="h-3.5 w-3.5" />
                        Retrieved sources
                    </div>
                    <div className="grid gap-3 md:grid-cols-2">
                        {sources.map((source, index) => (
                            <div key={`${source.source}-${index}`} className="rounded-xl border border-border bg-deep p-4">
                                <p className="text-sm font-medium text-stone-200">{source.title}</p>
                                <p className="mt-1 text-xs text-stone-500">{source.source}</p>
                                <p className="mt-2 line-clamp-4 text-xs leading-5 text-stone-400">{source.snippet}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {result.disclaimers.length > 0 && (
                <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-5 shadow-sm">
                    <div className="mb-4 flex items-center gap-2 text-[10px] font-medium uppercase tracking-widest text-amber-500/80">
                        <ShieldAlert className="h-3.5 w-3.5" />
                        Important limits
                    </div>
                    <div className="space-y-3">
                        {result.disclaimers.map((disclaimer, index) => (
                            <p key={`${disclaimer}-${index}`} className="text-sm leading-6 text-amber-200/90">
                                {disclaimer}
                            </p>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
