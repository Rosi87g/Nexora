import asyncio
import os
import requests
from typing import List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import time
import json
import psutil
import re
from datetime import datetime
import random
import aiohttp

from .prompts.general import NEXORA_SYSTEM_PROMPT
from .prompts.math import MATH_SYSTEM_PROMPT
from .prompts.coding import CODING_SYSTEM_PROMPT
from .prompts.greeting import GREETING_PROMPT
from .prompts.grounded import GROUNDED_SYSTEM_PROMPT

from app.internet.google_search import google_search
from app.internet.wikipedia_search import wiki_search
from app.tools.code_execution import safe_execute_code
from app.core.vector import (
    retrieve_context,
    retrieve_knowledge,
    get_sentence_transformer
)

from app.core.response_style import (
    get_response_style_config,
    adjust_model_options_for_style,
    detect_style_from_query,
    merge_style_with_base_prompt
)

from dotenv import load_dotenv
load_dotenv()

from app.core.intent_detector import detect_query_intent

get_sentence_transformer()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_TIMEOUT = 15.0
GEN_TIMEOUT = 600
STALL_TIMEOUT = 600
_executor = ThreadPoolExecutor(max_workers=4)

VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "true").lower() == "true"

CONVERSATION_HISTORY: Dict[str, List[Dict]] = {}

SAFE_IDENTITY = (
    "I'm Nexora 1.1, a private AI assistant designed to help with reasoning, "
    "coding, learning, research, and problem-solving. "
    "I focus on accuracy, clarity, and usefulness."
)


def add_to_history(user_id: str, role: str, content: str):
    if user_id not in CONVERSATION_HISTORY:
        CONVERSATION_HISTORY[user_id] = []
    CONVERSATION_HISTORY[user_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    })
    if len(CONVERSATION_HISTORY[user_id]) > 8:
        CONVERSATION_HISTORY[user_id] = CONVERSATION_HISTORY[user_id][-8:]


def get_history_messages(user_id: str) -> List[Dict]:
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in CONVERSATION_HISTORY.get(user_id, [])
    ]


LOG_COLORS = {
    'QUESTION': '\033[96m',
    'MODEL': '\033[95m',
    'PROGRESS': '\033[93m',
    'SUCCESS': '\033[92m',
    'ERROR': '\033[91m',
    'INFO': '\033[94m',
    'TOOL': '\033[93m',
    'RESET': '\033[0m'
}


def log(category: str, message: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    color = LOG_COLORS.get(category, LOG_COLORS['INFO'])
    reset = LOG_COLORS['RESET']
    category_padded = category.ljust(8)
    print(f"{color}[{timestamp}] [{category_padded}]{reset} {message}")


# ────────────────────────────────────────────────
# FIX 1A ── Aggressive & smarter web search trigger
# ────────────────────────────────────────────────
def should_search_web(question: str, force: bool = False) -> tuple[bool, str]:
    """
    Determine if web search is needed.
    AGGRESSIVE strategy - search by default for factual queries.
    """
    if force:
        return True, extract_search_query(question)

    q = question.lower().strip()

    # ✅ NEVER search for these (conversational/creative)
    never_search_patterns = [
        r'^(hi|hey|hello|sup|yo|howdy|greetings)\b',
        r'\b(joke|story|poem|song|creative|imagine|pretend)\b',
        r'^(what do you think|in your opinion|how do you feel)\b',
        r'^(help me (write|create|design|make))\b',
        r'\b(algorithm|function|class|loop|debug)\b.*\b(code|python|java|javascript)\b',
        r'\b(solve|calculate|prove|derive)\b.*\b(equation|integral|derivative|matrix)\b',
    ]
    
    for pattern in never_search_patterns:
        if re.search(pattern, q):
            return False, ""

    # ✅ ALWAYS search for these (current/factual)
    always_search_patterns = [
        r'\b(current|latest|recent|now|today|this (year|month|week|morning|afternoon|evening))\b',
        r'\b(202[4-6])\b',
        r'\b(price|cost|rate|salary|stock|market|exchange)\b',
        r'\b(news|breaking|update|announce|reported)\b',
        r'\b(who is (the )?(current|new|acting))\b',
        r'\b(what is the (current|latest|new))\b',
        r'\b(score|result|winner|won|lost|match)\b',
        r'\b(weather|temperature|forecast|climate)\b',
        r'\b(version|release|launched|updated|patch)\b',
        r'\b(election|president|minister|governor|ceo|chairman|director)\b',
    ]
    
    for pattern in always_search_patterns:
        if re.search(pattern, q):
            return True, question

    # ✅ SEARCH for factual "who/what/when/where" questions about named entities
    factual_entity_patterns = [
        r'\b(who is|what is|tell me about|explain|describe)\s+[A-Z]',
        r'\b(company|corporation|organization|startup|business)\b',
        r'\b(product|service|app|platform|tool|software)\b',
        r'\b(person|celebrity|politician|scientist|author|artist|ceo)\b',
    ]
    
    for pattern in factual_entity_patterns:
        if re.search(pattern, question):
            return True, question

    # ✅ DEFAULT: Don't search for pure conceptual/educational questions
    return False, ""


def extract_search_query(question: str) -> str:
    q_lower = question.lower()
    q_clean = re.sub(r'\b(what|who|when|where|why|how|is|are|was|were|the|a|an)\b', '', q_lower)
    q_clean = re.sub(r'\s+', ' ', q_clean).strip()
    if len(q_clean) < 5:
        return question
    return q_clean


def classify_factual_requirement(question: str) -> str:
    q = question.lower().strip()

    if any(k in q for k in [
        "version", "release", "released", "new version", "latest version",
        "current version", "which version", "v ", "v.", "build number"
    ]):
        return "version_info"

    if any(k in q for k in [
        "price", "cost", "rate", "salary", "fees", "how much", "worth",
        "current price", "today's price"
    ]):
        return "numeric_current"

    if any(k in q for k in [
        "who is", "current", "now", "ceo", "president", "leader", "minister",
        "head", "director", "manager", "governor", "chief"
    ]):
        return "current_role"

    if any(k in q for k in [
        "happening", "news", "recent", "today", "now", "current", "latest",
        "breaking", "this week", "this month", "2024", "2025", "2026"
    ]):
        return "current_event"

    return "general_fact"


# ────────────────────────────────────────────────
# FIX 1B ── Stronger context validation
# ────────────────────────────────────────────────
def context_satisfies_requirement(requirement: str, contexts: list[str]) -> bool:
    """
    Verify if retrieved contexts meet the factual requirement.
    """
    if not contexts:
        return False

    joined = " ".join(contexts).lower()
    
    if len(joined.strip()) < 50:
        return False

    if requirement == "version_info":
        version_indicators = [
            "version", "v.", "v1", "v2", "v3", "released", "release date", 
            "changelog", "build", "update", "patch", "stable", "beta",
            "latest", "current version", "new version"
        ]
        indicator_count = sum(1 for ind in version_indicators if ind in joined)
        has_version_number = bool(re.search(r'v\d+\.\d+|version \d+|\d+\.\d+\.\d+', joined))
        return indicator_count >= 2 or has_version_number

    if requirement == "numeric_current":
        return bool(re.search(r'\d+', joined))

    if requirement == "current_role":
        current_indicators = [
            "currently", "as of", "serving", "appointed", "incumbent",
            "present", "now", "since", "acting", "current", "today",
            "2024", "2025", "2026"
        ]
        return any(ind in joined for ind in current_indicators)

    if requirement == "current_event":
        time_indicators = [
            "today", "yesterday", "this week", "this month",
            "breaking", "reported", "announced", "just", "recently",
            "hours ago", "days ago", "2024", "2025", "2026",
            "latest", "current", "now"
        ]
        return any(ind in joined for ind in time_indicators)

    return len(joined.strip()) >= 50


# ────────────────────────────────────────────────
# FIX 1C ── New validation function
# ────────────────────────────────────────────────
def validate_search_results(search_results: list[str], query: str) -> bool:
    """
    Validate that search results actually contain relevant information.
    Prevents hallucination from empty or irrelevant results.
    """
    if not search_results:
        return False
    
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'who', 
                  'when', 'where', 'how', 'why', 'do', 'does', 'did', 'can', 'could',
                  'will', 'would', 'should', 'may', 'might', 'must'}
    
    query_terms = set(
        word.lower().strip('?.,!')
        for word in query.split()
        if word.lower() not in stop_words and len(word) > 2
    )
    
    combined = " ".join(search_results).lower()
    
    if not query_terms:
        return len(combined) > 100
    
    matches = sum(1 for term in query_terms if term in combined)
    match_ratio = matches / len(query_terms)
    
    return match_ratio >= 0.3


ELABORATE_KEYWORDS = [
    "elaborate", "detailed", "more", "explain thoroughly", "in depth",
    "comprehensive", "extensively", "detail", "expand", "deep dive",
    "complete", "full explanation", "thoroughly", "everything about",
    "all about", "tell me more", "give me more", "longer", "explain"
]

BRIEF_KEYWORDS = [
    "brief", "summary", "quickly", "short", "tldr", "concise",
    "simple", "simply", "just", "quick"
]


def is_greeting(question: str) -> bool:
    q_lower = question.lower().strip()
    q_clean = re.sub(r'[.!?,\s]+$', '', q_lower)

    simple_greetings = [
        "hi", "hey", "hello", "sup", "yo", "howdy", "greetings",
        "good morning", "good afternoon", "good evening",
        "morning", "afternoon", "evening",
        "hey there", "hi there", "hello there"
    ]

    if q_clean in simple_greetings:
        return True

    greeting_patterns = [
        r'^(hi+|hey+|hello+|yo+|sup+|howdy|greetings)[\s.!?]*$',
        r'^(good\s+)?(morning|afternoon|evening)[\s.!?]*$',
        r'^(whats up|what\'s up)[\s?!.]*$',
        r'^how (are you|are u|r u|is it going|you doing)[\s?!.]*$',
        r'^(hey|hi|hello)\s+(there|friend|mate|buddy)[\s.!?]*$',
    ]

    for pattern in greeting_patterns:
        if re.match(pattern, q_lower):
            return True

    identity_keywords = [
        "who are you", "who r you", "who're you",
        "what are you", "what r you",
        "what is your name", "whats your name", "what's your name",
        "who made you", "who created you", "who built you", "who developed you",
        "tell me about yourself", "about yourself", "introduce yourself",
        "who is nexora", "what is nexora"
    ]

    if any(keyword in q_lower for keyword in identity_keywords):
        return True

    return False


MATH_KEYWORDS = ["math", "equation", "calculate", "solve", "prove", "integral", "derivative", "matrix", "vector", "geometry", "algebra", "calculus", "sin", "cos", "tan", "log", "exp"]
CODING_KEYWORDS = ["code", "program", "algorithm", "function", "class", "loop", "array", "list", "subarray", "string", "python", "java", "c++", "implement", "write code", "debug"]


def is_math_question(question: str) -> bool:
    q_lower = question.lower()
    return any(kw in q_lower for kw in MATH_KEYWORDS) or any(sym in question for sym in ["=", "^", "√", "∫", "∑", "π", "θ"])


def is_coding_question(question: str) -> bool:
    q_lower = question.lower()
    return any(kw in q_lower for kw in CODING_KEYWORDS) or "def " in question or "class " in question or re.search(r'\b(arr|array|list|subarray|target)\b', q_lower)


MODEL_TIERS = {
    "minimal": ["gemma2:2b"],
    "fastest": ["qwen2.5:3b", "gemma3:4b", "phi3:mini"],
    "fast": ["qwen2.5:7b", "gemma2:9b"],
    "balanced": ["qwen2.5:14b"],
    "capable": ["qwen2.5:32b"]
}

ALL_MODELS = [m for tier in MODEL_TIERS.values() for m in tier]

_model_performance: Dict[str, List[float]] = {}
_model_failures: Dict[str, int] = {}
_current_model = None
_last_model_check = 0
_cached_available_models = []


def get_system_resources() -> Dict:
    try:
        return {
            "ram_total_gb": psutil.virtual_memory().total / (1024**3),
            "ram_available_gb": psutil.virtual_memory().available / (1024**3),
            "ram_percent": psutil.virtual_memory().percent,
            "cpu_count": psutil.cpu_count(logical=True),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
        }
    except:
        return {"ram_total_gb": 8, "ram_available_gb": 4, "ram_percent": 50, "cpu_count": 4, "cpu_percent": 50}


@lru_cache(maxsize=1)
def is_llm_available() -> bool:
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=OLLAMA_TIMEOUT)
        return r.status_code == 200
    except:
        return False


def get_available_models(force_refresh=False) -> List[str]:
    global _cached_available_models, _last_model_check
    now = time.time()
    if not force_refresh and _cached_available_models and (now - _last_model_check) < 300:
        return _cached_available_models
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=OLLAMA_TIMEOUT)
        r.raise_for_status()
        _cached_available_models = [m["name"] for m in r.json().get("models", [])]
        _last_model_check = now
        return _cached_available_models
    except:
        return _cached_available_models


def is_text_generation_model(model_name: str) -> bool:
    excluded_keywords = ['moondream', 'llava', 'bakllava', 'vision', 'clip', 'embedding', 'nomic-embed', 'mxbai-embed', 'all-minilm', 'codellama', 'starcoder', 'stable-diffusion']
    return not any(keyword in model_name.lower() for keyword in excluded_keywords)


def select_optimal_model(force_reselect=False, is_math_or_coding=False) -> Optional[str]:
    global _current_model
    available = get_available_models()
    if not available: return None
    text_models = [m for m in available if is_text_generation_model(m)]
    if not text_models: return None

    resources = get_system_resources()
    ram_gb = resources["ram_available_gb"]

    if is_math_or_coding:
        if "qwen2.5:14b" in text_models and ram_gb > 12.0:
            return "qwen2.5:14b"
        if "qwen2.5:7b" in text_models and ram_gb > 6.0:
            return "qwen2.5:7b"
        if "gemma3:4b" in text_models:
            return "gemma3:4b"
    else:
        if "gemma2:9b" in text_models and ram_gb > 8.0:
            return "gemma2:9b"
        if "qwen2.5:7b" in text_models and ram_gb > 4.0:
            return "qwen2.5:7b"

    if "gemma3:4b" in text_models:
        return "gemma3:4b"
    return text_models[0]


def record_performance(model: str, response_time: float, success: bool = True):
    if model not in _model_performance:
        _model_performance[model] = []
    if success:
        _model_performance[model].append(response_time)
        _model_failures[model] = max(0, _model_failures.get(model, 0) - 1)
    else:
        _model_failures[model] = _model_failures.get(model, 0) + 1
    if len(_model_performance[model]) > 10:
        _model_performance[model] = _model_performance[model][-10:]


async def generate_with_streaming_async(messages: List[Dict], model: str, options: Dict, contexts: List[str] = None):
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "keep_alive": "5m",
        "options": options,
    }
    try:
        timeout = aiohttp.ClientTimeout(total=GEN_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(f"{OLLAMA_HOST}/api/chat", json=payload) as response:
                response.raise_for_status()
                token_count = 0
                start_time = time.time()
                last_chunk_time = time.time()

                async for line in response.content:
                    if await asyncio.sleep(0) or True:
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk and chunk["message"]["role"] == "assistant":
                                content = chunk["message"].get("content", "")
                                if content:
                                    token_count += len(content.split())
                                    yield content
                                    last_chunk_time = time.time()

                                    if token_count % 5 == 0:
                                        await asyncio.sleep(0)
                            if chunk.get("done", False):
                                elapsed = time.time() - start_time
                                log('SUCCESS', f"Streaming complete: {token_count} tokens | {elapsed:.2f}s")
                                break
                        except json.JSONDecodeError:
                            continue

                    if time.time() - last_chunk_time > STALL_TIMEOUT:
                        log('ERROR', f"No tokens for {STALL_TIMEOUT}s - Generation stalled")
                        break

    except asyncio.CancelledError:
        log('INFO', "Ollama streaming cancelled by client")
        raise
    except asyncio.TimeoutError:
        log('ERROR', f"Streaming timeout after {GEN_TIMEOUT}s")
        yield "\n\nWarning: Response timeout - please try a shorter question"
    except aiohttp.ClientError as e:
        log('ERROR', f"Connection error: {e}")
        yield "\n\nWarning: Connection error - is Ollama running?"
    except Exception as e:
        log('ERROR', f"Streaming error: {e}")
        yield f"\n\nWarning: Error: {str(e)}"


def generate_with_streaming(messages: List[Dict], model: str, options: Dict) -> Optional[str]:
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "keep_alive": "10m",
        "options": options,
    }
    max_tokens = options.get("num_predict", "N/A")
    ctx_size = options.get("num_ctx", "N/A")
    temp = options.get("temperature", "N/A")
    intent_log = "GREETING" if options.get("num_predict", 0) < 100 else "ELABORATE" if options.get("num_predict", 0) > 1500 else "NORMAL"
    print("\n" + "Settings " + "="*77)
    log('MODEL', f"Target Model: {model}")
    log('INFO', f"Settings Context: {ctx_size} | Max Tokens: {max_tokens} | Temp: {temp}")
    log('INFO', f"Style Intent: {intent_log}")
    log('QUESTION', f"Query: {messages[-1]['content'][:150]}{'...' if len(messages[-1]['content']) > 150 else ''}")
    print("="*80)
    print(f"\n{'GENERATING':^80}\n")
    print("-"*80)

    try:
        response = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, stream=True, timeout=GEN_TIMEOUT)
        response.raise_for_status()
        full_response = []
        token_count = 0
        word_count_estimate = 0
        start_time = time.time()
        last_chunk_time = time.time()
        last_print_time = 0
        batch_buffer = []
        batch_size = 4

        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                chunk = json.loads(line)
                if chunk.get("done", False):
                    if batch_buffer:
                        text = "".join(batch_buffer)
                        full_response.append(text)
                        token_count += len(text.split())
                        word_count_estimate += len(text.split())
                    break
                if "message" not in chunk or chunk["message"]["role"] != "assistant":
                    continue
                text = chunk["message"].get("content", "")
                if not text:
                    continue
                batch_buffer.append(text)
                if len(batch_buffer) >= batch_size:
                    combined = "".join(batch_buffer)
                    full_response.append(combined)
                    new_tokens = len(combined.split())
                    token_count += new_tokens
                    word_count_estimate += new_tokens
                    batch_buffer.clear()
                    now = time.time()
                    elapsed = max(now - start_time, 0.1)
                    speed = token_count / elapsed
                    progress = min(30, int(token_count / 40))
                    bar = "█" * progress + "░" * (30 - progress)
                    if now - last_print_time >= 0.3:
                        print(f"\rSpeed {speed:5.1f} t/s │ {token_count:4d} tokens │ {word_count_estimate:3d} words │ {bar} {int((progress/30)*100):3d}%",
                              end="", flush=True)
                        last_print_time = now
                    last_chunk_time = now
            except json.JSONDecodeError:
                continue

        if batch_buffer:
            final_text = "".join(batch_buffer)
            full_response.append(final_text)
            token_count += len(final_text.split())
            word_count_estimate += len(final_text.split())

        answer = "".join(full_response).strip()
        total_time = time.time() - start_time
        final_speed = token_count / total_time if total_time > 0 else 0
        char_count = len(answer)
        actual_words = len(answer.split())

        print("\r" + " " * 120, end="\r")
        print("-"*80)
        print(f"\n{'GENERATION COMPLETE':^80}\n")
        log('SUCCESS', f"Characters: {char_count:,}")
        log('SUCCESS', f"Words: {actual_words:,}")
        log('SUCCESS', f"Tokens: {token_count:,}")
        log('SUCCESS', f"Time: {total_time:.2f}s")
        log('SUCCESS', f"Speed: {final_speed:.1f} tok/s | {actual_words/total_time:.1f} words/s")
        print("-" * 80)

        if not answer or len(answer) < 5:
            log('ERROR', "Empty or too short response")
            return None

        return answer

    except requests.Timeout:
        print("\r" + " " * 120, end="\r")
        log('ERROR', f"Timeout after {GEN_TIMEOUT}s")
        return None
    except requests.ConnectionError:
        print("\r" + " " * 120, end="\r")
        log('ERROR', "Cannot connect to Ollama. Run: ollama serve")
        return None
    except Exception as e:
        print("\r" + " " * 120, end="\r")
        log('ERROR', f"Generation failed: {str(e)}")
        return None


def validate_llm_answer(answer: str, model: str) -> str:
    return answer


# ────────────────────────────────────────────────
# FIX 1D ── Cleaner & more reliable greeting handler
# ────────────────────────────────────────────────
def get_instant_greeting_response(question: str) -> Optional[str]:
    q_lower = question.lower().strip()
    q_clean = re.sub(r'[.!?,\s]+$', '', q_lower)

    # ✅ IDENTITY RESPONSES (HIGHEST PRIORITY - REGEX MATCH)
    identity_patterns = [
        (r'\b(who are you|what are you)\b', SAFE_IDENTITY),
        (r'\b(your name|what\'s your name|whats your name)\b', "My name is Nexora 1.1."),
        (r'\b(who (made|built|created|developed) you)\b', SAFE_IDENTITY),
        (r'\b(tell me about yourself|about yourself|introduce yourself)\b', SAFE_IDENTITY),
        (r'\b(who is nexora|what is nexora)\b', SAFE_IDENTITY),
    ]
    
    for pattern, response in identity_patterns:
        if re.search(pattern, q_lower):
            return response
    
    # ✅ MULTI-WORD GREETINGS
    multi_word_greetings = {
        "hey there": ["Hey there! What can I help you with?", "Hi! What's up?", "Hello! How can I assist?"],
        "hi there": ["Hi there! What can I do for you?", "Hey! How can I help?", "Hello! Ready to chat?"],
        "hello there": ["Hello there! What's on your mind?", "Hey! How can I assist?", "Hi! What's up?"],
        "good morning": ["Good morning! How can I help?", "Morning! What's on your mind today?"],
        "good afternoon": ["Good afternoon! What can I do for you?", "Afternoon! How can I assist?"],
        "good evening": ["Good evening! Ready to chat?", "Evening! What's up?"],
    }

    for phrase, responses in multi_word_greetings.items():
        if phrase in q_lower:
            return random.choice(responses)

    # ✅ SIMPLE GREETINGS
    simple_greetings = {
        "hi": ["Hey! What's up?", "Hi there! How can I help?", "Hello! Ready to dive in?"],
        "hey": ["Hey! What's up?", "Hello! How can I help you today?", "Hi there! Ready to dive in?"],
        "hello": ["Hello! How can I help you today?", "Hey there! What's on your mind?", "Hi! What's up?"],
        "sup": ["Hey! What's good?", "All good! What can I help with?"],
        "yo": ["Yo! What can I do for you?", "Hey! What's up?"],
        "howdy": ["Howdy! How can I help?", "Hey there! What can I do for you?"],
        "greetings": ["Greetings! How may I assist you?"],
        "morning": ["Good morning! How can I help?"],
        "afternoon": ["Good afternoon! What's on your mind?"],
        "evening": ["Good evening! Ready to chat?"],
    }

    if q_clean in simple_greetings:
        return random.choice(simple_greetings[q_clean])

    # ✅ GREETING PATTERNS
    greeting_patterns = [
        (r'^(hi+|hey+|hello+|yo+|sup+|howdy|greetings)[\s.!?]*$', 
         ["Hey! What's up?", "Hello! How can I help?", "Hi there!"]),
        (r'^(good\s+)?(morning|afternoon|evening)[\s.!?]*$',
         ["Good {}! How can I help?"]),
        (r'^(whats up|what\'s up|wassup)[\s?!.]*$',
         ["All good! What can I help with?"]),
        (r'^how (are you|are u|r u|is it going|you doing)[\s?!.]*$',
         ["Doing great! How can I help you?"]),
    ]

    for pattern, responses in greeting_patterns:
        if re.match(pattern, q_lower):
            if "{}" in responses[0]:
                return random.choice(responses).format(q_clean.split()[0].capitalize())
            return random.choice(responses)

    if is_greeting(question):
        return random.choice([
            "Hey! What can I help you with?",
            "Hi there! What's on your mind?",
            "Hello! How can I assist you today?"
        ])

    return None


async def generate_direct_response(
    question: str,
    user_id: str = "guest",
    contexts: List[str] | None = None,
    intent: str = 'normal',
    is_greeting_msg: bool = False,
    enable_web_search: bool = True,
    force_search: bool = False,
    response_style: str = "balanced"
) -> str:
    contexts = contexts or []

    instant_response = get_instant_greeting_response(question)
    if instant_response:
        add_to_history(user_id, "user", question)
        add_to_history(user_id, "assistant", instant_response)
        log('SUCCESS', "Instant greeting | 0.00s")
        return instant_response

    query_style = detect_style_from_query(question)
    if query_style:
        response_style = query_style
        log('INFO', f"User requested style: {response_style.upper()}")
    else:
        log('INFO', f"Using default/fallback style: {response_style.upper()}")

    needs_search, search_query = should_search_web(question, force_search)
    search_results = []
    search_source = None

    if enable_web_search and needs_search:
        log('TOOL', f"WEB SEARCH: {search_query}")

        try:
            log('TOOL', "→ Searching Google...")
            raw_results = await asyncio.get_event_loop().run_in_executor(
                _executor, google_search, search_query, 5
            )

            if raw_results and len(raw_results) > 0:
                for result in raw_results:
                    if isinstance(result, dict):
                        title = result.get('title', '')
                        snippet = result.get('snippet', '')
                        link = result.get('link', '')

                        formatted = f"**{title}**\n{snippet}\nSource: {link}"
                        search_results.append(formatted)
                    else:
                        search_results.append(str(result))

                # FIX 1E ── Validate search results before using them
                if search_results:
                    if not validate_search_results(search_results, question):
                        log('ERROR', f"Search results not relevant to query: {question[:60]}...")
                        return (
                            "I found some information, but it doesn't seem directly relevant "
                            "to your question. Could you rephrase or be more specific?"
                        )
                    
                    search_source = "Google Search"
                    log('SUCCESS', f"Google: {len(search_results)} validated results")

            else:
                log('TOOL', "→ Trying Wikipedia...")
                wiki_chunks = await asyncio.get_event_loop().run_in_executor(
                    _executor, wiki_search, search_query
                )

                if wiki_chunks:
                    search_source = "Wikipedia"
                    search_results = wiki_chunks
                    log('SUCCESS', f"Wikipedia: {len(search_results)} chunks")
                else:
                    log('ERROR', "No search results")
                    search_results = []

        except Exception as e:
            log('ERROR', f"Search failed: {e}")
            search_results = []

    is_math = is_math_question(question)
    is_coding = is_coding_question(question)
    model = select_optimal_model(is_math_or_coding=(is_math or is_coding))

    if not model:
        return "No models available. Install: `ollama pull qwen2.5:7b`"

    start_time = time.time()

    file_contexts = retrieve_context(question, k=4)
    knowledge_results = retrieve_knowledge(question, k=5)

    all_contexts_list = search_results + file_contexts + knowledge_results
    combined_context = "\n\n".join(all_contexts_list[-6:]) if all_contexts_list else ""

    requirement = classify_factual_requirement(question)

    if needs_search:
        if not context_satisfies_requirement(requirement, all_contexts_list):
            log('ERROR', f"Grounding failed: requirement={requirement} | query={question[:60]}...")
            return (
                "I couldn't find reliable, up-to-date information "
                "that directly answers this question.\n\n"
                "The available sources don't contain the specific current or factual details needed."
            )

    add_to_history(user_id, "user", question)
    full_history = get_history_messages(user_id)
    limited_history = full_history[-6:] if len(full_history) > 6 else full_history

    system_prompt = NEXORA_SYSTEM_PROMPT
    if is_math:
        system_prompt = MATH_SYSTEM_PROMPT
    elif is_coding:
        system_prompt = CODING_SYSTEM_PROMPT

    style_config = get_response_style_config(response_style)
    strong_style_prompt = f"""
CRITICAL RESPONSE STYLE — YOU MUST OBEY THIS:
You are in "{style_config['name'].upper()}" mode.

{style_config['system_prompt']}

This overrides ALL other instructions about length, detail, or adaptiveness.
- If concise: 2–4 sentences max. No examples unless asked.
- If balanced: Natural, moderate depth. 4–8 sentences typical.
- If detailed: Be thorough. Use structure, examples, depth.

Do not adapt dynamically — stick to this style strictly."""

    system_prompt = f"{system_prompt}\n\n{strong_style_prompt}"

    messages = []

    messages.append({
        "role": "system",
        "content": (
            "You are Nexora 1.1.\n"
            "You are a standalone AI assistant.\n"
            "You do not reference models, companies, or origins.\n"
            "If asked about them, say you are privately deployed."
        )
    })

    messages.append({
        "role": "system",
        "content": system_prompt
    })

    messages.extend(limited_history)

    if combined_context:
        current_date = datetime.now().strftime('%B %d, %Y')

        grounded_system_prompt = f"""Today's date: {current_date}

{GROUNDED_SYSTEM_PROMPT}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VERIFIED SEARCH RESULTS (Retrieved {current_date}):
{combined_context}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL RULES:
- Answer ONLY using the information above
- If information is missing, explicitly state: "The search results don't contain..."
- NEVER use your training data for factual claims about current events
- NEVER predict, estimate, or guess about current positions/prices/versions
- For "Who is the current X?" → Only answer if explicitly stated in results
- If results are contradictory, mention the conflict
- Cite sources naturally: "According to [source name]..."

Example responses:
✅ CORRECT: "According to recent search results, Donald Trump is the current US President as of January 2025."
❌ WRONG: "Based on my knowledge, Joe Biden is president..." (Don't use training data!)
✅ CORRECT: "The search results mention several candidates but don't specify who currently holds the position."
❌ WRONG: "It's probably still X..." (Never guess!)
"""

        messages.append({
            "role": "system",
            "content": grounded_system_prompt
        })

        log('SUCCESS', f"Injected STRICT grounded context from {search_source or 'RAG'}")

    messages.append({
        "role": "user",
        "content": question
    })

    log('MODEL', "Generating with primary inference engine")
    if search_source:
        log('INFO', f"Using live data from: {search_source}")

    generation_options = {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "num_thread": min(8, psutil.cpu_count(logical=True)),
        "repeat_penalty": 1.1,
        "num_ctx": 8192,
        "num_predict": 1500,
    }

    answer = await asyncio.get_event_loop().run_in_executor(
        _executor,
        generate_with_streaming,
        messages,
        model,
        generation_options
    )

    # ────────────────────────────────────────────────
    # FIX 1F ── Final safety check
    # ────────────────────────────────────────────────
    if needs_search and not all_contexts_list:
        log('ERROR', 'Search was needed but no context retrieved - refusing to answer')
        return (
            "I need current information to answer this question accurately, "
            "but I wasn't able to retrieve it. Please check:\n"
            "1. Your internet connection\n"
            "2. Whether the query can be rephrased\n"
            "3. If this is a very recent topic (try again in a few hours)"
        )

    if answer:
        validated_answer = answer
        
        add_to_history(user_id, "assistant", validated_answer)
        elapsed = time.time() - start_time
        record_performance(model, elapsed, success=True)
        log('SUCCESS', f"Response in {elapsed:.2f}s")

        if search_source:
            log('SUCCESS', f"Used {search_source} data")

        return validated_answer

    return "I apologize, but I couldn't generate a response. Please try again."


async def generate_chat_response(
    question: str,
    user_id: str = "guest",
    chat_id: str | None = None,
    contexts: List[str] | None = None,
    enable_web_search: bool = True,
    response_style: str = "balanced",
    **kwargs
) -> str:
    question = (question or "").strip()
    if not question:
        return "Please ask a valid question."
    if len(question) > 4096:
        return "Question too long (max 4096 characters)."

    if is_greeting(question):
        instant_response = get_instant_greeting_response(question)
        if instant_response:
            add_to_history(user_id, "user", question)
            add_to_history(user_id, "assistant", instant_response)
            log('SUCCESS', "Instant greeting | 0.00s | No LLM used")
            return instant_response

    if not is_llm_available():
        is_llm_available.cache_clear()
        if not is_llm_available():
            log('ERROR', "Ollama is not running")
            return "Ollama is not running\n\nStart Ollama: `ollama serve`"

    contexts = contexts or []
    is_greeting_msg = False
    intent = "normal"

    return await generate_direct_response(
        question,
        user_id,
        contexts,
        intent,
        is_greeting_msg,
        enable_web_search,
        response_style=response_style
    )


async def generate_with_llm(question: str, contexts: list[str]) -> str:
    return await generate_chat_response(question, "system", "legacy", contexts)


def startup_check():
    try:
        if is_llm_available():
            models = get_available_models()
            resources = get_system_resources()
            log('INFO', f"Ollama: Running at {OLLAMA_HOST}")
            log('INFO', f"Models Available: {len(models)}")
            log('INFO', f"System RAM: {resources['ram_available_gb']:.1f}GB available")
            log('INFO', f"CPU Threads: {resources['cpu_count']}")
            optimal = select_optimal_model()
            if optimal:
                log('MODEL', f"Primary model: {optimal}")
            if os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_CX"):
                log('INFO', "Web Search: Configured")
            else:
                log('ERROR', "Web Search: Not configured (missing API keys)")
        else:
            log('ERROR', "LLM not detected - Start with: ollama serve")
    except Exception as e:
        log('ERROR', f"Startup check failed: {e}")


import threading
threading.Thread(target=startup_check, daemon=True).start()