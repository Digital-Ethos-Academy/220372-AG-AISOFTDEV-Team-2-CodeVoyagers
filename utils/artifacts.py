"""Artifacts handling for saving and managing generated content."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime
import hashlib

from .logging import get_logger
from .helpers import sanitize_filename

logger = get_logger()


class Artifact:
    """Represents a generated artifact (code, image, document, etc.)."""
    
    def __init__(
        self,
        content: Any,
        artifact_type: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize an Artifact.
        
        Parameters
        ----------
        content : Any
            The content of the artifact.
        artifact_type : str
            The type of artifact (code, image, text, json, etc.).
        name : str, optional
            Name of the artifact.
        description : str, optional
            Description of the artifact.
        metadata : Dict[str, Any], optional
            Additional metadata for the artifact.
        """
        self.content = content
        self.artifact_type = artifact_type
        self.name = name or f"artifact_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.description = description
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate a unique ID for the artifact."""
        content_str = str(self.content)[:1000]  # First 1000 chars
        timestamp = self.created_at.isoformat()
        hash_input = f"{content_str}{timestamp}{self.name}".encode('utf-8')
        return hashlib.md5(hash_input).hexdigest()[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert artifact to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.artifact_type,
            "description": self.description,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Artifact':
        """Create artifact from dictionary representation."""
        artifact = cls(
            content=data["content"],
            artifact_type=data["type"],
            name=data["name"],
            description=data.get("description"),
            metadata=data.get("metadata", {})
        )
        artifact.id = data["id"]
        artifact.created_at = datetime.fromisoformat(data["created_at"])
        return artifact


class ArtifactManager:
    """Manages saving and loading of artifacts."""
    
    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """Initialize ArtifactManager.
        
        Parameters
        ----------
        base_path : Union[str, Path], optional
            Base directory for saving artifacts. Defaults to ./artifacts/
        """
        if base_path is None:
            base_path = Path.cwd() / "artifacts"
        
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for different artifact types
        self.subdirs = {
            "code": self.base_path / "code",
            "images": self.base_path / "images",
            "documents": self.base_path / "documents",
            "data": self.base_path / "data",
            "other": self.base_path / "other"
        }
        
        for subdir in self.subdirs.values():
            subdir.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.base_path / "index.json"
        self._artifacts = self._load_index()
    
    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """Load the artifact index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                logger.warning(f"Could not load artifact index from {self.index_file}")
        return {}
    
    def _save_index(self) -> None:
        """Save the artifact index to disk."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self._artifacts, f, indent=2)
        except IOError:
            logger.error(f"Could not save artifact index to {self.index_file}")
    
    def _get_subdir(self, artifact_type: str) -> Path:
        """Get the appropriate subdirectory for an artifact type."""
        type_mapping = {
            "python": "code",
            "javascript": "code",
            "typescript": "code",
            "html": "code",
            "css": "code",
            "json": "data",
            "csv": "data",
            "txt": "documents",
            "md": "documents",
            "markdown": "documents",
            "image": "images",
            "png": "images",
            "jpg": "images",
            "jpeg": "images",
            "gif": "images",
            "svg": "images"
        }
        
        category = type_mapping.get(artifact_type.lower(), "other")
        return self.subdirs[category]
    
    def save_artifact(
        self,
        content: Any,
        artifact_type: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        overwrite: bool = False
    ) -> Artifact:
        """Save an artifact to disk.
        
        Parameters
        ----------
        content : Any
            The content to save.
        artifact_type : str
            The type of artifact.
        name : str, optional
            Name for the artifact.
        description : str, optional
            Description of the artifact.
        metadata : Dict[str, Any], optional
            Additional metadata.
        overwrite : bool, optional
            Whether to overwrite existing files.
            
        Returns
        -------
        Artifact
            The created artifact object.
        """
        artifact = Artifact(content, artifact_type, name, description, metadata)
        
        # Determine file extension based on type
        extension_map = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "html": ".html",
            "css": ".css",
            "json": ".json",
            "csv": ".csv",
            "txt": ".txt",
            "md": ".md",
            "markdown": ".md",
            "png": ".png",
            "jpg": ".jpg",
            "jpeg": ".jpeg",
            "gif": ".gif",
            "svg": ".svg"
        }
        
        extension = extension_map.get(artifact_type.lower(), ".txt")
        safe_name = sanitize_filename(artifact.name)
        
        # Handle different content types
        subdir = self._get_subdir(artifact_type)
        file_path = subdir / f"{safe_name}{extension}"
        
        # Avoid overwriting unless explicitly allowed
        if file_path.exists() and not overwrite:
            counter = 1
            stem = file_path.stem
            while file_path.exists():
                file_path = subdir / f"{stem}_{counter}{extension}"
                counter += 1
            artifact.name = file_path.stem
        
        try:
            if artifact_type.lower() in ["png", "jpg", "jpeg", "gif"] and isinstance(content, str):
                # Handle base64 encoded images
                import base64
                with open(file_path, 'wb') as f:
                    # Remove data URL prefix if present
                    if content.startswith('data:'):
                        content = content.split(',', 1)[1]
                    f.write(base64.b64decode(content))
            else:
                # Handle text content
                with open(file_path, 'w', encoding='utf-8') as f:
                    if isinstance(content, (dict, list)):
                        json.dump(content, f, indent=2)
                    else:
                        f.write(str(content))
            
            # Update metadata with file path
            artifact.metadata["file_path"] = str(file_path)
            
            # Add to index
            self._artifacts[artifact.id] = artifact.to_dict()
            self._save_index()
            
            logger.info(f"Saved artifact '{artifact.name}' to {file_path}")
            return artifact
            
        except Exception as e:
            logger.error(f"Failed to save artifact '{artifact.name}': {e}")
            raise
    
    def load_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Load an artifact by ID.
        
        Parameters
        ----------
        artifact_id : str
            The ID of the artifact to load.
            
        Returns
        -------
        Optional[Artifact]
            The loaded artifact, or None if not found.
        """
        if artifact_id not in self._artifacts:
            return None
        
        try:
            artifact_data = self._artifacts[artifact_id]
            return Artifact.from_dict(artifact_data)
        except Exception as e:
            logger.error(f"Failed to load artifact {artifact_id}: {e}")
            return None
    
    def list_artifacts(self, artifact_type: Optional[str] = None) -> list:
        """List all artifacts, optionally filtered by type.
        
        Parameters
        ----------
        artifact_type : str, optional
            Filter by artifact type.
            
        Returns
        -------
        list
            List of artifact dictionaries.
        """
        artifacts = list(self._artifacts.values())
        
        if artifact_type:
            artifacts = [a for a in artifacts if a["type"] == artifact_type]
        
        # Sort by creation date (newest first)
        artifacts.sort(key=lambda x: x["created_at"], reverse=True)
        return artifacts
    
    def delete_artifact(self, artifact_id: str) -> bool:
        """Delete an artifact.
        
        Parameters
        ----------
        artifact_id : str
            The ID of the artifact to delete.
            
        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        if artifact_id not in self._artifacts:
            return False
        
        try:
            artifact_data = self._artifacts[artifact_id]
            file_path = artifact_data.get("metadata", {}).get("file_path")
            
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            
            del self._artifacts[artifact_id]
            self._save_index()
            
            logger.info(f"Deleted artifact {artifact_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete artifact {artifact_id}: {e}")
            return False


# Global artifact manager instance
_artifact_manager = None


def get_artifact_manager() -> ArtifactManager:
    """Get the global artifact manager instance."""
    global _artifact_manager
    if _artifact_manager is None:
        _artifact_manager = ArtifactManager()
    return _artifact_manager


def save_artifact(
    content: Any,
    artifact_type: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    overwrite: bool = False
) -> Artifact:
    """Save an artifact using the global artifact manager.
    
    This is a convenience function that uses the global ArtifactManager instance.
    
    Parameters
    ----------
    content : Any
        The content to save.
    artifact_type : str
        The type of artifact.
    name : str, optional
        Name for the artifact.
    description : str, optional
        Description of the artifact.
    metadata : Dict[str, Any], optional
        Additional metadata.
    overwrite : bool, optional
        Whether to overwrite existing files.
        
    Returns
    -------
    Artifact
        The created artifact object.
    """
    manager = get_artifact_manager()
    return manager.save_artifact(content, artifact_type, name, description, metadata, overwrite)


def load_artifact(artifact_id: str) -> Optional[Artifact]:
    """Load an artifact by ID using the global artifact manager."""
    manager = get_artifact_manager()
    return manager.load_artifact(artifact_id)


def list_artifacts(artifact_type: Optional[str] = None) -> list:
    """List artifacts using the global artifact manager."""
    manager = get_artifact_manager()
    return manager.list_artifacts(artifact_type)


def delete_artifact(artifact_id: str) -> bool:
    """Delete an artifact using the global artifact manager."""
    manager = get_artifact_manager()
    return manager.delete_artifact(artifact_id)


__all__ = [
    "Artifact",
    "ArtifactManager",
    "get_artifact_manager",
    "save_artifact",
    "load_artifact",
    "list_artifacts",
    "delete_artifact",
]