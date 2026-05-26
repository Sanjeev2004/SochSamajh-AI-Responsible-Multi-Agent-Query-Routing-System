import { useEffect, useMemo, useRef, useState } from "react";
import {
    Activity,
    AlertTriangle,
    CheckCircle,
    MessageSquareWarning,
    ThumbsDown,
    ThumbsUp,
    RotateCcw
} from "lucide-react";
import { getFeedbackSummary, getHealth, routeQueryStream, sendFeedback } from "./hooks/useApi";
import { FeedbackSummary, HealthResponse, HistoryItem, RouterResponse } from "./types";
import { QueryInput } from "./components/QueryInput";
import { ResponseDisplay } from "./components/ResponseDisplay";
import { LoadingState } from "./components/LoadingState";

export default function App() {
    const [health, setHealth] = useState<HealthResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [streamingText, setStreamingText] = useState<string | null>(null);
    const [currentResult, setCurrentResult] = useState<RouterResponse | null>(null);
    const [history, setHistory] = useState<HistoryItem[]>(() => {
        try {
            const saved = localStorage.getItem("sochsamajh_history");
            return saved ? JSON.parse(saved) : [];
        } catch {
            return [];
        }
    });

    useEffect(() => {
        try {
            localStorage.setItem("sochsamajh_history", JSON.stringify(history.slice(0, 20)));
        } catch {
            // Silently fail if quota exceeded
        }
    }, [history]);
    const [feedbackSent, setFeedbackSent] = useState(false);
    const [feedbackSummary, setFeedbackSummary] = useState<FeedbackSummary | null>(null);
    const streamAbortRef = useRef<AbortController | null>(null);

    const currentHistoryItem = useMemo(() => {
        if (!currentResult) return null;
        return history.find((item) => item.id === currentResult.request_id) ?? null;
    }, [currentResult, history]);

    useEffect(() => {
        let mounted = true;
        const fetchHealth = () =>
            getHealth()
                .then((data) => mounted && setHealth(data))
                .catch(() => mounted && setHealth(null));

        fetchHealth();
        const interval = setInterval(fetchHealth, 15000);
        return () => {
            mounted = false;
            clearInterval(interval);
        };
    }, []);

    useEffect(() => {
        let mounted = true;
        const fetchFeedbackSummary = () =>
            getFeedbackSummary()
                .then((data) => mounted && setFeedbackSummary(data))
                .catch(() => mounted && setFeedbackSummary(null));

        fetchFeedbackSummary();
        const interval = setInterval(fetchFeedbackSummary, 30000);
        return () => {
            mounted = false;
            clearInterval(interval);
        };
    }, []);

    function handleNewQuery() {
        setCurrentResult(null);
        setStreamingText(null);
        setError(null);
        setFeedbackSent(false);
        streamAbortRef.current?.abort();
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function handleSubmit(query: string, userContext: string | null, fileName: string | null) {
        // Cancel any in-flight stream
        streamAbortRef.current?.abort();

        setError(null);
        setLoading(true);
        setStreamingText("");
        setCurrentResult(null);
        setFeedbackSent(false);

        // Holds the partial RouterResponse built from metadata event
        let pendingResult: RouterResponse | null = null;

        const controller = routeQueryStream(query, userContext, {
            onMetadata(data) {
                // Build a partial RouterResponse from the classification metadata
                // so ResponseDisplay can render domain badge + disclaimers immediately
                pendingResult = {
                    response: "",
                    classification: data.classification,
                    disclaimers: data.disclaimers ?? [],
                    safety_flags: data.safety_flags,
                    request_id: data.request_id,
                    sources: [],
                    pipeline_trace: [],
                };
                setCurrentResult(pendingResult);
            },
            onToken(text) {
                setStreamingText((prev) => (prev ?? "") + text);
            },
            onDone(data) {
                // Finalise the result with full text + sources
                const finalResult: RouterResponse = {
                    ...(pendingResult as RouterResponse),
                    response: data.full_text,
                    request_id: data.request_id,
                    sources: data.sources ?? [],
                };
                setCurrentResult(finalResult);
                setStreamingText(null);
                setLoading(false);
                setHistory((prev) => [
                    {
                        id: data.request_id,
                        query,
                        result: finalResult,
                        timestamp: new Date().toISOString(),
                        attached_file: fileName ?? undefined,
                    },
                    ...prev,
                ]);
            },
            onError(message) {
                setError(message);
                setStreamingText(null);
                setLoading(false);
            },
        });

        streamAbortRef.current = controller;
    }

    async function handleFeedback(rating: "up" | "down") {
        if (!currentResult || feedbackSent) return;
        try {
            await sendFeedback(
                currentResult.request_id,
                currentHistoryItem?.query || "",
                currentResult.response,
                rating
            );
            setFeedbackSent(true);
            const summary = await getFeedbackSummary();
            setFeedbackSummary(summary);
        } catch (feedbackError) {
            console.error("Failed to send feedback", feedbackError);
        }
    }

    const showCrisisResources = useMemo(
        () => Boolean(currentResult?.safety_flags.high_risk || currentResult?.safety_flags.self_harm),
        [currentResult]
    );

    return (
        <div className="min-h-screen bg-deep relative overflow-hidden font-sans text-stone-100 selection:bg-stone-300/30">
            <div className="relative mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 z-10">
                <header className="mb-10 pb-8 border-b border-border">
                    <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
                        <div className="max-w-2xl">
                            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 text-[11px] font-medium tracking-wide text-stone-400">
                                <Activity className="h-3.5 w-3.5" />
                                Responsible Multi-Agent Router
                            </div>
                            <h1 className="max-w-2xl font-display text-4xl font-semibold tracking-tight text-stone-100 sm:text-5xl">
                                SochSamajh AI
                            </h1>
                            <p className="mt-4 max-w-xl text-sm leading-7 text-stone-400 sm:text-base">
                                Get a routed answer, clear disclaimers, and visible safety signals without extra clutter.
                            </p>
                        </div>

                        <div className="grid gap-4 sm:grid-cols-2 lg:w-[22rem]">
                            <div className="rounded-xl border border-border bg-surface p-4">
                                <p className="text-[10px] font-semibold uppercase tracking-widest text-stone-500">
                                    Backend
                                </p>
                                <div className="mt-2 flex items-center gap-2">
                                    {health === null ? (
                                        <div className="h-3 w-16 animate-pulse rounded bg-border" />
                                    ) : (
                                        <>
                                            <span className={`h-2 w-2 rounded-full ${health.status === "ok" ? "bg-emerald-500" : "bg-amber-500"}`}></span>
                                            <p className="text-sm font-medium text-stone-300">
                                                {health.status === "ok" ? "System ready" : "Connection unstable"}
                                            </p>
                                        </>
                                    )}
                                </div>
                            </div>

                            <div className="rounded-xl border border-border bg-surface p-4">
                                <p className="text-[10px] font-semibold uppercase tracking-widest text-stone-500">
                                    Scope
                                </p>
                                <p className="mt-2 text-sm font-medium text-stone-300">Educational only</p>
                                <p className="mt-1 text-[11px] leading-relaxed text-stone-500">Not a substitute for a professional.</p>
                            </div>
                        </div>
                    </div>
                </header>

                <main className="grid gap-8 lg:grid-cols-[minmax(0,1.6fr)_minmax(280px,0.7fr)]">
                    <section className="space-y-6">
                        <div className="rounded-2xl border border-border bg-surface p-5 sm:p-8 shadow-sm">
                            <QueryInput onSubmit={handleSubmit} disabled={loading} />
                        </div>

                        {error && (
                            <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-4 text-sm text-rose-200">
                                <div className="flex items-start gap-3">
                                    <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                                    <p>{error}</p>
                                </div>
                            </div>
                        )}

                        {loading && !currentResult && <LoadingState />}

                        {currentResult && (
                            <div className="space-y-6">
                                <ResponseDisplay 
                                    result={currentResult} 
                                    query={currentHistoryItem?.query ?? ""}
                                    attachedFile={currentHistoryItem?.attached_file}
                                    streamingText={streamingText}
                                />

                                <div className="flex flex-col gap-4 rounded-xl border border-border bg-surface p-5 sm:flex-row sm:items-center sm:justify-between">
                                    <div>
                                        <p className="text-sm font-medium text-stone-200">Was this response useful?</p>
                                        <p className="mt-1 text-xs text-stone-500">
                                            Your feedback helps improve routing quality and safer fallback behavior.
                                        </p>
                                    </div>

                                    {feedbackSent ? (
                                        <span className="inline-flex items-center gap-2 rounded-lg border border-border bg-surface-hover px-3 py-2 text-xs font-medium text-stone-300">
                                            <CheckCircle className="h-4 w-4 text-stone-400" />
                                            Feedback recorded
                                        </span>
                                    ) : (
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => handleFeedback("up")}
                                                className="inline-flex items-center gap-2 rounded-lg border border-border bg-deep px-4 py-2 text-xs font-medium text-stone-300 hover:bg-surface-hover hover:text-stone-100 transition"
                                                title="Helpful"
                                            >
                                                <ThumbsUp className="h-4 w-4" />
                                                Helpful
                                            </button>
                                            <button
                                                onClick={() => handleFeedback("down")}
                                                className="inline-flex items-center gap-2 rounded-lg border border-border bg-deep px-4 py-2 text-xs font-medium text-stone-300 hover:bg-surface-hover hover:text-stone-100 transition"
                                                title="Not Helpful"
                                            >
                                                <ThumbsDown className="h-4 w-4" />
                                                Needs work
                                            </button>
                                        </div>
                                    )}
                                </div>

                                <div className="flex justify-start pt-2">
                                    <button
                                        onClick={handleNewQuery}
                                        className="group inline-flex items-center gap-2 rounded-lg border border-border bg-surface px-5 py-2.5 text-sm font-medium text-stone-300 transition hover:bg-surface-hover hover:text-stone-100"
                                    >
                                        <RotateCcw className="h-4 w-4 transition-transform group-hover:-rotate-180 duration-500" />
                                        Start new query
                                    </button>
                                </div>
                            </div>
                        )}

                        {showCrisisResources && (
                            <div className="rounded-xl border border-rose-500/20 bg-rose-500/5 p-4 sm:p-5">
                                <div className="flex gap-3">
                                    <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-rose-400" />
                                    <div className="space-y-2">
                                        <p className="text-sm font-semibold text-rose-200">Immediate support matters here.</p>
                                        <p className="text-sm leading-6 text-rose-300/80">
                                            If this feels urgent or unsafe, contact local emergency services, the nearest
                                            hospital, or a trusted person who can stay with you now. In India, emergency
                                            support is available at 112.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </section>

                    <aside className="space-y-6">
                        <section className="rounded-2xl border border-border bg-surface p-6">
                            <div className="mb-5 flex items-center gap-3">
                                <MessageSquareWarning className="h-4 w-4 text-stone-400" />
                                <h2 className="text-xs font-semibold uppercase tracking-widest text-stone-300">
                                    Feedback queue
                                </h2>
                            </div>
                            
                            {feedbackSummary === null ? (
                                <div className="space-y-4">
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="rounded-xl border border-border bg-deep p-4 space-y-2">
                                            <div className="h-2 w-10 animate-pulse rounded bg-border" />
                                            <div className="h-6 w-8 animate-pulse rounded bg-border" />
                                        </div>
                                        <div className="rounded-xl border border-border bg-deep p-4 space-y-2">
                                            <div className="h-2 w-16 animate-pulse rounded bg-border" />
                                            <div className="h-6 w-8 animate-pulse rounded bg-border" />
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <div className="h-16 w-full animate-pulse rounded-xl bg-border" />
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="rounded-xl border border-border bg-deep p-4">
                                            <p className="text-[10px] font-medium uppercase tracking-widest text-stone-500">Total</p>
                                            <p className="mt-1 text-2xl font-semibold text-stone-200">{feedbackSummary.total}</p>
                                        </div>
                                        <div className="rounded-xl border border-border bg-deep p-4">
                                            <p className="text-[10px] font-medium uppercase tracking-widest text-stone-500">Needs review</p>
                                            <p className="mt-1 text-2xl font-semibold text-stone-400">
                                                {feedbackSummary.negative_feedback_queue.length}
                                            </p>
                                        </div>
                                    </div>
                                    {feedbackSummary.negative_feedback_queue.length > 0 && (
                                        <div className="mt-4 space-y-2">
                                            {feedbackSummary.negative_feedback_queue.slice(0, 3).map((item) => (
                                                <div key={`${item.request_id}-${item.timestamp}`} className="rounded-xl border border-border bg-deep p-3">
                                                    <p className="line-clamp-2 text-xs leading-5 text-stone-400">{item.query_text}</p>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </>
                            )}
                        </section>

                        <section className="rounded-2xl border border-border bg-surface p-6">
                            <div className="mb-5 flex items-center gap-3">
                                <CheckCircle className="h-4 w-4 text-stone-400" />
                                <h2 className="text-xs font-semibold uppercase tracking-widest text-stone-300">
                                    Quick tips
                                </h2>
                            </div>
                            <div className="space-y-3 text-sm text-stone-400">
                                <div className="rounded-xl border border-border bg-deep p-4">
                                    Add symptoms, timeline, or jurisdiction for better routing.
                                </div>
                                <div className="rounded-xl border border-border bg-deep p-4">
                                    Mention urgency if the situation feels serious.
                                </div>
                            </div>
                        </section>

                        {history.length > 0 && (
                            <section className="rounded-2xl border border-border bg-surface p-6">
                                <div className="mb-5 flex items-center gap-3">
                                    <Activity className="h-4 w-4 text-stone-400" />
                                    <h2 className="text-xs font-semibold uppercase tracking-widest text-stone-300">
                                        Recent history
                                    </h2>
                                </div>
                                <div className="space-y-3">
                                    {history.map((item, idx) => (
                                        <button
                                            key={item.id}
                                            onClick={() => {
                                                setCurrentResult(item.result);
                                                setFeedbackSent(false);
                                            }}
                                            className="w-full rounded-xl border border-border bg-deep p-4 text-left transition hover:bg-surface-hover hover:border-stone-700"
                                        >
                                            <div className="flex items-start justify-between gap-4">
                                                <p className="line-clamp-2 text-sm leading-6 text-stone-300">
                                                    {item.query}
                                                </p>
                                                <span className="whitespace-nowrap rounded-md bg-surface-hover px-2 py-1 text-[10px] font-medium uppercase tracking-wider text-stone-500 mt-1 block w-fit">
                                                    {item.result.classification.domain}
                                                </span>
                                            </div>
                                            {item.attached_file && (
                                                <p className="mt-1.5 text-[11px] text-stone-500 line-clamp-1">
                                                    📎 {item.attached_file}
                                                </p>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            </section>
                        )}
                    </aside>
                </main>
            </div>
        </div>
    );
}

