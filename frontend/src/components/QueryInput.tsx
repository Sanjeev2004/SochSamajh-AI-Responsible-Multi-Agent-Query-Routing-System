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
    const [previewExpanded, setPreviewExpanded] = useState(false);

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
        setPreviewExpanded(false);
    }

    function handleKeyDown(event: React.KeyboardEvent) {
        if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
            handleSubmit();
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                <div>
                    <h2 className="mt-2 font-display text-4xl font-semibold tracking-tight text-white drop-shadow-sm">
                        Describe your situation.
                    </h2>
                </div>
                <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-[11px] uppercase tracking-widest text-stone-400 backdrop-blur-md">
                    Ctrl/Cmd + Enter to submit
                </div>
            </div>

            {/* ── Step 1: Document Upload (separate from query) ── */}
            <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.02] backdrop-blur-md p-5 transition-all duration-300 hover:bg-white/[0.04]">
                <div className="mb-4 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-violet-400">
                    <FileText className="h-3.5 w-3.5" />
                    Document context (optional)
                </div>

                {uploadStatus === "idle" && (
                    <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                        <input
                            type="file"
                            ref={fileInputRef}
                            onChange={handleFileChange}
                            accept=".txt,.pdf"
                            className="hidden"
                        />
                        <button
                            onClick={() => fileInputRef.current?.click()}
                            className="group inline-flex items-center justify-center gap-2 rounded-xl border border-dashed border-white/20 bg-white/5 px-5 py-3 text-sm font-medium text-stone-300 transition-all hover:border-violet-400/50 hover:bg-violet-400/10 hover:text-violet-100 hover:shadow-glow-violet"
                        >
                            <Paperclip className="h-4 w-4 transition-transform group-hover:scale-110" />
                            Upload PDF or TXT
                        </button>
                        <p className="text-xs text-stone-500">Upload medical reports or legal contracts for deep context.</p>
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
                        <div className={`overflow-y-auto rounded-xl border border-white/10 bg-black/20 p-3 transition-all ${previewExpanded ? "max-h-64" : "max-h-32"}`}>
                            <p className="text-[11px] uppercase tracking-[0.15em] text-stone-500 mb-1">Preview</p>
                            <p className="text-xs leading-5 text-stone-300 whitespace-pre-wrap break-words">
                                {previewExpanded ? uploadedContext : uploadedContext.slice(0, 1500)}
                                {uploadedContext.length > 1500 && !previewExpanded && (
                                    <span className="text-stone-500"> …({(uploadedContext.length - 1500).toLocaleString()} more characters)</span>
                                )}
                            </p>
                            {uploadedContext.length > 1500 && (
                                <button
                                    onClick={() => setPreviewExpanded(prev => !prev)}
                                    className="mt-2 text-[11px] text-teal-300 hover:text-teal-100 transition"
                                >
                                    {previewExpanded ? "Show less" : `Show full text (${uploadedContext.length.toLocaleString()} chars)`}
                                </button>
                            )}
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
                className={`relative overflow-hidden rounded-[2rem] border transition-all duration-500 sm:p-6 p-4 ${
                    focused
                        ? "border-teal-400/40 bg-teal-400/[0.03] shadow-[0_0_30px_-5px_rgba(45,212,191,0.15)]"
                        : "border-white/10 bg-white/[0.02] hover:bg-white/[0.03]"
                } backdrop-blur-xl`}
            >
                {/* Subtle animated gradient background when focused */}
                <div className={`absolute inset-0 -z-10 bg-gradient-to-br from-teal-400/5 via-violet-400/5 to-transparent transition-opacity duration-700 ${focused ? "opacity-100" : "opacity-0"}`} />

                <div className="mb-4 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-teal-400">
                    <MessageSquareQuote className="h-3.5 w-3.5" />
                    Medical or legal question
                    {uploadedContext && (
                        <span className="ml-2 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-2.5 py-0.5 text-[10px] text-emerald-300">
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
                        className={`group inline-flex items-center justify-center gap-2 rounded-xl px-6 py-3.5 font-display text-sm font-semibold tracking-wide transition-all duration-300 ${
                            disabled || !value.trim()
                                ? "cursor-not-allowed border border-white/10 bg-white/5 text-stone-500"
                                : "bg-gradient-to-r from-teal-400 to-violet-500 text-white shadow-lg shadow-teal-500/25 hover:-translate-y-1 hover:shadow-xl hover:shadow-violet-500/30 hover:brightness-110 active:scale-95"
                        }`}
                    >
                        <WandSparkles className={`h-4 w-4 ${disabled || !value.trim() ? "" : "animate-pulse"}`} />
                        Analyze query
                        <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                    </button>
                </div>
            </div>

            <div className="space-y-4">
                <div className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-stone-400">
                    <WandSparkles className="h-3.5 w-3.5 text-violet-400" />
                    Try a prompt
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                    {QUICK_PROMPTS.map((prompt) => (
                        <button
                            key={prompt}
                            onClick={() => setValue(prompt)}
                            className="rounded-xl border border-white/10 bg-white/[0.02] p-4 text-left text-sm leading-6 text-stone-300 backdrop-blur-sm transition-all duration-300 hover:-translate-y-1 hover:border-violet-400/40 hover:bg-violet-400/10 hover:text-white hover:shadow-lg hover:shadow-violet-500/10"
                        >
                            {prompt}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
