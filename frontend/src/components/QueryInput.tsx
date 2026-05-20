import { useRef, useState } from "react";
import { ArrowUpRight, MessageSquareQuote, WandSparkles, Paperclip, X, FileText, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { uploadDocument } from "../hooks/useApi";

interface QueryInputProps {
    onSubmit: (query: string, userContext: string | null, fileName: string | null) => void;
    disabled?: boolean;
}

const MAX_CHARS = 2000;
const QUICK_PROMPTS = [
    "I have chest pain since this morning. What warning signs mean I should get urgent care?",
    "My landlord is refusing to return my deposit after I moved out. What documents matter most?"
];

type UploadStatus = "idle" | "uploading" | "success" | "error";

export function QueryInput({ onSubmit, disabled }: QueryInputProps) {
    const [value, setValue] = useState("");
    const [focused, setFocused] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Document upload state (two-step flow)
    const [uploadStatus, setUploadStatus] = useState<UploadStatus>("idle");
    const [uploadedContext, setUploadedContext] = useState<string | null>(null);
    const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
    const [uploadError, setUploadError] = useState<string | null>(null);

    function handleSubmit() {
        if (!value.trim()) return;
        onSubmit(value.trim(), uploadedContext, uploadedFileName);
        setValue("");
    }

    async function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
        if (!event.target.files || !event.target.files[0]) return;
        const file = event.target.files[0];

        // Reset previous state
        setUploadStatus("uploading");
        setUploadError(null);
        setUploadedContext(null);
        setUploadedFileName(file.name);

        try {
            const extractedText = await uploadDocument(file);
            setUploadedContext(extractedText);
            setUploadStatus("success");
        } catch (err: any) {
            const detail = err.response?.data?.detail || "Failed to parse the document. Please try a different file.";
            setUploadError(detail);
            setUploadStatus("error");
            setUploadedFileName(null);
        }

        // Reset the file input so the same file can be re-selected
        if (fileInputRef.current) fileInputRef.current.value = "";
    }

    function handleRemoveDocument() {
        setUploadStatus("idle");
        setUploadedContext(null);
        setUploadedFileName(null);
        setUploadError(null);
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

            {/* ── Step 1: Document Upload (separate from query) ── */}
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-stone-400">
                    <FileText className="h-3.5 w-3.5 text-cyan-300" />
                    Document context (optional)
                </div>

                {uploadStatus === "idle" && (
                    <div className="flex items-center gap-3">
                        <input
                            type="file"
                            ref={fileInputRef}
                            onChange={handleFileChange}
                            accept=".txt,.pdf"
                            className="hidden"
                        />
                        <button
                            onClick={() => fileInputRef.current?.click()}
                            className="inline-flex items-center gap-2 rounded-full border border-dashed border-white/20 bg-white/5 px-4 py-2.5 text-xs text-stone-300 transition hover:border-cyan-300/40 hover:bg-cyan-300/10 hover:text-cyan-100"
                        >
                            <Paperclip className="h-3.5 w-3.5" />
                            Upload a PDF or TXT for context
                        </button>
                        <p className="text-[11px] text-stone-500">Upload first, then ask your question below.</p>
                    </div>
                )}

                {uploadStatus === "uploading" && (
                    <div className="flex items-center gap-3 rounded-xl border border-cyan-300/20 bg-cyan-300/10 px-4 py-3">
                        <Loader2 className="h-4 w-4 animate-spin text-cyan-300" />
                        <div>
                            <p className="text-sm font-medium text-cyan-50">Parsing {uploadedFileName}…</p>
                            <p className="text-xs text-cyan-100/60">Extracting text from your document.</p>
                        </div>
                    </div>
                )}

                {uploadStatus === "success" && uploadedContext && (
                    <div className="space-y-3">
                        <div className="flex items-center justify-between rounded-xl border border-emerald-300/25 bg-emerald-300/10 px-4 py-3">
                            <div className="flex items-center gap-3">
                                <CheckCircle2 className="h-4 w-4 text-emerald-300" />
                                <div>
                                    <p className="text-sm font-medium text-emerald-50">
                                        📎 {uploadedFileName}
                                    </p>
                                    <p className="text-xs text-emerald-100/60">
                                        {uploadedContext.length.toLocaleString()} characters extracted
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={handleRemoveDocument}
                                className="rounded-full p-1.5 text-stone-400 transition hover:bg-white/10 hover:text-white"
                                title="Remove document"
                            >
                                <X className="h-3.5 w-3.5" />
                            </button>
                        </div>
                        <div className="max-h-32 overflow-y-auto rounded-xl border border-white/10 bg-black/20 p-3">
                            <p className="text-[11px] uppercase tracking-[0.15em] text-stone-500 mb-1">Preview</p>
                            <p className="text-xs leading-5 text-stone-300 whitespace-pre-wrap">
                                {uploadedContext.slice(0, 500)}
                                {uploadedContext.length > 500 && (
                                    <span className="text-stone-500"> …({uploadedContext.length - 500} more characters)</span>
                                )}
                            </p>
                        </div>
                    </div>
                )}

                {uploadStatus === "error" && (
                    <div className="flex items-center justify-between rounded-xl border border-rose-300/25 bg-rose-300/10 px-4 py-3">
                        <div className="flex items-center gap-3">
                            <AlertCircle className="h-4 w-4 text-rose-300" />
                            <div>
                                <p className="text-sm font-medium text-rose-50">Upload failed</p>
                                <p className="text-xs text-rose-100/70">{uploadError}</p>
                            </div>
                        </div>
                        <button
                            onClick={handleRemoveDocument}
                            className="rounded-full p-1.5 text-stone-400 transition hover:bg-white/10 hover:text-white"
                            title="Dismiss"
                        >
                            <X className="h-3.5 w-3.5" />
                        </button>
                    </div>
                )}
            </div>

            {/* ── Step 2: Query Input ── */}
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
                    {uploadedContext && (
                        <span className="ml-2 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-2 py-0.5 text-[10px] text-emerald-200">
                            + document context loaded
                        </span>
                    )}
                </div>
                <textarea
                    value={value}
                    onChange={(event) => setValue(event.target.value)}
                    onKeyDown={handleKeyDown}
                    onFocus={() => setFocused(true)}
                    onBlur={() => setFocused(false)}
                    maxLength={MAX_CHARS}
                    placeholder={
                        uploadedContext
                            ? "Now ask your question about the uploaded document…"
                            : "Example: My father has a very high fever and confusion since last night. What signs suggest this needs urgent medical help?"
                    }
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
