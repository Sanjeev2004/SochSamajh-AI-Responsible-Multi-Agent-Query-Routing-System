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
                    <h2 className="mt-2 font-display text-3xl font-semibold tracking-tight text-stone-100">
                        Describe your situation.
                    </h2>
                </div>
                <div className="rounded-md border border-border bg-surface px-3 py-1.5 text-[10px] uppercase tracking-widest text-stone-500">
                    Ctrl/Cmd + Enter to submit
                </div>
            </div>

            {/* ── Step 1: Document Upload (separate from query) ── */}
            <div className="rounded-2xl border border-border bg-surface p-5 transition-all">
                <div className="mb-4 flex items-center gap-2 text-[11px] font-medium uppercase tracking-widest text-stone-400">
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
                            className="group inline-flex items-center justify-center gap-2 rounded-lg border border-border border-dashed bg-deep px-5 py-2.5 text-sm font-medium text-stone-300 transition-all hover:bg-surface-hover hover:text-stone-100"
                        >
                            <Paperclip className="h-4 w-4 transition-transform group-hover:scale-110" />
                            Upload PDF or TXT
                        </button>
                        <p className="text-xs text-stone-500">Upload medical reports or legal contracts for deep context.</p>
                    </div>
                )}

                {uploadStatus === "uploading" && (
                    <div className="flex items-center gap-3 rounded-lg border border-border bg-deep px-4 py-3">
                        <Loader2 className="h-4 w-4 animate-spin text-stone-400" />
                        <div>
                            <p className="text-sm font-medium text-stone-200">Parsing {uploadedFileName}…</p>
                            <p className="text-xs text-stone-500">Extracting text from your document.</p>
                        </div>
                    </div>
                )}

                {uploadStatus === "success" && uploadedContext && (
                    <div className="space-y-3">
                        <div className="flex items-center justify-between rounded-lg border border-border bg-deep px-4 py-3">
                            <div className="flex items-center gap-3">
                                <CheckCircle2 className="h-4 w-4 text-stone-400" />
                                <div>
                                    <p className="text-sm font-medium text-stone-200">
                                        📎 {uploadedFileName}
                                    </p>
                                    <p className="text-xs text-stone-500">
                                        {uploadedContext.length.toLocaleString()} characters extracted
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={handleRemoveDocument}
                                className="rounded-md p-1.5 text-stone-500 transition hover:bg-surface-hover hover:text-stone-200"
                                title="Remove document"
                            >
                                <X className="h-3.5 w-3.5" />
                            </button>
                        </div>
                        <div className={`overflow-y-auto rounded-lg border border-border bg-deep p-3 transition-all ${previewExpanded ? "max-h-64" : "max-h-32"}`}>
                            <p className="text-[10px] font-medium uppercase tracking-widest text-stone-500 mb-2">Preview</p>
                            <p className="text-xs leading-5 text-stone-400 whitespace-pre-wrap break-words">
                                {previewExpanded ? uploadedContext : uploadedContext.slice(0, 1500)}
                                {uploadedContext.length > 1500 && !previewExpanded && (
                                    <span className="text-stone-600"> …({(uploadedContext.length - 1500).toLocaleString()} more characters)</span>
                                )}
                            </p>
                            {uploadedContext.length > 1500 && (
                                <button
                                    onClick={() => setPreviewExpanded(prev => !prev)}
                                    className="mt-2 text-[11px] font-medium text-stone-300 hover:text-stone-100 transition"
                                >
                                    {previewExpanded ? "Show less" : `Show full text (${uploadedContext.length.toLocaleString()} chars)`}
                                </button>
                            )}
                        </div>
                    </div>
                )}

                {uploadStatus === "error" && (
                    <div className="flex items-center justify-between rounded-lg border border-rose-500/20 bg-rose-500/5 px-4 py-3">
                        <div className="flex items-center gap-3">
                            <AlertCircle className="h-4 w-4 text-rose-400" />
                            <div>
                                <p className="text-sm font-medium text-rose-200">Upload failed</p>
                                <p className="text-xs text-rose-300/80">{uploadError}</p>
                            </div>
                        </div>
                        <button
                            onClick={handleRemoveDocument}
                            className="rounded-md p-1.5 text-stone-500 transition hover:bg-surface-hover hover:text-stone-200"
                            title="Dismiss"
                        >
                            <X className="h-3.5 w-3.5" />
                        </button>
                    </div>
                )}
            </div>

            {/* ── Step 2: Query Input ── */}
            <div
                className={`relative overflow-hidden rounded-2xl border transition-all duration-300 sm:p-6 p-4 ${
                    focused
                        ? "border-stone-500 bg-surface shadow-subtle"
                        : "border-border bg-deep hover:border-stone-700"
                }`}
            >
                <div className="mb-4 flex items-center gap-2 text-[11px] font-medium uppercase tracking-widest text-stone-400">
                    <MessageSquareQuote className="h-3.5 w-3.5" />
                    Medical or legal question
                    {uploadedContext && (
                        <span className="ml-2 rounded-md bg-surface-hover px-2 py-0.5 text-[10px] text-stone-300">
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
                    className="min-h-[160px] w-full resize-none bg-transparent text-[15px] leading-7 text-stone-200 placeholder:text-stone-600 focus:outline-none"
                    rows={6}
                />

                <div className="mt-4 flex flex-col gap-4 border-t border-border pt-4 sm:flex-row sm:items-end sm:justify-between">
                    <div className="space-y-2">
                        <div className="flex items-center gap-3 text-xs text-stone-500">
                            <span className={value.length > MAX_CHARS * 0.8 ? "text-amber-400" : ""}>
                                {value.length}/{MAX_CHARS}
                            </span>
                        </div>
                        <p className="max-w-xl text-[11px] leading-5 text-stone-600">Include symptoms, urgency, timeline, or location.</p>
                    </div>

                    <button
                        onClick={handleSubmit}
                        disabled={disabled || !value.trim()}
                        className={`group inline-flex items-center justify-center gap-2 rounded-lg px-6 py-2.5 text-sm font-medium transition-all duration-200 ${
                            disabled || !value.trim()
                                ? "cursor-not-allowed bg-surface text-stone-500"
                                : "bg-stone-100 text-stone-900 hover:bg-white active:scale-95"
                        }`}
                    >
                        <WandSparkles className="h-4 w-4" />
                        Analyze query
                        <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                    </button>
                </div>
            </div>

            <div className="space-y-4">
                <div className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-widest text-stone-500">
                    <WandSparkles className="h-3.5 w-3.5" />
                    Try a prompt
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                    {QUICK_PROMPTS.map((prompt) => (
                        <button
                            key={prompt}
                            onClick={() => setValue(prompt)}
                            className="rounded-xl border border-border bg-surface p-4 text-left text-sm leading-6 text-stone-400 transition hover:bg-surface-hover hover:border-stone-700 hover:text-stone-200"
                        >
                            {prompt}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
