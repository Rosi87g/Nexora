# app/core/answer_refiner.py - Enhanced & Grok-Compatible Version
import re
import html
from typing import List, Tuple, Dict

uploaded_files_memory: Dict[str, List[str]] = {}

def _clean_text(s: str) -> str:
    if not s:
        return ""

    s = html.unescape(s)
    s = re.sub(r'https?://\S+|www\.\S+', '', s)
    s = re.sub(r'\[[^\]]*\]', '', s)
    s = re.sub(r'\(\d+\)', '', s)
    s = re.sub(r'\s{2,}', ' ', s)
    return s.strip()

def _split_paragraphs(text: str) -> List[str]:
    parts = [p.strip() for p in re.split(r'\n{1,}|\.\s+', text) if len(p.strip()) > 10]
    return parts

def _score_relevance(question: str, text: str) -> int:
    q = (question or "").lower()
    t = (text or "").lower()
    score = 0
    for token in set(re.findall(r'\w{3,}', q)):
        if token in t:
            score += 1
    score += min(2, len(t) // 200)
    return score

def _extract_definition(text: str, question: str) -> str:
    patterns = [
        r'is\s+(?:a|an|the)\s+([^.]+)',
        r'refers to\s+([^.]+)',
        r'defined as\s+([^.]+)',
        r'means\s+([^.]+)',
        r'describes\s+([^.]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            definition = match.group(1).strip()
            if 20 < len(definition) < 200:
                return definition.capitalize() + "."
    sentences = re.split(r'\.\s+', text)
    if sentences and len(sentences[0]) > 20:
        return sentences[0].strip()
    return text[:200].strip() + "..."

def _extract_key_facts(texts: List[str], max_facts: int = 5) -> List[str]:
    facts = []
    indicators = ['is', 'are', 'can', 'includes', 'causes', 'results in', 'consists of', 'contains', 'forms', 'produces', 'leads to']
    for text in texts:
        sentences = re.split(r'\.\s+|\n', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20 or len(sentence) > 200:
                continue
            if any(ind in sentence.lower() for ind in indicators):
                if not any(sentence.lower()[:50] in f.lower() for f in facts):
                    facts.append(sentence if sentence.endswith('.') else sentence + '.')
                    if len(facts) >= max_facts:
                        return facts
    return facts or ["Core details summarized above."]

def _extract_types_or_examples(texts: List[str], max_items: int = 4) -> List[str]:
    items = []
    keywords = ['types include', 'examples include', 'such as', 'including', 'categories', 'forms of', 'kinds of', 'varieties']
    for text in texts:
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                start_idx = text_lower.index(keyword)
                segment = text[start_idx:start_idx + 300]
                potential = re.split(r',|;|\n|•|and', segment)
                for item in potential:
                    item = re.sub(r'^(and|or|the|a|an)\s+', '', item.strip(), flags=re.IGNORECASE)
                    if 10 < len(item) < 100 and not any(item.lower() in i.lower() for i in items):
                        items.append(item.capitalize() + ".")
                        if len(items) >= max_items:
                            return items
    return items or ["Various forms, applications, and examples exist."]

def refine_answer_from_sources(
    question: str,
    sources: List[Tuple[str, str]],
    user_id: str = "guest",
) -> str:
    question = (question or "").strip()
    if not sources:
        return f"**{question}**\n\nI couldn't retrieve reliable sources for this topic at the moment."

    weights = {"llm": 5, "internal": 4, "vector": 4, "wikipedia": 3, "file": 3, "google": 2}
    cleaned_items = []

    for label, text in sources:
        if not text or len(text) < 30:
            continue
        t = _clean_text(text)
        for para in _split_paragraphs(t):
            score = _score_relevance(question, para) * weights.get(label, 1)
            cleaned_items.append({"text": para, "score": score})

    if not cleaned_items:
        return f"**{question}**\n\nLimited information available from sources."

    cleaned_items.sort(key=lambda x: x["score"], reverse=True)
    selected_texts = []
    seen = set()
    for item in cleaned_items[:10]:
        key = re.sub(r'\W+', ' ', item["text"].lower())[:150]
        if key not in seen:
            seen.add(key)
            selected_texts.append(item["text"])

    top_texts = selected_texts[:5]
    definition = _extract_definition(top_texts[0], question)
    key_facts = _extract_key_facts(top_texts)
    types_examples = _extract_types_or_examples(top_texts)
    additional = " ".join([s.strip() for s in selected_texts[1:3] if 30 < len(s) < 180][:2])

    def bullets(items: List[str]) -> str:
        return "\n".join(f"• {i}" for i in items) if items else "• Not specified in sources"

    return (
        f"**{question}**\n\n"
        f"**Definition:**\n{definition}\n\n"
        f"**Key Facts:**\n{bullets(key_facts)}\n\n"
        f"**Types / Examples:**\n{bullets(types_examples)}\n\n"
        f"**Additional Context:**\n{additional or 'This topic has broad applications across relevant fields.'}"
    )

def refine_answer(question: str, raw_answer: str, detail_level: str = "medium") -> str:
    if any(marker in raw_answer for marker in ["**Definition:**", "**Core Concept**", "**Concept Overview**"]):
        return raw_answer

    paragraphs = [p.strip() for p in raw_answer.split('\n\n') if len(p.strip()) > 20]
    if not paragraphs:
        return raw_answer

    definition = paragraphs[0]
    key_facts = []
    examples = []

    for para in paragraphs[1:]:
        sentences = re.split(r'\.\s+', para)
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 20:
                continue
            lower = sent.lower()
            if any(word in lower for word in ['example', 'such as', 'including', 'like', 'type', 'kind']):
                if len(examples) < 4:
                    examples.append(sent if sent.endswith('.') else sent + '.')
            else:
                if len(key_facts) < 5:
                    key_facts.append(sent if sent.endswith('.') else sent + '.')

    if not key_facts:
        key_facts = ["Main points covered in definition."]
    if not examples:
        examples = ["Multiple variations and use cases exist."]

    return (
        f"**{question}**\n\n"
        f"**Definition:**\n{definition}\n\n"
        f"**Key Facts:**\n" + "\n".join(f"• {f}" for f in key_facts) + "\n\n"
        f"**Types / Examples:**\n" + "\n".join(f"• {e}" for e in examples) + "\n\n"
        f"**Additional Context:**\n{paragraphs[-1] if len(paragraphs) > 1 else 'See above for core understanding.'}"
    )