# app/tools/response_scorer.py
import re
from typing import Dict, List
from collections import Counter

def check_complete_sentences(answer: str) -> float:
    """
    Check if response has complete sentences (ends with . ! ?)
    """
    sentences = re.split(r'[.!?]+', answer.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 3]
    
    if not sentences:
        return 0.0
    
    # Check for capital letters at start
    capital_starts = sum(1 for s in sentences if s[0].isupper())
    
    # Penalty for very short responses
    avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
    length_score = min(avg_length / 10, 1.0)
    
    return (capital_starts / len(sentences)) * 0.7 + length_score * 0.3


def check_question_keywords(answer: str, question: str) -> float:
    """
    Check if answer contains relevant keywords from question
    """
    # Extract meaningful words (not stopwords)
    stopwords = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for'}
    
    question_words = set(re.findall(r'\b\w+\b', question.lower()))
    question_words = {w for w in question_words if w not in stopwords and len(w) > 3}
    
    answer_words = set(re.findall(r'\b\w+\b', answer.lower()))
    
    if not question_words:
        return 0.5
    
    overlap = len(question_words & answer_words)
    relevance = overlap / len(question_words)
    
    return min(relevance, 1.0)


def check_logical_flow(answer: str) -> float:
    """
    Check if answer has logical flow (connectors, transitions)
    """
    connectors = [
        'however', 'therefore', 'moreover', 'furthermore', 'additionally',
        'consequently', 'thus', 'hence', 'for example', 'such as',
        'in fact', 'indeed', 'specifically', 'namely', 'first', 'second',
        'finally', 'in conclusion', 'to summarize', 'in other words'
    ]
    
    answer_lower = answer.lower()
    found_connectors = sum(1 for c in connectors if c in answer_lower)
    
    # Check for numbered/bulleted lists
    has_structure = bool(re.search(r'(\n\d+\.|\n-|\n\*)', answer))
    
    # Check for paragraphs
    paragraphs = len(answer.split('\n\n'))
    
    connector_score = min(found_connectors / 5, 1.0) * 0.4
    structure_score = 0.3 if has_structure else 0
    paragraph_score = min(paragraphs / 3, 1.0) * 0.3
    
    return connector_score + structure_score + paragraph_score


def verify_claims(answer: str) -> float:
    """
    Basic factuality check - detect uncertain/vague language
    """
    uncertain_phrases = [
        'i think', 'probably', 'maybe', 'perhaps', 'possibly',
        'might be', 'could be', 'seems like', 'appears to',
        'i guess', 'i believe', 'not sure', "i don't know"
    ]
    
    answer_lower = answer.lower()
    uncertainty_count = sum(1 for phrase in uncertain_phrases if phrase in answer_lower)
    
    # Penalty for too much uncertainty
    uncertainty_penalty = min(uncertainty_count * 0.15, 0.6)
    
    # Bonus for citations
    has_citations = bool(re.search(r'(according to|research shows|studies indicate)', answer_lower))
    citation_bonus = 0.2 if has_citations else 0
    
    # Bonus for specific numbers/dates
    has_specifics = bool(re.search(r'\d+%|\d+ (years?|months?|days?)|in \d{4}', answer))
    specific_bonus = 0.1 if has_specifics else 0
    
    base_score = 1.0 - uncertainty_penalty + citation_bonus + specific_bonus
    
    return max(min(base_score, 1.0), 0.0)


def detect_quality_issues(answer: str, question: str) -> List[str]:
    """
    Detect specific quality issues
    """
    issues = []
    
    # Too short
    if len(answer.split()) < 10:
        issues.append("Response too brief")
    
    # No punctuation
    if not re.search(r'[.!?]', answer):
        issues.append("Missing punctuation")
    
    # Repetitive
    words = answer.lower().split()
    word_counts = Counter(words)
    most_common = word_counts.most_common(3)
    if most_common and most_common[0][1] > len(words) * 0.2:
        issues.append(f"Repetitive word: '{most_common[0][0]}'")
    
    # Generic response
    generic_phrases = [
        "i cannot", "i don't have", "as an ai", "i apologize",
        "i'm not able", "i cannot provide", "beyond my capabilities"
    ]
    if any(phrase in answer.lower() for phrase in generic_phrases):
        issues.append("Generic AI refusal detected")
    
    # Off-topic
    if check_question_keywords(answer, question) < 0.2:
        issues.append("May be off-topic")
    
    return issues


def score_response(answer: str, question: str) -> Dict:
    """
    Main scoring function
    """
    scores = {
        'completeness': check_complete_sentences(answer),
        'relevance': check_question_keywords(answer, question),
        'coherence': check_logical_flow(answer),
        'factuality': verify_claims(answer)
    }
    
    overall = sum(scores.values()) / len(scores)
    
    issues = detect_quality_issues(answer, question)
    
    # Determine quality level
    if overall >= 0.75:
        quality = "EXCELLENT"
    elif overall >= 0.6:
        quality = "GOOD"
    elif overall >= 0.4:
        quality = "FAIR"
    else:
        quality = "POOR"
    
    return {
        'overall_score': round(overall, 2),
        'quality_level': quality,
        'component_scores': {k: round(v, 2) for k, v in scores.items()},
        'issues': issues,
        'should_regenerate': overall < 0.4 or len(issues) >= 3
    }


def format_score_report(score_data: Dict) -> str:
    """
    Format scoring results for terminal output
    """
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║            RESPONSE QUALITY REPORT                           ║
╠══════════════════════════════════════════════════════════════╣
║ Overall Score: {score_data['overall_score']:.2f} | Quality: {score_data['quality_level']:<10} ║
╠══════════════════════════════════════════════════════════════╣
║ Component Scores:                                            ║
"""
    
    for component, score in score_data['component_scores'].items():
        bar = '█' * int(score * 20)
        report += f"║  {component.capitalize():<15} {score:.2f} {bar:<20}║\n"
    
    if score_data['issues']:
        report += "╠══════════════════════════════════════════════════════════════╣\n"
        report += "║ Issues Detected:                                             ║\n"
        for issue in score_data['issues']:
            report += f"║  • {issue:<56}║\n"
    
    report += "╚══════════════════════════════════════════════════════════════╝"
    
    return report