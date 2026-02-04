import { useState } from "react";
import { Send } from "lucide-react";

interface QueryInputProps {
    onSubmit: (query: string) => void;
    disabled?: boolean;
}

const MAX_CHARS = 2000;

export function QueryInput({ onSubmit, disabled }: QueryInputProps) {
    const [value, setValue] = useState("");

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
        <div className="space-y-3">
            <textarea
                value={value}
                onChange={(event) => setValue(event.target.value)}
                onKeyDown={handleKeyDown}
                maxLength={MAX_CHARS}
                placeholder="Ask your medical or legal question..."
                className="w-full resize-none rounded-lg border border-slate-700 bg-slate-900 p-4 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition"
                rows={5}
            />
            <div className="flex items-center justify-between">
                <span className="text-xs text-slate-500">{value.length} / {MAX_CHARS}</span>
                <button
                    onClick={handleSubmit}
                    disabled={disabled || !value.trim()}
                    className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-xs font-medium text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-40"
                >
                    <Send className="h-3.5 w-3.5" />
                    Send
                </button>
            </div>
        </div>
    );
}
}
