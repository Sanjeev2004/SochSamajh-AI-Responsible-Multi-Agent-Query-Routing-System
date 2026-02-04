import { useEffect, useMemo, useState } from "react";
import { Activity, HeartPulse } from "lucide-react";
import { getHealth, routeQuery } from "./hooks/useApi";
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
        } catch (err) {
            setError("Unable to process the request. Please try again.");
        } finally {
            setLoading(false);
        }
    }

    const showCrisisResources = useMemo(
        () => currentResult?.safety_flags.high_risk || currentResult?.safety_flags.self_harm,
        [currentResult]
    );

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100">
            <div className="mx-auto max-w-5xl px-6 py-12">
                <header className="flex flex-col gap-6">
                    <div className="flex items-center gap-3">
                        <div className="rounded-2xl bg-indigo-500/20 p-3">
                            <HeartPulse className="h-6 w-6 text-indigo-300" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold">Medical & Legal Query Router</h1>
                            <p className="text-sm text-slate-400">Safety-aware, multi-agent routing with LangGraph + LangSmith</p>
                        </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                        <span className="inline-flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1 text-xs text-slate-300">
                            <Activity className="h-4 w-4 text-emerald-400" />
                            {health?.status === "ok" ? "Backend healthy" : "Backend unreachable"}
                        </span>
                        {health?.model && (
                            <span className="rounded-full border border-slate-800 bg-slate-900/60 px-3 py-1 text-xs text-slate-300">
                                Model: {health.model}
                            </span>
                        )}
                    </div>
                </header>

                <main className="mt-10 grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
                    <div className="space-y-6">
                        <QueryInput onSubmit={handleSubmit} disabled={loading} />
                        {error && <p className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-4 text-sm text-rose-100">{error}</p>}
                        {loading && <LoadingState />}
                        {currentResult && !loading && <ResponseDisplay result={currentResult} />}
                    </div>

                    <aside className="space-y-6">
                        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
                            <h2 className="text-lg font-semibold">Response history</h2>
                            <div className="mt-4 space-y-4">
                                {history.length === 0 && <p className="text-sm text-slate-400">No queries yet.</p>}
                                {history.map((item) => (
                                    <button
                                        key={item.id}
                                        onClick={() => setCurrentResult(item.result)}
                                        className="w-full rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-left text-xs text-slate-300 transition hover:border-indigo-400/60"
                                    >
                                        <p className="font-semibold text-slate-200">{item.query}</p>
                                        <p className="mt-1 text-[11px] text-slate-500">{new Date(item.timestamp).toLocaleString()}</p>
                                    </button>
                                ))}
                            </div>
                        </section>

                        {showCrisisResources && (
                            <section className="rounded-2xl border border-amber-500/40 bg-amber-500/10 p-6">
                                <h2 className="text-lg font-semibold text-amber-100">Crisis resources</h2>
                                <p className="mt-2 text-sm text-amber-100">
                                    If you or someone else is in danger, call local emergency services. In the U.S., call or text 988
                                    for the Suicide & Crisis Lifeline, or text HOME to 741741 for the Crisis Text Line.
                                </p>
                            </section>
                        )}
                    </aside>
                </main>
            </div>
        </div>
    );
}
