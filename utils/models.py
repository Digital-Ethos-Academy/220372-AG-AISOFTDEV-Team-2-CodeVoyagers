"""Model configurations for supported LLM providers."""

from typing import Dict, Any, List


# Recommended models configuration
RECOMMENDED_MODELS: Dict[str, Dict[str, Any]] = {
    "gpt-4o": {
        "provider": "openai",
        "max_tokens": 128000,
        "supports_vision": True,
        "supports_function_calling": True,
        "cost_per_1k_tokens": {"input": 0.0025, "output": 0.01}
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "max_tokens": 128000,
        "supports_vision": True,
        "supports_function_calling": True,
        "cost_per_1k_tokens": {"input": 0.000150, "output": 0.0006}
    },
    "gpt-4-turbo": {
        "provider": "openai",
        "max_tokens": 128000,
        "supports_vision": True,
        "supports_function_calling": True,
        "cost_per_1k_tokens": {"input": 0.01, "output": 0.03}
    },
    "o1": {
        "provider": "openai",
        "max_tokens": 32768,
        "supports_vision": False,
        "supports_function_calling": False,
        "cost_per_1k_tokens": {"input": 0.015, "output": 0.06}
    },
    "o3": {
        "provider": "openai",
        "max_tokens": 32768,
        "supports_vision": False,
        "supports_function_calling": False,
        "cost_per_1k_tokens": {"input": 0.015, "output": 0.06}
    },
    "gemini-2.5-flash": {
        "provider": "google",
        "max_tokens": 1048576,
        "supports_vision": True,
        "supports_function_calling": True,
        "cost_per_1k_tokens": {"input": 0.000075, "output": 0.0003}
    },
    "gemini-1.5-pro": {
        "provider": "google",
        "max_tokens": 2097152,
        "supports_vision": True,
        "supports_function_calling": True,
        "cost_per_1k_tokens": {"input": 0.00125, "output": 0.005}
    },
    "claude-3-5-sonnet": {
        "provider": "anthropic",
        "max_tokens": 8192,
        "supports_vision": True,
        "supports_function_calling": True,
        "cost_per_1k_tokens": {"input": 0.003, "output": 0.015}
    },
    "claude-3-5-haiku": {
        "provider": "anthropic",
        "max_tokens": 8192,
        "supports_vision": True,
        "supports_function_calling": True,
        "cost_per_1k_tokens": {"input": 0.0008, "output": 0.004}
    },
    "llama-3.3-70b": {
        "provider": "meta",
        "max_tokens": 8192,
        "supports_vision": False,
        "supports_function_calling": True,
        "cost_per_1k_tokens": {"input": 0.0005, "output": 0.0015}
    },
    "deepseek-v3": {
        "provider": "deepseek",
        "max_tokens": 8192,
        "supports_vision": False,
        "supports_function_calling": True,
        "cost_per_1k_tokens": {"input": 0.00014, "output": 0.00028}
    }
}


def get_model_info(model_name: str) -> Dict[str, Any]:
    """Get information about a specific model.
    
    Parameters
    ----------
    model_name : str
        The name of the model.
        
    Returns
    -------
    Dict[str, Any]
        Model configuration dictionary.
        
    Raises
    ------
    KeyError
        If the model is not found.
    """
    if model_name not in RECOMMENDED_MODELS:
        raise KeyError(f"Model '{model_name}' not found in RECOMMENDED_MODELS")
    return RECOMMENDED_MODELS[model_name]


def get_models_by_provider(provider: str) -> List[str]:
    """Get all models for a specific provider.
    
    Parameters
    ----------
    provider : str
        The provider name.
        
    Returns
    -------
    List[str]
        List of model names for the provider.
    """
    return [
        model for model, config in RECOMMENDED_MODELS.items()
        if config["provider"] == provider
    ]


def get_vision_capable_models() -> List[str]:
    """Get all models that support vision.
    
    Returns
    -------
    List[str]
        List of model names that support vision.
    """
    return [
        model for model, config in RECOMMENDED_MODELS.items()
        if config.get("supports_vision", False)
    ]


def get_function_calling_models() -> List[str]:
    """Get all models that support function calling.
    
    Returns
    -------
    List[str]
        List of model names that support function calling.
    """
    return [
        model for model, config in RECOMMENDED_MODELS.items()
        if config.get("supports_function_calling", False)
    ]


def recommended_models_table() -> str:
    """Generate a formatted table of recommended models.
    
    Returns
    -------
    str
        A formatted table string showing model information.
    """
    headers = ["Model", "Provider", "Max Tokens", "Vision", "Functions", "Cost (Input/Output per 1K)"]
    rows = []
    
    for model, config in RECOMMENDED_MODELS.items():
        cost = config.get("cost_per_1k_tokens", {})
        cost_str = f"${cost.get('input', 0):.6f}/${cost.get('output', 0):.6f}"
        
        row = [
            model,
            config["provider"],
            str(config["max_tokens"]),
            "✓" if config.get("supports_vision", False) else "✗",
            "✓" if config.get("supports_function_calling", False) else "✗",
            cost_str
        ]
        rows.append(row)
    
    # Calculate column widths
    col_widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))
    
    # Format table
    separator = "+" + "+".join("-" * (width + 2) for width in col_widths) + "+"
    header_row = "|" + "|".join(f" {headers[i]:<{col_widths[i]}} " for i in range(len(headers))) + "|"
    
    table_lines = [separator, header_row, separator]
    
    for row in rows:
        table_row = "|" + "|".join(f" {row[i]:<{col_widths[i]}} " for i in range(len(row))) + "|"
        table_lines.append(table_row)
    
    table_lines.append(separator)
    
    return "\n".join(table_lines)