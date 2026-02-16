import { useState } from "react";
import { Sparkles } from "lucide-react";

interface QueryInputProps {
    onSubmit: (query: string) => void;
    disabled?: boolean;
}

const MAX_CHARS = 2000;

export function QueryInput({ onSubmit, disabled }: QueryInputProps) {
    const [value, setValue] = useState("");
    const [focused, setFocused] = useState(false);

    function handleSubmit() {
        if (!value.trim()) return;
        onSubmit(value.trim());
        setValue("");
    }

    function handleKeyDown(e: React.KeyboardEvent) {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            handleSubmit();
        }
    }

    return (
        <div className="space-y-4 group">
            <div
                className={`relative rounded-xl transition-all duration-300 ${
                    focused
                        ? "ring-2 ring-indigo-500/50 bg-gradient-to-br from-slate-900/80 to-indigo-950/30 border border-indigo-500/30"
                        : "bg-gradient-to-br from-slate-900/50 to-slate-800/30 border border-slate-700/50 hover:border-indigo-500/20"
                } backdrop-blur`}
            >
                <textarea
                    value={value}
                    onChange={(event) => setValue(event.target.value)}
                    onKeyDown={handleKeyDown}
                    onFocus={() => setFocused(true)}
                    onBlur={() => setFocused(false)}
                    maxLength={MAX_CHARS}
                    placeholder="Ask your medical or legal question..."
                    className="w-full resize-none rounded-xl bg-transparent p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition-colors"
                    rows={5}
                />
            </div>

            <div className="flex items-center justify-between px-1">
                <div className="flex items-center gap-2">
                    <span
                        className={`text-xs font-medium transition-colors ${
                            value.length > MAX_CHARS * 0.8 ? "text-amber-400" : "text-slate-500"
                        }`}
                    >
                        {value.length} / {MAX_CHARS}
                    </span>
                    {value.length > 0 && (
                        <div className="h-1 w-24 bg-gradient-to-r from-indigo-500/30 to-violet-500/30 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-indigo-500 to-violet-500 transition-all duration-300"
                                style={{ width: `${(value.length / MAX_CHARS) * 100}%` }}
                            ></div>
                        </div>
                    )}
                </div>

                <button
                    onClick={handleSubmit}
                    disabled={disabled || !value.trim()}
                    className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition-all duration-300 transform hover:scale-105 active:scale-95 ${
                        disabled || !value.trim()
                            ? "opacity-40 cursor-not-allowed bg-slate-700"
                            : "bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/50"
                    }`}
                >
                    <Sparkles className="h-3.5 w-3.5" />
                    Ask
                </button>
            </div>
        </div>
    );
}
