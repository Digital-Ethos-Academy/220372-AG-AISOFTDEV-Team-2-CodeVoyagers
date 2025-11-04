"""Audio transcription functionality."""

import asyncio
from typing import Any, Optional, Tuple
from pathlib import Path

from .errors import ProviderOperationError
from .helpers import ensure_provider
from .logging import get_logger

logger = get_logger()


def transcribe_audio(
    audio_path: str,
    client: Any,
    model_name: str,
    api_provider: str,
    language: Optional[str] = None
) -> str:
    """Transcribe audio file to text.

    Args:
        audio_path (str): Path to the audio file.
        client: The API client.
        model_name (str): The name of the model to use.
        api_provider (str): The API provider ('openai', 'google', etc.).
        language (str, optional): Language code for transcription (e.g., 'en', 'es').

    Returns:
        str: The transcribed text.
        
    Raises
    ------
    ProviderOperationError
        If the provider call fails.

    Example
    -------
    >>> client, model, provider = setup_llm_client("whisper-1")
    >>> transcription = transcribe_audio("audio.mp3", client, model, provider)
    """
    # Validate audio file exists
    audio_file = Path(audio_path)
    if not audio_file.exists():
        raise ProviderOperationError(
            api_provider,
            model_name,
            "audio transcription",
            f"Audio file not found: {audio_path}"
        )
    
    provider_module = ensure_provider(
        client, api_provider, model_name, "audio transcription"
    )
    
    if hasattr(provider_module, "transcribe_audio"):
        if language:
            return provider_module.transcribe_audio(client, audio_path, model_name, language)
        return provider_module.transcribe_audio(client, audio_path, model_name)
    else:
        raise ProviderOperationError(
            api_provider,
            model_name,
            "audio transcription",
            f"Provider '{api_provider}' does not support audio transcription"
        )


async def async_transcribe_audio(
    audio_path: str,
    client: Any,
    model_name: str,
    api_provider: str,
    language: Optional[str] = None
) -> str:
    """Asynchronously transcribe audio file to text.

    Args:
        audio_path (str): Path to the audio file.
        client: The API client.
        model_name (str): The name of the model to use.
        api_provider (str): The API provider ('openai', 'google', etc.).
        language (str, optional): Language code for transcription (e.g., 'en', 'es').

    Returns:
        str: The transcribed text.
        
    Raises
    ------
    ProviderOperationError
        If the provider call fails.

    Example
    -------
    >>> client, model, provider = await async_setup_llm_client("whisper-1")
    >>> transcription = await async_transcribe_audio("audio.mp3", client, model, provider)
    """
    # Validate audio file exists
    audio_file = Path(audio_path)
    if not audio_file.exists():
        raise ProviderOperationError(
            api_provider,
            model_name,
            "audio transcription",
            f"Audio file not found: {audio_path}"
        )
    
    provider_module = ensure_provider(
        client, api_provider, model_name, "audio transcription"
    )
    
    if hasattr(provider_module, "async_transcribe_audio"):
        if language:
            return await provider_module.async_transcribe_audio(client, audio_path, model_name, language)
        return await provider_module.async_transcribe_audio(client, audio_path, model_name)
    elif hasattr(provider_module, "transcribe_audio"):
        if language:
            return await asyncio.to_thread(
                provider_module.transcribe_audio, client, audio_path, model_name, language
            )
        return await asyncio.to_thread(
            provider_module.transcribe_audio, client, audio_path, model_name
        )
    else:
        raise ProviderOperationError(
            api_provider,
            model_name,
            "audio transcription",
            f"Provider '{api_provider}' does not support audio transcription"
        )


def transcribe_audio_compat(
    audio_path: str,
    client: Any,
    model_name: str,
    api_provider: str,
    language: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """Compatibility wrapper for audio transcription returning ``(result, error_str)``.

    .. deprecated:: 1.0
       Use :func:`transcribe_audio` and catch :class:`ProviderOperationError`.
    """
    try:
        result = transcribe_audio(audio_path, client, model_name, api_provider, language)
        return result, None
    except ProviderOperationError as e:
        return None, str(e)


async def async_transcribe_audio_compat(
    audio_path: str,
    client: Any,
    model_name: str,
    api_provider: str,
    language: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """Async compatibility wrapper for audio transcription.

    .. deprecated:: 1.0
       Use :func:`async_transcribe_audio` and catch :class:`ProviderOperationError`.
    """
    try:
        result = await async_transcribe_audio(audio_path, client, model_name, api_provider, language)
        return result, None
    except ProviderOperationError as e:
        return None, str(e)


def get_supported_audio_formats(api_provider: str) -> list:
    """Get supported audio formats for a provider.
    
    Args:
        api_provider (str): The API provider name.
        
    Returns:
        list: List of supported audio file extensions.
    """
    # Common supported formats by provider
    provider_formats = {
        "openai": [".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"],
        "google": [".wav", ".mp3", ".flac", ".aac", ".ogg", ".webm"],
        "anthropic": [],  # No audio support yet
        "deepseek": [],   # No audio support yet
        "meta": [],       # No audio support yet
    }
    
    return provider_formats.get(api_provider.lower(), [])


def validate_audio_file(audio_path: str, api_provider: str) -> bool:
    """Validate if an audio file is supported by the provider.
    
    Args:
        audio_path (str): Path to the audio file.
        api_provider (str): The API provider name.
        
    Returns:
        bool: True if the file is supported, False otherwise.
    """
    audio_file = Path(audio_path)
    
    if not audio_file.exists():
        return False
    
    supported_formats = get_supported_audio_formats(api_provider)
    if not supported_formats:
        return False
    
    file_extension = audio_file.suffix.lower()
    return file_extension in supported_formats


__all__ = [
    "transcribe_audio",
    "transcribe_audio_compat",
    "async_transcribe_audio",
    "async_transcribe_audio_compat",
    "get_supported_audio_formats",
    "validate_audio_file",
]