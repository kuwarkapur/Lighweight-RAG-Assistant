import re

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.I),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|system)\s+", re.I),
    re.compile(r"you\s+are\s+now\s+", re.I),
    re.compile(r"new\s+instructions?\s*:", re.I),
    re.compile(r"system\s*:\s*", re.I),
    re.compile(r"<\s*/?\s*system\s*>", re.I),
    re.compile(r"jailbreak", re.I),
    re.compile(r"do\s+not\s+follow\s+(the\s+)?(rules|policy|guidelines)", re.I),
]

BLOCK_MESSAGE = (
    "I cannot process this request because it appears to contain instructions "
    "that conflict with my safety guidelines. Please rephrase your question."
)


def detect_prompt_injection(text: str) -> tuple[bool, str | None]:
    for pattern in INJECTION_PATTERNS:
        if pattern.search(text):
            return True, BLOCK_MESSAGE
    return False, None
