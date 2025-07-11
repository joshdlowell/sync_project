from pathlib import Path

from .configuration import logger


class PathValidator:
    """Validates path operations for integrity checking"""

    def validate_root_and_dir_paths(self, root_path: str, dir_path: str) -> bool:
        """Validate that dir_path is within root_path"""
        try:
            root = Path(root_path)
            target = Path(dir_path)

            return str(target).startswith(str(root))
        except (OSError, ValueError):
            logger.error(f"Failed to validate root and dir paths: {root_path} {dir_path}")
            return False

    def validate_path_exists(self, path: str) -> bool:
        """Validate that path exists"""
        return Path(path).exists()
