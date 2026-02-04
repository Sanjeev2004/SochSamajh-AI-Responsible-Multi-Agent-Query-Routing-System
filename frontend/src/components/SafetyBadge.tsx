import { ShieldAlert, ShieldCheck, ShieldX } from "lucide-react";
import { Domain, RiskLevel } from "../types";

interface SafetyBadgeProps {
    label: string;
    tone: "neutral" | "warning" | "danger" | "success";
}

function toneClasses(tone: SafetyBadgeProps["tone"]) {
    switch (tone) {
        case "danger":
            return "bg-rose-500/20 text-rose-200 border-rose-500/40";
        case "warning":
            return "bg-amber-500/20 text-amber-200 border-amber-500/40";
        case "success":
            return "bg-emerald-500/20 text-emerald-200 border-emerald-500/40";
        default:
            return "bg-slate-500/20 text-slate-200 border-slate-500/40";
    }
}

export function SafetyBadge({ label, tone }: SafetyBadgeProps) {
    const Icon = tone === "danger" ? ShieldX : tone === "warning" ? ShieldAlert : ShieldCheck;

    return (
        <span className={`inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-semibold ${toneClasses(tone)}`}>
            <Icon className="h-3.5 w-3.5" />
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
