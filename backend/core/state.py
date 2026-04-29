from __future__ import annotations

from typing import Literal, Optional, TypedDict
from pydantic import BaseModel, Field

Domain = Literal["medical", "legal", "general", "unknown"]
RiskLevel = Literal["low", "medium", "high"]


class ClassificationOutput(BaseModel):
    domain: Domain
    risk_level: RiskLevel
    needs_disclaimer: bool
    self_harm: bool
    illegal_request: bool
    reasoning: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    triggered_terms: list[str] = Field(default_factory=list)
    alternative_domains: dict[str, float] = Field(default_factory=dict)
    explanation: str = ""


class SourceCitation(BaseModel):
    title: str
    source: str
    domain: Domain | None = None
    snippet: str = ""
    score: float | None = None


class AgentResponse(BaseModel):
    content: str
    disclaimers: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    sources: list[SourceCitation] = Field(default_factory=list)


class SafetyFlags(BaseModel):
    self_harm: bool = False
    illegal_request: bool = False
    high_risk: bool = False


class RouterResponse(BaseModel):
    response: str
    classification: ClassificationOutput
    disclaimers: list[str]
    safety_flags: SafetyFlags
    request_id: str
    sources: list[SourceCitation] = Field(default_factory=list)
    pipeline_trace: list[str] = Field(default_factory=list)


class GraphState(TypedDict, total=False):
    query: str
    classification: ClassificationOutput
    response: AgentResponse
    safety_flags: SafetyFlags
    request_id: str
    error: Optional[str]
    pipeline_trace: list[str]
