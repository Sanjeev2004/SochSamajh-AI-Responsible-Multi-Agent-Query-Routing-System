import { useEffect, useMemo, useState } from "react";
import {
    Activity,
    AlertTriangle,
    CheckCircle,
    ThumbsDown,
    ThumbsUp
} from "lucide-react";
import { getHealth, routeQuery, sendFeedback } from "./hooks/useApi";
import { HistoryItem, RouterResponse } from "./types";
import { QueryInput } from "./components/QueryInput";
import { ResponseDisplay } from "./components/ResponseDisplay";
import { LoadingState } from "./components/LoadingState";

export default function App() {
    const [health, setHealth] = useState<{ status: string; model: string } | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [currentResult, setCurrentResult] = useState<RouterResponse | null>(null);
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [feedbackSent, setFeedbackSent] = useState(false);

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

    async function handleSubmit(query: string) {
        setError(null);
        setLoading(true);
        setFeedbackSent(false);
        try {
            const result = await routeQuery(query);
            setCurrentResult(result);
            setHistory((prev) => [
                {
                    id: result.request_id,
                    query,
                    result,
                    timestamp: new Date().toISOString()
                },
                ...prev
            ]);
        } catch {
            setError("We could not reach the router right now. Please try again in a moment.");
        } finally {
            setLoading(false);
        }
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
        } catch (feedbackError) {
            console.error("Failed to send feedback", feedbackError);
        }
    }

    const showCrisisResources = useMemo(
        () => Boolean(currentResult?.safety_flags.high_risk || currentResult?.safety_flags.self_harm),
        [currentResult]
    );

    return (
        <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(39,140,137,0.18),_transparent_28%),radial-gradient(circle_at_85%_18%,_rgba(213,119,54,0.16),_transparent_22%),linear-gradient(180deg,_#0d1417_0%,_#111a1d_48%,_#0d1315_100%)] text-stone-100">
            <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
                <header className="mb-8 overflow-hidden rounded-[2rem] border border-white/10 bg-white/5 px-6 py-6 shadow-2xl shadow-black/20 backdrop-blur-xl sm:px-8 sm:py-8">
                    <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
                        <div className="max-w-2xl">
                            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.28em] text-teal-100/90">
                                <Activity className="h-3.5 w-3.5 text-teal-300" />
                                Responsible Multi-Agent Router
                            </div>
                            <h1 className="max-w-2xl font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua',serif] text-4xl leading-tight text-stone-50 sm:text-5xl">
                                SochSamagh AI
                            </h1>
                            <p className="mt-4 max-w-xl text-sm leading-7 text-stone-300 sm:text-base">
                                Get a routed answer, clear disclaimers, and visible safety signals without extra clutter.
                            </p>
                        </div>

                        <div className="grid gap-3 sm:grid-cols-2 lg:w-[20rem]">
                            <div className="rounded-2xl border border-teal-400/20 bg-teal-400/10 p-4">
                                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-teal-200/80">
                                    Backend
                                </p>
                                <div className="mt-2 flex items-center gap-2">
                                    <span
                                        className={`h-2.5 w-2.5 rounded-full ${
                                            health?.status === "ok" ? "bg-emerald-400 shadow-lg shadow-emerald-400/40" : "bg-amber-400"
                                        }`}
                                    />
                                    <p className="text-sm font-medium text-stone-100">
                                        {health?.status === "ok" ? "System ready" : "Connection unstable"}
                                    </p>
                                </div>
                                <p className="mt-2 text-xs text-stone-300/85">{health?.status === "ok" ? `Model: ${health?.model ?? "configured"}` : "API unavailable"}</p>
                            </div>

                            <div className="rounded-2xl border border-amber-400/20 bg-amber-400/10 p-4">
                                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-amber-200/80">
                                    Scope
                                </p>
                                <p className="mt-2 text-sm font-medium text-stone-100">Educational guidance only</p>
                                <p className="mt-2 text-xs leading-5 text-stone-300/85">Not a replacement for a doctor, lawyer, or emergency help.</p>
                            </div>
                        </div>
                    </div>
                </header>

                <main className="grid gap-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(260px,0.7fr)]">
                    <section className="space-y-6">
                        <div className="rounded-[2rem] border border-white/10 bg-black/20 p-4 shadow-2xl shadow-black/10 backdrop-blur-xl sm:p-6">
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

                        {loading && <LoadingState />}

                        {currentResult && !loading && (
                            <div className="space-y-4">
                                <ResponseDisplay result={currentResult} />

                                <div className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-white/5 p-4 sm:flex-row sm:items-center sm:justify-between">
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

                    <aside className="space-y-6">
                        <section className="rounded-[2rem] border border-white/10 bg-white/5 p-5 shadow-xl shadow-black/10 backdrop-blur-xl">
                            <div className="mb-4 flex items-center gap-2">
                                <CheckCircle className="h-4 w-4 text-emerald-300" />
                                <h2 className="text-sm font-semibold uppercase tracking-[0.2em] text-stone-200">
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
                            <section className="rounded-[2rem] border border-white/10 bg-white/5 p-5 shadow-xl shadow-black/10 backdrop-blur-xl">
                                <div className="mb-4 flex items-center gap-2">
                                    <Activity className="h-4 w-4 text-cyan-300" />
                                    <h2 className="text-sm font-semibold uppercase tracking-[0.2em] text-stone-200">
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
                                                <span className="whitespace-nowrap rounded-full bg-white/5 px-2 py-1 text-[10px] uppercase tracking-[0.2em] text-stone-400">
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
