const steps = [
    "Screening for safety signals",
    "Classifying intent and risk",
    "Routing to specialized agent",
    "Formatting final response"
];

export function LoadingState() {
    return (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <p className="text-sm text-slate-300">Processing...</p>
            <div className="mt-4 space-y-3">
                {steps.map((step, index) => (
                    <div key={step} className="flex items-center gap-3">
                        <span className="h-2 w-2 animate-pulse rounded-full bg-indigo-400" style={{ animationDelay: `${index * 0.2}s` }} />
                        <span className="text-sm text-slate-200">{step}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
