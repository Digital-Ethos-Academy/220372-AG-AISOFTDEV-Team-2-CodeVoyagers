"""Custom exceptions for the utils package."""


class ProviderOperationError(Exception):
    """Exception raised when a provider operation fails.
    
    Attributes
    ----------
    provider : str
        The name of the provider that failed.
    model : str
        The model name being used.
    operation : str
        The operation that was being performed.
    message : str
        The error message.
    """
    
    def __init__(self, provider: str, model: str, operation: str, message: str):
        """Initialize the ProviderOperationError.
        
        Parameters
        ----------
        provider : str
            The name of the provider that failed.
        model : str
            The model name being used.
        operation : str
            The operation that was being performed.
        message : str
            The error message.
        """
        self.provider = provider
        self.model = model
        self.operation = operation
        self.message = message
        super().__init__(f"Provider '{provider}' failed for model '{model}' during {operation}: {message}")


class ModelNotFoundError(Exception):
    """Exception raised when a requested model is not found."""
    pass


class ProviderNotFoundError(Exception):
    """Exception raised when a requested provider is not found."""
    pass


class ConfigurationError(Exception):
    """Exception raised when there is a configuration error."""
    pass


class APIKeyError(Exception):
    """Exception raised when there is an API key error."""
    pass