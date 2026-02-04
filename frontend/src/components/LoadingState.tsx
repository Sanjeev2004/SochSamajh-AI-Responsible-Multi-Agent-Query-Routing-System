export function LoadingState() {
    return (
        <div className="flex items-center gap-3 rounded-lg border border-slate-700 bg-slate-800/50 p-4">
            <div className="flex gap-1.5">
                {[0, 1, 2].map((i) => (
                    <div
                        key={i}
                        className="h-1.5 w-1.5 rounded-full bg-indigo-500"
                        style={{
                            animation: `pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite`,
                            animationDelay: `${i * 0.3}s`
                        }}
                    />
                ))}
            </div>
            <span className="text-xs text-slate-400">Processing...</span>
        </div>
    );
}
