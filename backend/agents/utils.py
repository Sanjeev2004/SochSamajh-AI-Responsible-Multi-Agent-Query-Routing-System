from __future__ import annotations

# 2000 chars ≈ ~350 words, sufficient for most real-world queries
# while preventing regex DoS on pathological inputs
MAX_QUERY_LENGTH = 2000


def _context_hint(context: str, max_chars: int = 260) -> str:
    """Extract brief one-line hint from RAG context."""
    if not context.strip():
        return ""
    first_line = next((line.strip() for line in context.splitlines() if line.strip()), "")
    if not first_line:
        return ""
    return f"\n\nRelevant retrieved note:\n- {first_line[:max_chars]}"
