"""Helper functions for the utils package."""

import re
from typing import Any

from .errors import ProviderOperationError
from .providers import PROVIDERS


def normalize_prompt(prompt: str) -> str:
    """Normalize a prompt by stripping whitespace and ensuring it's not empty.
    
    Parameters
    ----------
    prompt : str
        The prompt to normalize.
        
    Returns
    -------
    str
        The normalized prompt.
    """
    if not isinstance(prompt, str):
        return str(prompt).strip()
    return prompt.strip()


def ensure_provider(
    client: Any, 
    api_provider: str, 
    model_name: str, 
    operation: str
) -> Any:
    """Ensure a provider exists and return the provider module.
    
    Parameters
    ----------
    client : Any
        The client object.
    api_provider : str
        The API provider name.
    model_name : str
        The model name.
    operation : str
        The operation being performed.
        
    Returns
    -------
    Any
        The provider module.
        
    Raises
    ------
    ProviderOperationError
        If the provider is not found or doesn't support the operation.
    """
    provider_module = PROVIDERS.get(api_provider)
    if not provider_module:
        raise ProviderOperationError(
            api_provider,
            model_name,
            operation,
            f"Provider '{api_provider}' not found in PROVIDERS registry"
        )
    return provider_module


def validate_model_name(model_name: str) -> bool:
    """Validate that a model name is properly formatted.
    
    Parameters
    ----------
    model_name : str
        The model name to validate.
        
    Returns
    -------
    bool
        True if the model name is valid.
    """
    if not model_name or not isinstance(model_name, str):
        return False
    return bool(re.match(r'^[a-zA-Z0-9\-_.]+$', model_name))


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing invalid characters.
    
    Parameters
    ----------
    filename : str
        The filename to sanitize.
        
    Returns
    -------
    str
        The sanitized filename.
    """
    # Remove invalid characters for filenames
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    return sanitized or 'untitled'


def parse_temperature(temperature: Any) -> float:
    """Parse and validate a temperature value.
    
    Parameters
    ----------
    temperature : Any
        The temperature value to parse.
        
    Returns
    -------
    float
        The parsed temperature, clamped between 0.0 and 2.0.
    """
    try:
        temp = float(temperature)
        return max(0.0, min(2.0, temp))
    except (ValueError, TypeError):
        return 0.7  # Default temperature