"""Image generation and editing functionality."""

import asyncio
from typing import Any, Optional, Tuple

from .errors import ProviderOperationError
from .helpers import ensure_provider, normalize_prompt
from .logging import get_logger

logger = get_logger()


def get_image_generation_completion(
    client: Any, prompt: str, model_name: str, api_provider: str
) -> Tuple[str, str]:
    """
    Generates an image based on a prompt using the specified API provider.

    Args:
        client: The API client.
        prompt (str): The text prompt for image generation.
        model_name (str): The name of the model to use.
        api_provider (str): The API provider ('google', 'openai', etc.).

    Returns:
        A tuple containing the base64-encoded image and the MIME type.
        
    Raises
    ------
    ProviderOperationError
        If the provider call fails.

    Example
    -------
    >>> client, model, provider = setup_llm_client("dall-e-3")
    >>> base64_img, mime_type = get_image_generation_completion(
    ...     client, "A beautiful sunset", model, provider
    ... )
    """
    prompt = normalize_prompt(prompt)
    provider_module = ensure_provider(
        client, api_provider, model_name, "image generation"
    )
    
    return provider_module.image_generation(client, prompt, model_name)


async def async_get_image_generation_completion(
    client: Any, prompt: str, model_name: str, api_provider: str
) -> Tuple[str, str]:
    """Asynchronously fetch an image generation completion.
    
    Args:
        client: The API client.
        prompt (str): The text prompt for image generation.
        model_name (str): The name of the model to use.
        api_provider (str): The API provider ('google', 'openai', etc.).

    Returns:
        A tuple containing the base64-encoded image and the MIME type.
        
    Raises
    ------
    ProviderOperationError
        If the provider call fails.

    Example
    -------
    >>> client, model, provider = await async_setup_llm_client("dall-e-3")
    >>> base64_img, mime_type = await async_get_image_generation_completion(
    ...     client, "A beautiful sunset", model, provider
    ... )
    """
    prompt = normalize_prompt(prompt)
    provider_module = ensure_provider(
        client, api_provider, model_name, "image generation"
    )
    if hasattr(provider_module, "async_image_generation"):
        if api_provider == "google":
            return await provider_module.async_image_generation(client, prompt, model_name)
        return await provider_module.async_image_generation(
            client, prompt, model_name
        )
    if api_provider == "google":
        return await asyncio.to_thread(
            provider_module.image_generation, client, prompt, model_name
        )
    return await asyncio.to_thread(
        provider_module.image_generation, client, prompt, model_name
    )


def get_image_generation_completion_compat(
    client: Any, prompt: str, model_name: str, api_provider: str
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Compatibility wrapper returning ``(base64_str, mime_type, error_str)``.

    .. deprecated:: 1.0
       Use :func:`get_image_generation_completion` and catch :class:`ProviderOperationError`.
    """
    try:
        b64, mime = get_image_generation_completion(
            client, prompt, model_name, api_provider
        )
        return b64, mime, None
    except ProviderOperationError as e:
        return None, None, str(e)


async def async_get_image_generation_completion_compat(
    client: Any, prompt: str, model_name: str, api_provider: str
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Async compatibility wrapper for image generation.

    .. deprecated:: 1.0
       Use :func:`async_get_image_generation_completion` and catch :class:`ProviderOperationError`.
    """
    try:
        b64, mime = await async_get_image_generation_completion(
            client, prompt, model_name, api_provider
        )
        return b64, mime, None
    except ProviderOperationError as e:
        return None, None, str(e)


def get_image_edit_completion(
    client: Any, 
    prompt: str, 
    image_path: str, 
    model_name: str, 
    api_provider: str,
    mask_path: Optional[str] = None
) -> Tuple[str, str]:
    """
    Edits an image based on a prompt using the specified API provider.

    Args:
        client: The API client.
        prompt (str): The text prompt describing the desired edit.
        image_path (str): Path to the image to edit.
        model_name (str): The name of the model to use.
        api_provider (str): The API provider ('openai', etc.).
        mask_path (str, optional): Path to mask image for selective editing.

    Returns:
        A tuple containing the base64-encoded edited image and the MIME type.
        
    Raises
    ------
    ProviderOperationError
        If the provider call fails.

    Example
    -------
    >>> client, model, provider = setup_llm_client("dall-e-3")
    >>> base64_img, mime_type = get_image_edit_completion(
    ...     client, "Add a rainbow", "image.png", model, provider
    ... )
    """
    prompt = normalize_prompt(prompt)
    provider_module = ensure_provider(
        client, api_provider, model_name, "image editing"
    )
    
    if hasattr(provider_module, "image_edit"):
        return provider_module.image_edit(client, prompt, image_path, model_name, mask_path)
    else:
        raise ProviderOperationError(
            api_provider,
            model_name,
            "image editing",
            f"Provider '{api_provider}' does not support image editing"
        )


async def async_get_image_edit_completion(
    client: Any, 
    prompt: str, 
    image_path: str, 
    model_name: str, 
    api_provider: str,
    mask_path: Optional[str] = None
) -> Tuple[str, str]:
    """Asynchronously edit an image based on a prompt.
    
    Args:
        client: The API client.
        prompt (str): The text prompt describing the desired edit.
        image_path (str): Path to the image to edit.
        model_name (str): The name of the model to use.
        api_provider (str): The API provider ('openai', etc.).
        mask_path (str, optional): Path to mask image for selective editing.

    Returns:
        A tuple containing the base64-encoded edited image and the MIME type.
        
    Raises
    ------
    ProviderOperationError
        If the provider call fails.

    Example
    -------
    >>> client, model, provider = await async_setup_llm_client("dall-e-3")
    >>> base64_img, mime_type = await async_get_image_edit_completion(
    ...     client, "Add a rainbow", "image.png", model, provider
    ... )
    """
    prompt = normalize_prompt(prompt)
    provider_module = ensure_provider(
        client, api_provider, model_name, "image editing"
    )
    
    if hasattr(provider_module, "async_image_edit"):
        return await provider_module.async_image_edit(client, prompt, image_path, model_name, mask_path)
    elif hasattr(provider_module, "image_edit"):
        return await asyncio.to_thread(
            provider_module.image_edit, client, prompt, image_path, model_name, mask_path
        )
    else:
        raise ProviderOperationError(
            api_provider,
            model_name,
            "image editing",
            f"Provider '{api_provider}' does not support image editing"
        )


def get_image_edit_completion_compat(
    client: Any, 
    prompt: str, 
    image_path: str, 
    model_name: str, 
    api_provider: str,
    mask_path: Optional[str] = None
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Compatibility wrapper for image editing returning ``(base64_str, mime_type, error_str)``.

    .. deprecated:: 1.0
       Use :func:`get_image_edit_completion` and catch :class:`ProviderOperationError`.
    """
    try:
        b64, mime = get_image_edit_completion(
            client, prompt, image_path, model_name, api_provider, mask_path
        )
        return b64, mime, None
    except ProviderOperationError as e:
        return None, None, str(e)


async def async_get_image_edit_completion_compat(
    client: Any, 
    prompt: str, 
    image_path: str, 
    model_name: str, 
    api_provider: str,
    mask_path: Optional[str] = None
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Async compatibility wrapper for image editing.

    .. deprecated:: 1.0
       Use :func:`async_get_image_edit_completion` and catch :class:`ProviderOperationError`.
    """
    try:
        b64, mime = await async_get_image_edit_completion(
            client, prompt, image_path, model_name, api_provider, mask_path
        )
        return b64, mime, None
    except ProviderOperationError as e:
        return None, None, str(e)


__all__ = [
    "get_image_generation_completion",
    "get_image_generation_completion_compat",
    "async_get_image_generation_completion",
    "async_get_image_generation_completion_compat",
    "get_image_edit_completion",
    "get_image_edit_completion_compat",
    "async_get_image_edit_completion",
    "async_get_image_edit_completion_compat",
]