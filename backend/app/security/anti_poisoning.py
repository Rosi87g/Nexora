import re
from typing import List

BANNED_PATTERNS = [
    r"ignore\s*(all\s*)?previous\s*instructions",
    r"you\s*are\s*now\s*(a|an)",
    r"system\s*prompt",
    r"jailbreak",
    r"dan\s*mode",
    r"role\s*play\s*as",
    r"pretend\s*to\s*be",
    r"bypass\s*safety",
    r"act\s*as\s*an?\s*ai\s*without\s*restrictions",
    r"do\s*anything\s*now",
    r"never\s*refuse",
]

SAFE_KEYWORDS = [
    "react", "javascript", "angular", "vue", "framework", "library",
    "python", "java", "programming", "code", "developer", "web",
    "html", "css", "node", "express", "django", "flask"
]

def is_safe_answer(answer: str) -> bool:
    if not answer or len(answer.strip()) < 20:
        return False

    text = answer.lower()

    for pattern in BANNED_PATTERNS:
        if re.search(pattern, text):
            if any(safe in text for safe in SAFE_KEYWORDS):
                continue
            return False

    if any(phrase in text for phrase in [
        "i can't answer",
        "i'm not allowed",
        "against my guidelines",
        "not confident enough",
        "i'm sorry but i can't"
    ]):
        return False

    return True

def is_grounded_answer(answer: str, context: List[str]) -> bool:
    if not context or not answer:
        return False

    answer_words = set(re.findall(r'\w+', answer.lower()))
    total_overlap = 0

    for ctx in context:
        ctx_words = set(re.findall(r'\w+', ctx.lower()))
        overlap = len(answer_words.intersection(ctx_words))
        total_overlap += overlap
        if overlap >= 5:
            return True

    return total_overlap >= 8

def confidence_score(answer: str, context: List[str], grounded: bool) -> float:
    score = 0.4

    if grounded:
        score += 0.35

    word_count = len(answer.split())
    if word_count > 80:
        score += 0.1
    if word_count > 200:
        score += 0.05

    if context:
        score += min(0.1, len(context) * 0.03)

    if any(marker in answer for marker in ["•", "-", "*", "1.", "2.", "##", "###"]):
        score += 0.05

    return round(min(score, 0.99), 2)