"""PlantUML diagram rendering functionality."""

import base64
import json
import zlib
from pathlib import Path
from typing import Optional, Union
from urllib.parse import quote

from .logging import get_logger
from .settings import PlantUML

logger = get_logger()


def encode_plantuml(plantuml_text: str) -> str:
    """Encode PlantUML text for URL embedding.
    
    Parameters
    ----------
    plantuml_text : str
        The PlantUML diagram text.
        
    Returns
    -------
    str
        The encoded string for use in PlantUML URLs.
    """
    # PlantUML URL encoding process:
    # 1. UTF-8 encode
    # 2. Compress with deflate
    # 3. Base64 encode
    # 4. Replace characters for URL safety
    
    utf8_bytes = plantuml_text.encode('utf-8')
    compressed = zlib.compress(utf8_bytes, 9)[2:-4]  # Remove zlib header/footer
    encoded = base64.b64encode(compressed).decode('ascii')
    
    # Character replacements for PlantUML URL encoding
    encoded = encoded.replace('+', '-')
    encoded = encoded.replace('/', '_')
    
    return encoded


def decode_plantuml(encoded_text: str) -> str:
    """Decode PlantUML encoded text.
    
    Parameters
    ----------
    encoded_text : str
        The encoded PlantUML string.
        
    Returns
    -------
    str
        The decoded PlantUML text.
    """
    # Reverse the encoding process
    encoded_text = encoded_text.replace('-', '+')
    encoded_text = encoded_text.replace('_', '/')
    
    # Add padding if needed
    padding = 4 - len(encoded_text) % 4
    if padding != 4:
        encoded_text += '=' * padding
    
    compressed = base64.b64decode(encoded_text)
    
    # Add zlib header/footer
    zlib_data = b'\x78\x9c' + compressed + b'\x00\x00\x00\x00\x00\x00\x00\x00'
    
    utf8_bytes = zlib.decompress(zlib_data)
    return utf8_bytes.decode('utf-8')


def generate_plantuml_url(
    plantuml_text: str, 
    server: str = "http://www.plantuml.com/plantuml",
    format: str = "svg"
) -> str:
    """Generate a PlantUML server URL for a diagram.
    
    Parameters
    ----------
    plantuml_text : str
        The PlantUML diagram text.
    server : str, optional
        The PlantUML server URL.
    format : str, optional
        The output format (svg, png, eps, emap, etc.).
        
    Returns
    -------
    str
        The complete URL for the diagram.
    """
    encoded = encode_plantuml(plantuml_text)
    return f"{server}/{format}/{encoded}"


def render_plantuml_diagram(
    plantuml_text: str,
    output_path: Optional[Union[str, Path]] = None,
    format: str = "svg",
    server: str = "http://www.plantuml.com/plantuml"
) -> str:
    """Render a PlantUML diagram and optionally save to file.
    
    Parameters
    ----------
    plantuml_text : str
        The PlantUML diagram text.
    output_path : Union[str, Path], optional
        Path to save the rendered diagram. If None, returns the URL.
    format : str, optional
        The output format (svg, png, eps, emap, etc.).
    server : str, optional
        The PlantUML server URL.
        
    Returns
    -------
    str
        Either the URL to the diagram or the path to the saved file.
    """
    url = generate_plantuml_url(plantuml_text, server, format)
    
    if output_path is None:
        return url
    
    # Download and save the diagram
    try:
        import urllib.request
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        urllib.request.urlretrieve(url, output_file)
        logger.info(f"PlantUML diagram saved to {output_file}")
        return str(output_file)
        
    except Exception as e:
        logger.error(f"Failed to download PlantUML diagram: {e}")
        return url


def create_plantuml_object(plantuml_text: str) -> PlantUML:
    """Create a PlantUML object for display in Jupyter notebooks.
    
    Parameters
    ----------
    plantuml_text : str
        The PlantUML diagram text.
        
    Returns
    -------
    PlantUML
        A PlantUML object that can be displayed in notebooks.
    """
    return PlantUML(plantuml_text)


def validate_plantuml_syntax(plantuml_text: str) -> tuple[bool, Optional[str]]:
    """Validate PlantUML syntax (basic validation).
    
    Parameters
    ----------
    plantuml_text : str
        The PlantUML diagram text to validate.
        
    Returns
    -------
    tuple[bool, Optional[str]]
        A tuple of (is_valid, error_message).
    """
    text = plantuml_text.strip()
    
    if not text:
        return False, "Empty PlantUML text"
    
    # Check for required @startuml/@enduml tags
    if not text.startswith('@startuml') and not text.startswith('@startmindmap') and not text.startswith('@startgantt'):
        return False, "PlantUML diagram must start with @startuml, @startmindmap, or @startgantt"
    
    if not text.endswith('@enduml') and not text.endswith('@endmindmap') and not text.endswith('@endgantt'):
        return False, "PlantUML diagram must end with @enduml, @endmindmap, or @endgantt"
    
    # Check for balanced parentheses/brackets
    brackets = {'(': ')', '[': ']', '{': '}'}
    stack = []
    
    for char in text:
        if char in brackets:
            stack.append(brackets[char])
        elif char in brackets.values():
            if not stack or stack.pop() != char:
                return False, "Unbalanced parentheses, brackets, or braces"
    
    if stack:
        return False, "Unbalanced parentheses, brackets, or braces"
    
    return True, None


def plantuml_to_json(plantuml_text: str) -> dict:
    """Convert PlantUML text to a JSON representation.
    
    This is a simple parser that extracts basic information from PlantUML diagrams.
    
    Parameters
    ----------
    plantuml_text : str
        The PlantUML diagram text.
        
    Returns
    -------
    dict
        A JSON representation of the diagram structure.
    """
    lines = plantuml_text.strip().split('\n')
    
    result = {
        "type": "unknown",
        "title": None,
        "elements": [],
        "relationships": [],
        "styling": []
    }
    
    # Detect diagram type
    first_line = lines[0].strip().lower()
    if first_line.startswith('@startuml'):
        result["type"] = "uml"
    elif first_line.startswith('@startmindmap'):
        result["type"] = "mindmap"
    elif first_line.startswith('@startgantt'):
        result["type"] = "gantt"
    
    for line in lines[1:-1]:  # Skip start/end tags
        line = line.strip()
        if not line or line.startswith("'"):  # Skip empty lines and comments
            continue
        
        # Extract title
        if line.lower().startswith('title '):
            result["title"] = line[6:].strip()
        
        # Extract class/entity definitions
        elif line.startswith('class ') or line.startswith('entity '):
            parts = line.split()
            if len(parts) >= 2:
                result["elements"].append({
                    "type": parts[0],
                    "name": parts[1],
                    "definition": line
                })
        
        # Extract relationships (basic)
        elif '-->' in line or '<--' in line or '--|>' in line:
            result["relationships"].append({
                "definition": line,
                "type": "relationship"
            })
        
        # Extract styling
        elif 'skinparam' in line.lower() or line.startswith('!'):
            result["styling"].append(line)
    
    return result


def json_to_plantuml(json_data: dict) -> str:
    """Convert a JSON representation back to PlantUML text.
    
    Parameters
    ----------
    json_data : dict
        The JSON representation of a PlantUML diagram.
        
    Returns
    -------
    str
        The PlantUML diagram text.
    """
    diagram_type = json_data.get("type", "uml")
    
    # Start tag
    if diagram_type == "mindmap":
        lines = ["@startmindmap"]
    elif diagram_type == "gantt":
        lines = ["@startgantt"]
    else:
        lines = ["@startuml"]
    
    # Title
    if json_data.get("title"):
        lines.append(f"title {json_data['title']}")
        lines.append("")
    
    # Styling
    for style in json_data.get("styling", []):
        lines.append(style)
    
    if json_data.get("styling"):
        lines.append("")
    
    # Elements
    for element in json_data.get("elements", []):
        lines.append(element["definition"])
    
    if json_data.get("elements"):
        lines.append("")
    
    # Relationships
    for relationship in json_data.get("relationships", []):
        lines.append(relationship["definition"])
    
    # End tag
    if diagram_type == "mindmap":
        lines.append("@endmindmap")
    elif diagram_type == "gantt":
        lines.append("@endgantt")
    else:
        lines.append("@enduml")
    
    return '\n'.join(lines)


def save_plantuml_diagram(
    plantuml_text: str,
    filename: str,
    output_dir: Optional[Union[str, Path]] = None
) -> Path:
    """Save a PlantUML diagram to a file.
    
    Parameters
    ----------
    plantuml_text : str
        The PlantUML diagram text.
    filename : str
        The filename (without extension).
    output_dir : Union[str, Path], optional
        The output directory. Defaults to current directory.
        
    Returns
    -------
    Path
        The path to the saved file.
    """
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{filename}.puml"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(plantuml_text)
    
    logger.info(f"PlantUML diagram saved to {output_file}")
    return output_file


def load_plantuml_diagram(file_path: Union[str, Path]) -> str:
    """Load a PlantUML diagram from a file.
    
    Parameters
    ----------
    file_path : Union[str, Path]
        Path to the PlantUML file.
        
    Returns
    -------
    str
        The PlantUML diagram text.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"PlantUML file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


__all__ = [
    "encode_plantuml",
    "decode_plantuml",
    "generate_plantuml_url",
    "render_plantuml_diagram",
    "create_plantuml_object",
    "validate_plantuml_syntax",
    "plantuml_to_json",
    "json_to_plantuml",
    "save_plantuml_diagram",
    "load_plantuml_diagram",
]