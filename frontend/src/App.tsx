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
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
            <div className="mx-auto max-w-4xl px-6 py-8">
                {/* Minimal Header */}
                <header className="mb-12 flex items-center justify-between border-b border-slate-800 pb-6">
                    <div>
                        <h1 className="text-2xl font-bold">Medical & Legal Router</h1>
                        <p className="mt-1 text-xs text-slate-400">Safety-aware AI assistant</p>
                    </div>
                    <div className="text-right text-xs text-slate-400">
                        {health?.status === "ok" ? (
                            <p className="text-emerald-400">Ready</p>
                        ) : (
                            <p className="text-slate-500">Offline</p>
                        )}
                    </div>
                </header>

                {/* Main Content - Single Column */}
                <main className="space-y-8">
                    {/* Query Input */}
                    <QueryInput onSubmit={handleSubmit} disabled={loading} />

                    {/* Error */}
                    {error && (
                        <div className="rounded-lg bg-rose-500/10 p-3 text-xs text-rose-100 border border-rose-500/30">
                            {error}
                        </div>
                    )}

                    {/* Loading State */}
                    {loading && <LoadingState />}

                    {/* Response */}
                    {currentResult && !loading && <ResponseDisplay result={currentResult} />}

                    {/* Crisis Resources */}
                    {showCrisisResources && (
                        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4">
                            <p className="text-xs text-amber-100 leading-relaxed">
                                <strong>Crisis Support:</strong> Call 988 (US) | Text HOME to 741741 | Emergency: 911
                            </p>
                        </div>
                    )}

                    {/* History */}
                    {history.length > 0 && (
                        <div className="border-t border-slate-800 pt-8">
                            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-4">Recent</h3>
                            <div className="space-y-2 max-h-48 overflow-y-auto">
                                {history.map((item) => (
                                    <button
                                        key={item.id}
                                        onClick={() => setCurrentResult(item.result)}
                                        className="w-full text-left px-3 py-2 rounded-md text-xs text-slate-400 hover:bg-slate-800/50 transition truncate"
                                    >
                                        {item.query}
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
