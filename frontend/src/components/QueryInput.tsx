import { useMemo, useState } from "react";
import { Send } from "lucide-react";

interface QueryInputProps {
    onSubmit: (query: string) => void;
    disabled?: boolean;
}

const MAX_CHARS = 2000;

export function QueryInput({ onSubmit, disabled }: QueryInputProps) {
    const [value, setValue] = useState("");

    const remaining = useMemo(() => MAX_CHARS - value.length, [value]);

    function handleSubmit() {
        if (!value.trim()) return;
        onSubmit(value.trim());
    }

    return (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold">Ask a question</h2>
                <span className="text-xs text-slate-400">Safety-aware routing enabled</span>
            </div>
            <p className="mt-2 text-sm text-slate-400">
                This system provides educational information only and will refuse unsafe requests.
            </p>
            <textarea
                value={value}
                onChange={(event) => setValue(event.target.value)}
                maxLength={MAX_CHARS}
                placeholder="Type your medical or legal question here..."
                className="mt-4 h-32 w-full resize-none rounded-xl border border-slate-800 bg-slate-950 p-4 text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            <div className="mt-3 flex items-center justify-between">
                <span className={`text-xs ${remaining < 100 ? "text-amber-400" : "text-slate-400"}`}>
                    {remaining} characters remaining
                </span>
                <button
                    onClick={handleSubmit}
                    disabled={disabled || !value.trim()}
                    className="inline-flex items-center gap-2 rounded-full bg-indigo-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-50"
                >
                    <Send className="h-4 w-4" />
                    Submit
                </button>
            </div>
        </div>
    );
}
