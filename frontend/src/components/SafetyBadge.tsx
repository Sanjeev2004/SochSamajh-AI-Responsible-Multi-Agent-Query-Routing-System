import { Dot } from "lucide-react";
import { Domain, RiskLevel } from "../types";

interface SafetyBadgeProps {
    label: string;
    tone: "neutral" | "warning" | "danger" | "success";
}

function toneClasses(tone: SafetyBadgeProps["tone"]) {
    switch (tone) {
        case "danger":
            return "border-rose-300/25 bg-rose-300/10 text-rose-100";
        case "warning":
            return "border-amber-300/25 bg-amber-300/10 text-amber-50";
        case "success":
            return "border-emerald-300/25 bg-emerald-300/10 text-emerald-50";
        default:
            return "border-white/10 bg-white/5 text-stone-200";
    }
}

function toneColor(tone: SafetyBadgeProps["tone"]) {
    switch (tone) {
        case "danger":
            return "text-rose-300";
        case "warning":
            return "text-amber-300";
        case "success":
            return "text-emerald-300";
        default:
            return "text-stone-400";
    }
}

export function SafetyBadge({ label, tone }: SafetyBadgeProps) {
    return (
        <span className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium uppercase tracking-[0.16em] ${toneClasses(tone)}`}>
            <Dot className={`h-3 w-3 ${toneColor(tone)}`} fill="currentColor" />
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
