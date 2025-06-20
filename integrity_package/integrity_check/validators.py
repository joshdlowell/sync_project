from pathlib import Path


class PathValidator:
    """Validates path operations for integrity checking"""

    def validate_root_and_dir_paths(self, root_path: str, dir_path: str) -> bool:
        """Validate that dir_path is within root_path"""
        try:
            root = Path(root_path).resolve()
            target = Path(dir_path).resolve()
            return str(target).startswith(str(root))
        except (OSError, ValueError):
            return False

    def validate_path_exists(self, path: str) -> bool:
        """Validate that path exists"""
        return Path(path).exists()
