"""Provider registry for LLM backends."""

from typing import Dict, Any, Optional
import importlib


class ProviderRegistry:
    """Registry for LLM provider modules."""
    
    def __init__(self):
        self._providers: Dict[str, Any] = {}
        self._lazy_providers: Dict[str, str] = {
            "openai": "utils.providers.openai_provider",
            "google": "utils.providers.google_provider", 
            "anthropic": "utils.providers.anthropic_provider",
            "meta": "utils.providers.meta_provider",
            "deepseek": "utils.providers.deepseek_provider",
        }
    
    def get(self, provider_name: str) -> Optional[Any]:
        """Get a provider module, loading it lazily if needed.
        
        Parameters
        ----------
        provider_name : str
            The name of the provider.
            
        Returns
        -------
        Optional[Any]
            The provider module, or None if not found.
        """
        # Return already loaded provider
        if provider_name in self._providers:
            return self._providers[provider_name]
        
        # Try to load lazily
        if provider_name in self._lazy_providers:
            try:
                module_path = self._lazy_providers[provider_name]
                module = importlib.import_module(module_path)
                self._providers[provider_name] = module
                return module
            except ImportError:
                # Provider module not available, return a mock
                return self._create_mock_provider(provider_name)
        
        return None
    
    def _create_mock_provider(self, provider_name: str) -> Any:
        """Create a mock provider for testing/fallback purposes.
        
        Parameters
        ----------
        provider_name : str
            The name of the provider.
            
        Returns
        -------
        Any
            A mock provider module.
        """
        class MockProvider:
            @staticmethod
            def setup_client(model_name: str, config: Dict[str, Any]) -> Any:
                return f"mock_client_{provider_name}_{model_name}"
            
            @staticmethod
            async def async_setup_client(model_name: str, config: Dict[str, Any]) -> Any:
                return f"mock_async_client_{provider_name}_{model_name}"
            
            @staticmethod
            def text_completion(client: Any, prompt: str, model_name: str, temperature: float = 0.7) -> str:
                return f"Mock response from {provider_name} {model_name}: {prompt[:50]}..."
            
            @staticmethod
            async def async_text_completion(client: Any, prompt: str, model_name: str, temperature: float = 0.7) -> str:
                return f"Mock async response from {provider_name} {model_name}: {prompt[:50]}..."
            
            @staticmethod
            def vision_completion(client: Any, prompt: str, image_path: str, model_name: str) -> str:
                return f"Mock vision response from {provider_name} {model_name}: {prompt[:50]}... [Image: {image_path}]"
            
            @staticmethod
            async def async_vision_completion(client: Any, prompt: str, image_path: str, model_name: str) -> str:
                return f"Mock async vision response from {provider_name} {model_name}: {prompt[:50]}... [Image: {image_path}]"
            
            @staticmethod
            def image_generation(client: Any, prompt: str, model_name: str) -> tuple:
                return (f"mock_base64_image_data_{provider_name}", "image/png")
            
            @staticmethod
            async def async_image_generation(client: Any, prompt: str, model_name: str) -> tuple:
                return (f"mock_async_base64_image_data_{provider_name}", "image/png")
            
            @staticmethod
            def transcribe_audio(client: Any, audio_path: str, model_name: str) -> str:
                return f"Mock transcription from {provider_name} {model_name}: [Audio file: {audio_path}]"
            
            @staticmethod
            async def async_transcribe_audio(client: Any, audio_path: str, model_name: str) -> str:
                return f"Mock async transcription from {provider_name} {model_name}: [Audio file: {audio_path}]"
        
        mock_provider = MockProvider()
        self._providers[provider_name] = mock_provider
        return mock_provider
    
    def register(self, provider_name: str, provider_module: Any) -> None:
        """Register a provider module.
        
        Parameters
        ----------
        provider_name : str
            The name of the provider.
        provider_module : Any
            The provider module.
        """
        self._providers[provider_name] = provider_module
    
    def list_providers(self) -> list:
        """List all available provider names.
        
        Returns
        -------
        list
            List of provider names.
        """
        return list(self._lazy_providers.keys())


# Global provider registry instance
PROVIDERS = ProviderRegistry()


def get_provider(provider_name: str) -> Optional[Any]:
    """Get a provider from the global registry.
    
    Parameters
    ----------
    provider_name : str
        The name of the provider.
        
    Returns
    -------
    Optional[Any]
        The provider module, or None if not found.
    """
    return PROVIDERS.get(provider_name)