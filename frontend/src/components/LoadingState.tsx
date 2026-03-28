export function LoadingState() {
    return (
        <div className="overflow-hidden rounded-[2rem] border border-teal-300/20 bg-teal-300/10 p-5 backdrop-blur-xl">
            <div className="flex items-center gap-3">
                <div className="flex gap-2">
                    {[0, 1, 2].map((index) => (
                        <div
                            key={index}
                            className="h-2.5 w-2.5 rounded-full bg-gradient-to-r from-teal-300 to-amber-300"
                            style={{
                                animation: "pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite",
                                animationDelay: `${index * 0.2}s`
                            }}
                        />
                    ))}
                </div>
                <div>
                    <p className="text-sm font-medium text-stone-100">Analyzing your query</p>
                    <p className="text-xs text-stone-400">Checking intent, risk, and the safest route for a response.</p>
                </div>
            </div>

            <div className="mt-4 space-y-3">
                <div className="h-4 w-4/5 rounded-full bg-white/10" />
                <div className="h-4 w-full rounded-full bg-white/10" />
                <div className="h-4 w-3/5 rounded-full bg-white/10" />
            </div>
        </div>
    );
}
