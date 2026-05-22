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
        <div className="min-h-screen bg-deep relative overflow-hidden font-sans text-stone-100 selection:bg-teal-400/30">
            {/* Ambient Animated Background Blobs */}
            <div className="pointer-events-none absolute inset-0 overflow-hidden">
                <div className="absolute -left-[10%] top-0 h-[500px] w-[500px] animate-float rounded-full bg-teal-500/10 mix-blend-screen blur-[120px]" />
                <div className="absolute right-0 top-[20%] h-[600px] w-[600px] animate-pulse-slow rounded-full bg-violet-500/10 mix-blend-screen blur-[150px]" />
                <div className="absolute bottom-0 left-[20%] h-[500px] w-[500px] animate-float rounded-full bg-emerald-500/10 mix-blend-screen blur-[120px]" style={{ animationDelay: '2s' }} />
            </div>

            <div className="relative mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 z-10">
                <header className="mb-10 overflow-hidden rounded-[2.5rem] border border-white/10 bg-white/[0.02] px-6 py-8 shadow-2xl backdrop-blur-2xl sm:px-10 sm:py-10 transition-all hover:bg-white/[0.03]">
                    <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
                        <div className="max-w-2xl">
                            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-teal-400/30 bg-teal-400/10 px-4 py-1.5 text-[10px] font-bold uppercase tracking-widest text-teal-300 shadow-glow-teal">
                                <Activity className="h-3.5 w-3.5" />
                                Responsible Multi-Agent Router
                            </div>
                            <h1 className="max-w-2xl font-display text-5xl font-bold tracking-tight text-white drop-shadow-md sm:text-6xl bg-clip-text text-transparent bg-gradient-to-r from-white via-stone-200 to-stone-400">
                                SochSamajh AI
                            </h1>
                            <p className="mt-4 max-w-xl text-sm leading-7 text-stone-300 sm:text-base">
                                Get a routed answer, clear disclaimers, and visible safety signals without extra clutter.
                            </p>
                        </div>

                        <div className="grid gap-4 sm:grid-cols-2 lg:w-[22rem]">
                            <div className="rounded-[1.5rem] border border-white/5 bg-white/[0.02] p-5 backdrop-blur-md">
                                <p className="text-[10px] font-bold uppercase tracking-widest text-stone-500">
                                    Backend
                                </p>
                                <div className="mt-3 flex items-center gap-3">
                                    {health === null ? (
                                        <div className="flex flex-col gap-2 w-full pt-1">
                                            <div className="h-3 w-16 animate-pulse rounded-full bg-white/10" />
                                        </div>
                                    ) : (
                                        <>
                                            <div className="relative flex h-3 w-3 items-center justify-center">
                                                <span className={`absolute inline-flex h-full w-full animate-ping rounded-full opacity-75 ${health.status === "ok" ? "bg-teal-400" : "bg-amber-400"}`}></span>
                                                <span className={`relative inline-flex h-2.5 w-2.5 rounded-full ${health.status === "ok" ? "bg-teal-500" : "bg-amber-500"}`}></span>
                                            </div>
                                            <p className="text-sm font-semibold text-stone-200">
                                                {health.status === "ok" ? "System ready" : "Connection unstable"}
                                            </p>
                                        </>
                                    )}
                                </div>
                            </div>

                            <div className="rounded-[1.5rem] border border-white/5 bg-white/[0.02] p-5 backdrop-blur-md">
                                <p className="text-[10px] font-bold uppercase tracking-widest text-stone-500">
                                    Scope
                                </p>
                                <p className="mt-2 text-sm font-semibold text-stone-200">Educational only</p>
                                <p className="mt-1 text-[11px] leading-relaxed text-stone-400">Not a replacement for a doctor or lawyer.</p>
                            </div>
                        </div>
                    </div>
                </header>

                <main className="grid gap-8 lg:grid-cols-[minmax(0,1.6fr)_minmax(280px,0.7fr)]">
                    <section className="space-y-8">
                        <div className="rounded-[2.5rem] border border-white/10 bg-white/[0.02] p-5 shadow-2xl backdrop-blur-xl sm:p-8 transition-all duration-300 hover:border-white/20">
                            <QueryInput onSubmit={handleSubmit} disabled={loading} />
                        </div>

                        {error && (
                            <div className="rounded-2xl border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-100">
                                <div className="flex items-start gap-3">
                                    <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                                    <p>{error}</p>
                                </div>
                            </div>
                        )}

                        {loading && !currentResult && <LoadingState />}

                        {currentResult && (
                            <div className="space-y-4">
                                <ResponseDisplay 
                                    result={currentResult} 
                                    query={currentHistoryItem?.query ?? ""}
                                    attachedFile={currentHistoryItem?.attached_file}
                                    streamingText={streamingText}
                                />

                                <div className="flex flex-col gap-4 rounded-[1.5rem] border border-white/10 bg-white/[0.02] p-5 backdrop-blur-md sm:flex-row sm:items-center sm:justify-between transition-all duration-300 hover:bg-white/[0.04]">
                                    <div>
                                        <p className="text-sm font-medium text-stone-100">Was this response useful?</p>
                                        <p className="mt-1 text-xs text-stone-400">
                                            Your feedback helps improve routing quality and safer fallback behavior.
                                        </p>
                                    </div>

                                    {feedbackSent ? (
                                        <span className="inline-flex items-center gap-2 rounded-full border border-emerald-400/25 bg-emerald-400/10 px-3 py-2 text-xs font-medium text-emerald-200">
                                            <CheckCircle className="h-4 w-4" />
                                            Feedback recorded
                                        </span>
                                    ) : (
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => handleFeedback("up")}
                                                className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-stone-200 transition hover:border-emerald-400/30 hover:bg-emerald-400/10 hover:text-emerald-200"
                                                title="Helpful"
                                            >
                                                <ThumbsUp className="h-4 w-4" />
                                                Helpful
                                            </button>
                                            <button
                                                onClick={() => handleFeedback("down")}
                                                className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-stone-200 transition hover:border-rose-400/30 hover:bg-rose-400/10 hover:text-rose-200"
                                                title="Not Helpful"
                                            >
                                                <ThumbsDown className="h-4 w-4" />
                                                Needs work
                                            </button>
                                        </div>
                                    )}
                                </div>

                                <div className="flex justify-center pt-6">
                                    <button
                                        onClick={handleNewQuery}
                                        className="group inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-6 py-3 font-display text-sm font-semibold text-stone-300 backdrop-blur-md transition-all duration-300 hover:-translate-y-1 hover:border-violet-400/40 hover:bg-violet-400/10 hover:text-white hover:shadow-glow-violet active:scale-95"
                                    >
                                        <RotateCcw className="h-4 w-4 transition-transform group-hover:-rotate-180 duration-500" />
                                        Start new query
                                    </button>
                                </div>
                            </div>
                        )}

                        {showCrisisResources && (
                            <div className="rounded-2xl border border-rose-400/30 bg-rose-400/10 p-4 sm:p-5">
                                <div className="flex gap-3">
                                    <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-rose-200" />
                                    <div className="space-y-2">
                                        <p className="text-sm font-semibold text-rose-50">Immediate support matters here.</p>
                                        <p className="text-sm leading-6 text-rose-100/90">
                                            If this feels urgent or unsafe, contact local emergency services, the nearest
                                            hospital, or a trusted person who can stay with you now. In India, emergency
                                            support is available at 112.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}
                    </section>

                    <aside className="space-y-8">
                        <section className="rounded-[2rem] border border-white/10 bg-white/[0.02] p-6 shadow-2xl backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:border-white/20 hover:shadow-glow-violet">
                            <div className="mb-6 flex items-center gap-3">
                                <MessageSquareWarning className="h-4 w-4 text-violet-400" />
                                <h2 className="font-display text-xs font-bold uppercase tracking-[0.2em] text-stone-300">
                                    Feedback queue
                                </h2>
                            </div>
                            
                            {feedbackSummary === null ? (
                                <div className="space-y-4">
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="rounded-2xl border border-white/8 bg-black/15 p-4 space-y-2">
                                            <div className="h-2 w-10 animate-pulse rounded bg-white/10" />
                                            <div className="h-6 w-8 animate-pulse rounded bg-white/10" />
                                        </div>
                                        <div className="rounded-2xl border border-white/8 bg-black/15 p-4 space-y-2">
                                            <div className="h-2 w-16 animate-pulse rounded bg-white/10" />
                                            <div className="h-6 w-8 animate-pulse rounded bg-white/10" />
                                        </div>
                                    </div>
                                    <div className="space-y-2">
                                        <div className="h-16 w-full animate-pulse rounded-2xl bg-white/10" />
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div className="rounded-2xl border border-white/8 bg-black/15 p-4">
                                            <p className="text-[11px] uppercase tracking-[0.18em] text-stone-500">Total</p>
                                            <p className="mt-2 text-2xl font-semibold text-stone-100">{feedbackSummary.total}</p>
                                        </div>
                                        <div className="rounded-2xl border border-white/8 bg-black/15 p-4">
                                            <p className="text-[11px] uppercase tracking-[0.18em] text-stone-500">Needs review</p>
                                            <p className="mt-2 text-2xl font-semibold text-amber-100">
                                                {feedbackSummary.negative_feedback_queue.length}
                                            </p>
                                        </div>
                                    </div>
                                    {feedbackSummary.negative_feedback_queue.length > 0 && (
                                        <div className="mt-3 space-y-2">
                                            {feedbackSummary.negative_feedback_queue.slice(0, 3).map((item) => (
                                                <div key={`${item.request_id}-${item.timestamp}`} className="rounded-2xl border border-amber-300/15 bg-amber-300/10 p-3">
                                                    <p className="line-clamp-2 text-xs leading-5 text-amber-50/90">{item.query_text}</p>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </>
                            )}
                        </section>

                        <section className="rounded-[2rem] border border-white/10 bg-white/[0.02] p-6 shadow-2xl backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:border-white/20 hover:shadow-glow-teal">
                            <div className="mb-6 flex items-center gap-3">
                                <CheckCircle className="h-4 w-4 text-teal-400" />
                                <h2 className="font-display text-xs font-bold uppercase tracking-[0.2em] text-stone-300">
                                    Quick tips
                                </h2>
                            </div>
                            <div className="space-y-3 text-sm text-stone-300">
                                <div className="rounded-2xl border border-white/8 bg-black/15 p-4">
                                    Add symptoms, timeline, or jurisdiction.
                                </div>
                                <div className="rounded-2xl border border-white/8 bg-black/15 p-4">
                                    Mention urgency if the situation feels serious.
                                </div>
                            </div>
                        </section>

                        {history.length > 0 && (
                            <section className="rounded-[2rem] border border-white/10 bg-white/[0.02] p-6 shadow-2xl backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:border-white/20 hover:shadow-glow-teal">
                                <div className="mb-6 flex items-center gap-3">
                                    <Activity className="h-4 w-4 text-teal-400" />
                                    <h2 className="font-display text-xs font-bold uppercase tracking-[0.2em] text-stone-300">
                                        Recent conversation
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
                                            className="w-full rounded-2xl border border-white/8 bg-black/15 p-4 text-left transition hover:border-cyan-400/25 hover:bg-cyan-400/10"
                                        >
                                            <div className="flex items-start justify-between gap-4">
                                                <p className="line-clamp-3 text-sm leading-6 text-stone-200">
                                                    {idx === 0 ? "Latest: " : ""}
                                                    {item.query}
                                                </p>
                                                {item.attached_file && (
                                                    <p className="mt-1 text-[11px] text-teal-300/80 line-clamp-1">
                                                        📎 {item.attached_file}
                                                    </p>
                                                )}
                                                <span className="whitespace-nowrap rounded-full bg-white/5 px-2 py-1 text-[10px] uppercase tracking-[0.2em] text-stone-400 mt-2 block w-fit">
                                                    {item.result.classification.domain}
                                                </span>
                                            </div>
                                            <p className="mt-2 text-xs text-stone-500">
                                                {new Date(item.timestamp).toLocaleString()}
                                            </p>
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
