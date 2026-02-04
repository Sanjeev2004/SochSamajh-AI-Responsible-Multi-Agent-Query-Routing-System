import { Dot } from "lucide-react";
import { Domain, RiskLevel } from "../types";

interface SafetyBadgeProps {
    label: string;
    tone: "neutral" | "warning" | "danger" | "success";
}

function toneClasses(tone: SafetyBadgeProps["tone"]) {
    switch (tone) {
        case "danger":
            return "border-rose-500/30 bg-rose-500/10 text-rose-300";
        case "warning":
            return "border-amber-500/30 bg-amber-500/10 text-amber-300";
        case "success":
            return "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";
        default:
            return "border-slate-600/30 bg-slate-600/10 text-slate-400";
    }
}

function toneColor(tone: SafetyBadgeProps["tone"]) {
    switch (tone) {
        case "danger":
            return "text-rose-400";
        case "warning":
            return "text-amber-400";
        case "success":
            return "text-emerald-400";
        default:
            return "text-slate-500";
    }
}

export function SafetyBadge({ label, tone }: SafetyBadgeProps) {
    return (
        <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-medium ${toneClasses(tone)}`}>
            <Dot className={`h-1.5 w-1.5 ${toneColor(tone)}`} fill="currentColor" />
            {label}
        </span>
    );
}

export function domainToTone(domain: Domain) {
    if (domain === "medical" || domain === "legal") return "warning";
    if (domain === "general") return "success";
    return "neutral";
}

export function riskToTone(risk: RiskLevel) {
    if (risk === "high") return "danger";
    if (risk === "medium") return "warning";
    return "success";
}
