import { useState } from "react";
import { ArrowUpRight, MessageSquareQuote, WandSparkles } from "lucide-react";

interface QueryInputProps {
    onSubmit: (query: string) => void;
    disabled?: boolean;
}

const MAX_CHARS = 2000;
const QUICK_PROMPTS = [
    "I have chest pain since this morning. What warning signs mean I should get urgent care?",
    "My landlord is refusing to return my deposit after I moved out. What documents matter most?"
];

export function QueryInput({ onSubmit, disabled }: QueryInputProps) {
    const [value, setValue] = useState("");
    const [focused, setFocused] = useState(false);

    function handleSubmit() {
        if (!value.trim()) return;
        onSubmit(value.trim());
        setValue("");
    }

    function handleKeyDown(event: React.KeyboardEvent) {
        if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
            handleSubmit();
        }
    }

    return (
        <div className="space-y-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                <div>
                    <h2 className="mt-2 font-['Iowan_Old_Style','Palatino_Linotype','Book_Antiqua',serif] text-3xl text-stone-50">
                        Describe the situation in plain language.
                    </h2>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-xs leading-5 text-stone-300">
                    Ctrl/Cmd + Enter to submit
                </div>
            </div>

            <div
                className={`rounded-[1.75rem] border p-4 transition duration-300 sm:p-5 ${
                    focused
                        ? "border-teal-400/35 bg-teal-400/10 shadow-[0_0_0_1px_rgba(94,234,212,0.18)]"
                        : "border-white/10 bg-black/15"
                }`}
            >
                <div className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-stone-400">
                    <MessageSquareQuote className="h-3.5 w-3.5 text-teal-300" />
                    Medical or legal question
                </div>
                <textarea
                    value={value}
                    onChange={(event) => setValue(event.target.value)}
                    onKeyDown={handleKeyDown}
                    onFocus={() => setFocused(true)}
                    onBlur={() => setFocused(false)}
                    maxLength={MAX_CHARS}
                    placeholder="Example: My father has a very high fever and confusion since last night. What signs suggest this needs urgent medical help?"
                    className="min-h-[190px] w-full resize-none bg-transparent text-base leading-7 text-stone-100 placeholder:text-stone-500 focus:outline-none"
                    rows={6}
                />

                <div className="mt-4 flex flex-col gap-4 border-t border-white/10 pt-4 sm:flex-row sm:items-end sm:justify-between">
                    <div className="space-y-2">
                        <div className="flex items-center gap-3 text-xs text-stone-400">
                            <span className={value.length > MAX_CHARS * 0.8 ? "text-amber-300" : ""}>
                                {value.length}/{MAX_CHARS}
                            </span>
                            <div className="h-1.5 w-28 overflow-hidden rounded-full bg-white/10">
                                <div
                                    className="h-full rounded-full bg-gradient-to-r from-teal-300 via-cyan-300 to-amber-300 transition-all duration-300"
                                    style={{ width: `${(value.length / MAX_CHARS) * 100}%` }}
                                />
                            </div>
                        </div>
                        <p className="max-w-xl text-xs leading-5 text-stone-500">Include symptoms, urgency, timeline, or location.</p>
                    </div>

                    <button
                        onClick={handleSubmit}
                        disabled={disabled || !value.trim()}
                        className={`inline-flex items-center justify-center gap-2 rounded-full px-5 py-3 text-sm font-semibold transition ${
                            disabled || !value.trim()
                                ? "cursor-not-allowed border border-white/10 bg-white/5 text-stone-500"
                                : "border border-teal-300/40 bg-gradient-to-r from-teal-300 to-amber-300 text-slate-950 shadow-lg shadow-teal-500/20 hover:-translate-y-0.5"
                        }`}
                    >
                        <WandSparkles className="h-4 w-4" />
                        Analyze query
                        <ArrowUpRight className="h-4 w-4" />
                    </button>
                </div>
            </div>

            <div className="space-y-3">
                <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-stone-400">
                    <WandSparkles className="h-3.5 w-3.5 text-amber-300" />
                    Try a prompt
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                    {QUICK_PROMPTS.map((prompt) => (
                        <button
                            key={prompt}
                            onClick={() => setValue(prompt)}
                            className="rounded-2xl border border-white/10 bg-white/5 p-4 text-left text-sm leading-6 text-stone-300 transition hover:border-amber-300/30 hover:bg-amber-300/10 hover:text-stone-100"
                        >
                            {prompt}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
