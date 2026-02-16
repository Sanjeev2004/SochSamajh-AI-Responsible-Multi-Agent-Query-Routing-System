import { useEffect, useMemo, useState } from "react";
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
                    timestamp: new Date().toISOString(),
                },
                ...prev,
            ]);
        } catch {
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
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-indigo-950/20 to-slate-950 text-slate-100 relative overflow-hidden">
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl animate-pulse"></div>
                <div
                    className="absolute bottom-0 right-1/4 w-96 h-96 bg-violet-500/10 rounded-full blur-3xl animate-pulse"
                    style={{ animationDelay: "1s" }}
                ></div>
            </div>

            <div className="mx-auto max-w-4xl px-6 py-8 relative z-10">
                <header className="mb-12 text-center sm:text-left">
                    <div className="inline-block">
                        <h1 className="text-4xl sm:text-3xl font-bold bg-gradient-to-r from-indigo-400 via-violet-400 to-indigo-400 bg-clip-text text-transparent mb-2">
                            SochSamajh AI Router
                        </h1>
                        <p className="text-sm text-slate-400 tracking-widest uppercase">
                            Safety-Aware Medical and Legal Assistant
                        </p>
                    </div>
                    <div className="mt-4 flex items-center justify-center sm:justify-start gap-3">
                        <div
                            className={`h-2 w-2 rounded-full ${
                                health?.status === "ok" ? "bg-emerald-400 animate-pulse" : "bg-slate-600"
                            }`}
                        ></div>
                        <span className="text-xs text-slate-400">
                            {health?.status === "ok" ? "System Ready" : "Backend Unavailable"}
                        </span>
                    </div>
                </header>

                <main className="space-y-8">
                    <QueryInput onSubmit={handleSubmit} disabled={loading} />

                    {error && (
                        <div className="rounded-xl bg-gradient-to-r from-rose-500/20 to-rose-500/10 backdrop-blur border border-rose-500/30 p-4 text-xs text-rose-100 animate-in fade-in slide-in-from-top-2 duration-300">
                            Warning: {error}
                        </div>
                    )}

                    {loading && <LoadingState />}

                    {currentResult && !loading && <ResponseDisplay result={currentResult} />}

                    {showCrisisResources && (
                        <div className="rounded-xl bg-gradient-to-r from-amber-500/20 to-amber-500/10 backdrop-blur border border-amber-500/30 p-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                            <p className="text-xs text-amber-100 leading-relaxed">
                                <strong>Crisis Support (U.S.):</strong> Call 911 for emergencies | Call or text 988
                                (Suicide and Crisis Lifeline) | Text HOME to 741741 (Crisis Text Line)
                            </p>
                        </div>
                    )}

                    {history.length > 0 && (
                        <div className="border-t border-slate-700/50 pt-8 mt-12">
                            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-widest mb-4">
                                Conversation History
                            </h3>
                            <div className="space-y-2 max-h-64 overflow-y-auto">
                                {history.map((item, idx) => (
                                    <button
                                        key={item.id}
                                        onClick={() => setCurrentResult(item.result)}
                                        className="group w-full text-left px-4 py-3 rounded-lg bg-gradient-to-r from-slate-800/50 to-slate-800/20 hover:from-indigo-500/20 hover:to-violet-500/20 border border-slate-700/50 hover:border-indigo-500/30 transition-all duration-300 transform hover:translate-x-1"
                                    >
                                        <p className="text-sm text-slate-200 group-hover:text-indigo-300 transition line-clamp-2">
                                            {idx === 0 && <span className="text-indigo-400 mr-2">-&gt;</span>}
                                            {item.query}
                                        </p>
                                        <p className="text-xs text-slate-500 mt-1">
                                            {new Date(item.timestamp).toLocaleTimeString()}
                                        </p>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}
