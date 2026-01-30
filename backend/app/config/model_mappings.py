# backend/app/config/model_mappings.py

# Simple mapping for backward compatibility
MODEL_MAPPINGS = {
    "nexora-1.1": "qwen2.5:7b",
    "nexora-1.0": "gemma3:4b",
    "nexora-lite": "qwen2.5:3b",
    "nexora-code": "qwen2.5:14b"
}

# Detailed model information
PUBLIC_MODELS = {
    "nexora-1.2": {
        "internal_model": "qwen2.5:7b",
        "description": "Nexora's flagship model - Best for complex reasoning",
        "context_window": 8192,
        "max_tokens": 4096,
        "recommended_ram": "8GB"
    },
    "nexora-1.1": {
        "internal_model": "gemma3:4b",
        "description": "Fast and efficient - Great balance of speed and quality",
        "context_window": 4096,
        "max_tokens": 2048,
        "recommended_ram": "4GB"
    },
    "nexora-mini": {
        "internal_model": "qwen2.5:3b",
        "description": "Ultra-fast responses - Best for simple queries",
        "context_window": 2048,
        "max_tokens": 1024,
        "recommended_ram": "2GB"
    },
    "nexora-code": {
        "internal_model": "qwen2.5:14b",
        "description": "Specialized for programming and code generation",
        "context_window": 8192,
        "max_tokens": 4096,
        "recommended_ram": "8GB"
    }
}

def get_internal_model(public_name: str) -> str:
    """
    Convert public model name to Ollama model
    Raises ValueError if model not found
    """
    model = MODEL_MAPPINGS.get(public_name.lower())
    if not model:
        available = ", ".join(MODEL_MAPPINGS.keys())
        raise ValueError(f"Invalid model '{public_name}'. Available models: {available}")
    return model

def get_public_model(internal_name: str) -> str:
    """
    Convert Ollama model to public name
    Returns None if not found (no default)
    """
    reverse_map = {v: k for k, v in MODEL_MAPPINGS.items()}
    return reverse_map.get(internal_name)

def is_valid_model(model_name: str) -> bool:
    """Check if model name is valid"""
    return model_name.lower() in MODEL_MAPPINGS

def get_model_info(model_name: str) -> dict:
    """
    Get model configuration
    Returns None if model not found
    """
    return PUBLIC_MODELS.get(model_name.lower())

def list_all_models() -> list:
    """Get all available models with details"""
    return [
        {
            "id": name,
            "internal_model": MODEL_MAPPINGS[name],
            "description": PUBLIC_MODELS[name]["description"],
            "context_window": PUBLIC_MODELS[name]["context_window"],
            "max_tokens": PUBLIC_MODELS[name]["max_tokens"],
            "recommended_ram": PUBLIC_MODELS[name]["recommended_ram"]
        }
        for name in MODEL_MAPPINGS.keys()
    ]