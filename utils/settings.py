"""Settings and environment configuration for the utils package."""

import os
from pathlib import Path
from typing import Optional, Dict, Any, Union
import json

# Try to import IPython display utilities
try:
    from IPython.display import display, Markdown
    from IPython.display import Image as IPyImage
except ImportError:
    # Fallback implementations for non-Jupyter environments
    def display(obj: Any) -> None:
        """Fallback display function."""
        print(obj)
    
    class Markdown:
        """Fallback Markdown class."""
        def __init__(self, data: str):
            self.data = data
        
        def __repr__(self) -> str:
            return self.data
    
    class IPyImage:
        """Fallback Image class."""
        def __init__(self, data: Any = None, filename: str = None, **kwargs):
            self.data = data
            self.filename = filename
        
        def __repr__(self) -> str:
            return f"<Image: {self.filename or 'data'}>"


class PlantUML:
    """PlantUML diagram wrapper for display."""
    
    def __init__(self, diagram_code: str):
        """Initialize PlantUML diagram.
        
        Parameters
        ----------
        diagram_code : str
            The PlantUML diagram code.
        """
        self.diagram_code = diagram_code
    
    def __repr__(self) -> str:
        return f"<PlantUML Diagram: {len(self.diagram_code)} characters>"
    
    def _repr_html_(self) -> str:
        """HTML representation for Jupyter notebooks."""
        return f"<pre><code>{self.diagram_code}</code></pre>"


def load_dotenv(dotenv_path: Optional[Union[str, Path]] = None) -> bool:
    """Load environment variables from a .env file.
    
    Parameters
    ----------
    dotenv_path : Optional[Union[str, Path]]
        Path to the .env file. If None, looks for .env in current directory.
        
    Returns
    -------
    bool
        True if .env file was found and loaded, False otherwise.
    """
    if dotenv_path is None:
        dotenv_path = Path.cwd() / ".env"
    else:
        dotenv_path = Path(dotenv_path)
    
    if not dotenv_path.exists():
        return False
    
    try:
        with open(dotenv_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        os.environ[key] = value
        return True
    except Exception:
        return False


def load_environment() -> Dict[str, str]:
    """Load environment variables and return relevant API keys.
    
    Returns
    -------
    Dict[str, str]
        Dictionary of loaded environment variables.
    """
    # Try to load from .env file first
    load_dotenv()
    
    # Common API key environment variable names
    api_keys = [
        'OPENAI_API_KEY',
        'GOOGLE_API_KEY',
        'ANTHROPIC_API_KEY',
        'HUGGINGFACE_API_KEY',
        'GROQ_API_KEY',
        'DEEPSEEK_API_KEY',
        'META_API_KEY',
    ]
    
    loaded_keys = {}
    for key in api_keys:
        value = os.getenv(key)
        if value:
            loaded_keys[key] = value
    
    return loaded_keys


def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a specific provider.
    
    Parameters
    ----------
    provider : str
        The provider name (openai, google, anthropic, etc.).
        
    Returns
    -------
    Optional[str]
        The API key if found, None otherwise.
    """
    key_mapping = {
        'openai': 'OPENAI_API_KEY',
        'google': 'GOOGLE_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'huggingface': 'HUGGINGFACE_API_KEY',
        'groq': 'GROQ_API_KEY',
        'deepseek': 'DEEPSEEK_API_KEY',
        'meta': 'META_API_KEY',
    }
    
    env_var = key_mapping.get(provider.lower())
    if env_var:
        return os.getenv(env_var)
    return None


def save_config(config: Dict[str, Any], config_path: Optional[Union[str, Path]] = None) -> bool:
    """Save configuration to a JSON file.
    
    Parameters
    ----------
    config : Dict[str, Any]
        Configuration dictionary to save.
    config_path : Optional[Union[str, Path]]
        Path to save the config file. Defaults to 'config.json'.
        
    Returns
    -------
    bool
        True if saved successfully, False otherwise.
    """
    if config_path is None:
        config_path = Path.cwd() / "config.json"
    else:
        config_path = Path(config_path)
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception:
        return False


def load_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load configuration from a JSON file.
    
    Parameters
    ----------
    config_path : Optional[Union[str, Path]]
        Path to the config file. Defaults to 'config.json'.
        
    Returns
    -------
    Dict[str, Any]
        Configuration dictionary. Empty dict if file not found.
    """
    if config_path is None:
        config_path = Path.cwd() / "config.json"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def get_cache_dir() -> Path:
    """Get the cache directory for the utils package.
    
    Returns
    -------
    Path
        Path to the cache directory.
    """
    cache_dir = Path.home() / ".cache" / "utils"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_data_dir() -> Path:
    """Get the data directory for the utils package.
    
    Returns
    -------
    Path
        Path to the data directory.
    """
    data_dir = Path.home() / ".local" / "share" / "utils"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir