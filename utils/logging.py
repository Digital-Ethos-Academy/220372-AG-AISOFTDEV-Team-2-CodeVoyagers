"""Logging configuration for the utils package."""

import logging
import sys
from typing import Dict, Any, Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a configured logger instance.
    
    Parameters
    ----------
    name : str, optional
        The name of the logger. If None, uses the calling module's name.
        
    Returns
    -------
    logging.Logger
        A configured logger instance.
    """
    if name is None:
        name = __name__
    
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Prevent propagation to root logger
        logger.propagate = False
    
    return logger


class StructuredLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds structured logging with extra fields."""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Process the logging record with extra fields.
        
        Parameters
        ----------
        msg : str
            The log message.
        kwargs : Dict[str, Any]
            Additional keyword arguments.
            
        Returns
        -------
        tuple
            A tuple of (message, kwargs) with processed extra fields.
        """
        extra = kwargs.get('extra', {})
        if self.extra:
            extra.update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs


def get_structured_logger(
    name: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None
) -> StructuredLoggerAdapter:
    """Get a structured logger with provider and model context.
    
    Parameters
    ----------
    name : str, optional
        The name of the logger.
    provider : str, optional
        The provider name to include in logs.
    model : str, optional
        The model name to include in logs.
        
    Returns
    -------
    StructuredLoggerAdapter
        A structured logger adapter.
    """
    logger = get_logger(name)
    extra = {}
    if provider:
        extra['provider'] = provider
    if model:
        extra['model'] = model
    
    return StructuredLoggerAdapter(logger, extra)


def configure_logging(level: str = "INFO", format_string: Optional[str] = None) -> None:
    """Configure the root logging settings.
    
    Parameters
    ----------
    level : str, optional
        The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    format_string : str, optional
        Custom format string for log messages.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=numeric_level,
        format=format_string,
        stream=sys.stdout,
        force=True
    )