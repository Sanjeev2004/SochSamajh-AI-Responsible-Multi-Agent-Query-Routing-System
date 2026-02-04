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


class AgentResponse(BaseModel):
    content: str
    disclaimers: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)


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


class GraphState(TypedDict, total=False):
    query: str
    classification: ClassificationOutput
    response: AgentResponse
    safety_flags: SafetyFlags
    request_id: str
    error: Optional[str]
