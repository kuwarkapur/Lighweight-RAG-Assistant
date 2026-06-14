import re

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")


def mask_pii(text: str) -> str:
    text = EMAIL_PATTERN.sub("[EMAIL REDACTED]", text)
    text = PHONE_PATTERN.sub("[PHONE REDACTED]", text)
    return text
