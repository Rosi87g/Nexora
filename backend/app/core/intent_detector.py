# backend/app/core/intent_detector.py
import re
from datetime import datetime
from typing import Dict

def detect_query_intent(query: str) -> Dict[str, any]:
    """
    Determines if a query REQUIRES real-world grounding (like Claude's web search)
    Only triggers search for current/time-sensitive data that LLM can't know
    """
    q = query.lower().strip()
    q_clean = q.strip('"\'').strip('?!.,')
    
    # ═══════════════════════════════════════════════════════════
    # 1. GREETINGS (No search needed)
    # ═══════════════════════════════════════════════════════════
    greeting_patterns = [
        r'^(hi|hey|hello|sup|yo|howdy|greetings)[\s.!?]*$',
        r'^(good\s+)?(morning|afternoon|evening)[\s.!?]*$',
        r'^(whats up|what\'s up)[\s?!.]*$',
        r'^how (are you|are u|r u|is it going|you doing)[\s?!.]*$',
    ]
    
    for pattern in greeting_patterns:
        if re.match(pattern, q):
            return {
                "intent": "greeting",
                "needs_search": False,
                "reason": "greeting detected",
            }
    
    # ═══════════════════════════════════════════════════════════
    # 2. IDENTITY QUESTIONS (No search needed)
    # ═══════════════════════════════════════════════════════════
    identity_keywords = [
        "who are you", "what are you", "your name",
        "who made you", "who created you", "who built you",
        "tell me about yourself", "introduce yourself",
        "who is nexora", "what is nexora"
    ]
    
    if any(kw in q for kw in identity_keywords):
        return {
            "intent": "identity",
            "needs_search": False,
            "reason": "identity question",
        }
    
    # ═══════════════════════════════════════════════════════════
    # 3. PROCEDURAL/EDUCATIONAL (No search - LLM knows this)
    # ═══════════════════════════════════════════════════════════
    # Like Claude: "explain recursion" doesn't need web search
    procedural_indicators = [
        # Programming concepts/tutorials
        r'\b(explain|what is|define)\b.*(recursion|algorithm|function|variable|loop|array|object|class|inheritance|polymorphism)',
        r'\b(how does|how do)\b.*(recursion|sorting|searching|hashing|encryption)',
        r'\b(write|create|implement|code|program)\b',
        r'\b(debug|fix|solve)\b.*\b(code|error|bug)',
        r'\b(tutorial|guide|steps|learn)\b',
        
        # Math/Science concepts
        r'\b(calculate|solve|prove|derive|formula for)\b',
        r'\b(what is|explain)\b.*(pythagorean|fibonacci|factorial|prime)',
        
        # Creative writing
        r'\b(write|create|generate)\b.*(story|poem|joke|essay|article)',
    ]
    
    for pattern in procedural_indicators:
        if re.search(pattern, q):
            return {
                "intent": "procedural",
                "needs_search": False,
                "reason": "procedural/educational query (LLM can answer)",
            }
    
    # ═══════════════════════════════════════════════════════════
    # 4. TIME-SENSITIVE QUERIES (MANDATORY SEARCH)
    # ═══════════════════════════════════════════════════════════
    # Like Claude: "current president" MUST search
    time_indicators = [
        r'\b(current|today|now|latest|recent|this year)\b',
        r'\b(this week|this month)\b',
        r'\b(yesterday|tomorrow)\b',
        r'\b(is|are) .+ (still|currently|now)\b',
        r'\b(2024|2025|2026)\b',
        r'\bbreaking\b',
        r'\bjust (announced|released|happened)\b',
    ]
    
    for pattern in time_indicators:
        if re.search(pattern, q):
            search_terms = extract_clean_search_terms(q_clean)
            return {
                "intent": "time_sensitive",
                "needs_search": True,
                "reason": "time-sensitive query (current data required)",
                "search_terms": search_terms,
            }
    
    # ═══════════════════════════════════════════════════════════
    # 5. ENTITY STATUS QUERIES (MANDATORY SEARCH)
    # ═══════════════════════════════════════════════════════════
    # Like Claude: "Who is the CEO of X?" needs search
    entity_patterns = [
        r'\bwho is (the )?(current )?(president|ceo|leader|prime minister|governor|mayor|director|chairman)\b',
        r'\bwhat is (the )?(current |latest )?(price|cost|rate|value|worth)\b',
        r'\bwhere is .+ (now|currently|today)\b',
        r'\bwhen (did|was) .+ (released|launched|announced|elected|appointed)\b',
    ]
    
    for pattern in entity_patterns:
        if re.search(pattern, q):
            search_terms = extract_clean_search_terms(q_clean)
            return {
                "intent": "entity_status",
                "needs_search": True,
                "reason": "entity status query (mandatory grounding)",
                "search_terms": search_terms,
            }
    
    # ═══════════════════════════════════════════════════════════
    # 6. REAL-TIME DATA QUERIES (MANDATORY SEARCH)
    # ═══════════════════════════════════════════════════════════
    # Like Claude: weather, stocks, news need search
    realtime_keywords = [
        "weather", "temperature", "forecast",
        "stock price", "stock market", "exchange rate",
        "news", "breaking", "headlines",
        "score", "results", "standings", "game",
    ]
    
    if any(keyword in q for keyword in realtime_keywords):
        search_terms = extract_clean_search_terms(q_clean)
        return {
            "intent": "realtime_data",
            "needs_search": True,
            "reason": "real-time data query",
            "search_terms": search_terms,
        }
    
    # ═══════════════════════════════════════════════════════════
    # 7. SPECIFIC PERSON/COMPANY QUERIES (Search for verification)
    # ═══════════════════════════════════════════════════════════
    # Like Claude: "Tell me about Elon Musk" should verify current info
    specific_entity_patterns = [
        r'\b(tell me about|who is|what is)\b.*\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # "Tell me about John Doe"
        r'\b(google|microsoft|apple|amazon|tesla|meta|openai|anthropic)\b',  # Major companies
    ]
    
    for pattern in specific_entity_patterns:
        if re.search(pattern, q):
            search_terms = extract_clean_search_terms(q_clean)
            return {
                "intent": "entity_info",
                "needs_search": True,
                "reason": "specific entity query (verify current info)",
                "search_terms": search_terms,
            }
    
    # ═══════════════════════════════════════════════════════════
    # 8. DEFAULT: CONVERSATIONAL (No search - LLM knowledge)
    # ═══════════════════════════════════════════════════════════
    # Like Claude: Trust LLM's training for general knowledge
    return {
        "intent": "conversational",
        "needs_search": False,
        "reason": "general knowledge (LLM can answer)",
    }


def extract_clean_search_terms(query: str) -> str:
    """
    Extract clean search terms optimized for Google (like Claude does)
    
    Examples:
    "Who is the current US president?" → "current US president 2026"
    "What's the latest Python version?" → "latest Python version 2026"
    """
    q = query.lower().strip()
    
    # Remove quotes and punctuation
    q = q.strip('"\'').strip('?!.,;:')
    
    # Remove question words at start
    q = re.sub(r'^(who is|what is|when is|where is|which is|how is)\s+', '', q)
    q = re.sub(r'^(who\'s|what\'s|when\'s|where\'s|how\'s)\s+', '', q)
    q = re.sub(r'^(tell me about|explain|describe|define)\s+', '', q)
    
    # Remove common filler words
    filler = r'\b(the|a|an|of|in|on|at|to|for|with|by|from|about)\b'
    q = re.sub(filler, ' ', q)
    
    # Collapse multiple spaces
    q = re.sub(r'\s+', ' ', q).strip()
    
    # Add current year for time-sensitive queries (like Claude does)
    current_year = datetime.now().year
    
    time_sensitive_keywords = [
        'current', 'latest', 'now', 'today', 'recent',
        'president', 'ceo', 'leader', 'minister',
        'price', 'cost', 'rate', 'worth', 'version'
    ]
    
    if any(kw in q for kw in time_sensitive_keywords):
        if str(current_year) not in q and not re.search(r'\b20\d{2}\b', q):
            q = f"{q} {current_year}"
    
    return q if len(q) >= 5 else query