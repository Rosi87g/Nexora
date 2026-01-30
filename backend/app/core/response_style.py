# app/core/response_style.py

from typing import Dict, Literal
from enum import Enum

ResponseStyleType = Literal["concise", "balanced", "detailed"]


class ResponseStyle(Enum):
    """Enum for available response styles"""
    CONCISE = "concise"
    BALANCED = "balanced"
    DETAILED = "detailed"


# Response style configurations
RESPONSE_STYLE_CONFIGS = {
    "concise": {
        "name": "Concise",
        "description": "Brief and to-the-point responses",
        "system_prompt": """You should provide CONCISE, BRIEF responses. Get STRAIGHT to the point without unnecessary elaboration.

Key guidelines:
- Keep answers short (2-4 sentences typically)
- Avoid long explanations unless explicitly required
- Skip examples and tangents unless specifically requested
- Focus on the core answer only
- Use simple, direct language

Only provide more detail if the question explicitly requires it.""",
        "num_predict": 800,
        "temperature": 0.7,
        "top_p": 0.9,
        "intent_multiplier": 0.6,  # Reduce token generation
    },
    
    "balanced": {
        "name": "Balanced",
        "description": "Well-rounded responses with moderate detail",
        "system_prompt": """You should provide BALANCED responses with appropriate detail.

Key guidelines:
- Include relevant context and examples when helpful
- Aim for clear, informative answers (4-8 sentences typically)
- Avoid being overly verbose or too brief
- Strike a balance between thoroughness and conciseness
- Provide explanations that are neither shallow nor exhaustive

Adjust depth based on question complexity.""",
        "num_predict": 1500,
        "temperature": 0.7,
        "top_p": 0.9,
        "intent_multiplier": 1.0,  # Standard token generation
    },
    
    "detailed": {
        "name": "Detailed",
        "description": "Comprehensive and thorough responses",
        "system_prompt": """You should provide DETAILED, COMPREHENSIVE responses with thorough explanations.

Key guidelines:
- Include relevant context, examples, and step-by-step breakdowns
- Explore multiple angles and provide in-depth analysis
- Use formatting like bullet points or numbered lists for clarity
- Provide additional insights beyond the basic answer
- Explain the "why" and "how" behind concepts
- Anticipate follow-up questions and address them

Be thorough but still organized and readable.""",
        "num_predict": 2500,
        "temperature": 0.7,
        "top_p": 0.9,
        "intent_multiplier": 1.5,  # Increase token generation
    }
}


def get_response_style_config(style: ResponseStyleType = "balanced") -> Dict:
    """
    Get configuration for a specific response style.
    
    Args:
        style: The response style (concise, balanced, detailed)
        
    Returns:
        Dict containing style configuration
    """
    if style not in RESPONSE_STYLE_CONFIGS:
        print(f"Warning: Invalid style '{style}', defaulting to 'balanced'")
        style = "balanced"
    
    return RESPONSE_STYLE_CONFIGS[style]


def get_style_system_prompt(style: ResponseStyleType = "balanced") -> str:
    """
    Get the system prompt for a specific response style.
    
    Args:
        style: The response style
        
    Returns:
        System prompt string
    """
    config = get_response_style_config(style)
    return config["system_prompt"]


def adjust_model_options_for_style(
    base_options: Dict,
    style: ResponseStyleType = "balanced",
    intent: str = "normal"
) -> Dict:
    """
    Adjust model generation options based on response style.
    
    Args:
        base_options: Base model options dict
        style: The response style
        intent: User intent (normal, elaborate, brief)
        
    Returns:
        Adjusted options dict
    """
    config = get_response_style_config(style)
    
    # Start with base options
    adjusted = base_options.copy()
    
    # Apply style-specific settings
    adjusted["num_predict"] = config["num_predict"]
    adjusted["temperature"] = config.get("temperature", 0.7)
    adjusted["top_p"] = config.get("top_p", 0.9)
    
    # Adjust based on detected intent
    multiplier = config["intent_multiplier"]
    
    if intent == "elaborate":
        # User wants more detail regardless of style
        adjusted["num_predict"] = int(adjusted["num_predict"] * 1.5)
    elif intent == "brief":
        # User wants brevity regardless of style
        adjusted["num_predict"] = int(adjusted["num_predict"] * 0.5)
    else:
        # Normal intent - apply style multiplier
        adjusted["num_predict"] = int(adjusted["num_predict"] * multiplier)
    
    # Ensure we don't exceed reasonable limits
    adjusted["num_predict"] = min(adjusted["num_predict"], 3500)
    adjusted["num_predict"] = max(adjusted["num_predict"], 200)
    
    return adjusted


def detect_style_from_query(query: str) -> ResponseStyleType:
    """
    Detect if the user is requesting a specific style in their query.
    
    Args:
        query: User's query string
        
    Returns:
        Detected style or None if no preference detected
    """
    query_lower = query.lower()
    
    # Check for explicit style requests
    concise_keywords = [
        "briefly", "in short", "quick answer", "tldr", "summarize",
        "give me a short", "concisely", "just the basics", "quick summary"
    ]
    
    detailed_keywords = [
        "explain in detail", "elaborate", "comprehensive", "thorough",
        "in depth", "step by step", "detailed explanation", "explain thoroughly",
        "walk me through", "break it down", "full explanation"
    ]
    
    # Check detailed first (more specific)
    if any(keyword in query_lower for keyword in detailed_keywords):
        return "detailed"
    
    # Check concise
    if any(keyword in query_lower for keyword in concise_keywords):
        return "concise"
    
    # No explicit style detected, return None
    return None


def merge_style_with_base_prompt(base_prompt: str, style: ResponseStyleType) -> str:
    """
    Merge the style-specific prompt with the base system prompt.
    
    Args:
        base_prompt: Base system prompt
        style: Response style
        
    Returns:
        Combined system prompt
    """
    style_prompt = get_style_system_prompt(style)
    
    return f"""{base_prompt}

RESPONSE STYLE INSTRUCTION:
{style_prompt}

Remember to maintain your core identity and capabilities while adhering to the response style above."""


# Example usage functions for testing
def get_all_styles_info() -> Dict:
    """Get information about all available styles."""
    return {
        style: {
            "name": config["name"],
            "description": config["description"],
            "max_tokens": config["num_predict"]
        }
        for style, config in RESPONSE_STYLE_CONFIGS.items()
    }
