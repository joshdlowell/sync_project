import hashlib
import stat
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from .configuration import config
from .interfaces import FileSystemInterface, HashStorageInterface, HashFunction


class StandardFileSystem(FileSystemInterface):
    """Standard file system implementation using pathlib"""

    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def is_file(self, path: str) -> bool:
        return Path(path).is_file()

    def is_dir(self, path: str) -> bool:
        return Path(path).is_dir()

    def is_link(self, path: str) -> bool:
        """Check if path is a symbolic link"""
        return Path(path).is_symlink()

    def is_readable_file(self, path: str) -> bool:
        """Check if path is a readable regular file (not a special file)"""
        path_obj = Path(path)

        # Must be a file and not a symlink
        if not path_obj.is_file() or path_obj.is_symlink():
            return False

        try:
            # Check if it's a special file using stat
            file_stat = path_obj.stat()

            # Check if it's a regular file (not socket, FIFO, device, etc.)
            return stat.S_ISREG(file_stat.st_mode)
        except (OSError, PermissionError):
            return False

    def get_file_metadata(self, path: str) -> Dict[str, Any]:
        """Get file metadata including type, mode, size, etc."""
        path_obj = Path(path)

        try:
            file_stat = path_obj.lstat()  # Use lstat to not follow symlinks

            # Determine file type
            file_type = 'unknown'
            if stat.S_ISREG(file_stat.st_mode):
                file_type = 'regular'
            elif stat.S_ISDIR(file_stat.st_mode):
                file_type = 'directory'
            elif stat.S_ISLNK(file_stat.st_mode):
                file_type = 'symlink'
            elif stat.S_ISSOCK(file_stat.st_mode):
                file_type = 'socket'
            elif stat.S_ISFIFO(file_stat.st_mode):
                file_type = 'fifo'
            elif stat.S_ISCHR(file_stat.st_mode):
                file_type = 'char_device'
            elif stat.S_ISBLK(file_stat.st_mode):
                file_type = 'block_device'

            return {
                'type': file_type,
                'mode': file_stat.st_mode,
                'size': file_stat.st_size,
                'uid': file_stat.st_uid,
                'gid': file_stat.st_gid,
                'mtime': file_stat.st_mtime,
                'ctime': file_stat.st_ctime,
                'inode': file_stat.st_ino,
                'device': file_stat.st_dev
            }
        except (OSError, PermissionError) as e:
            config.logger.warning(f"Failed to get metadata for {path}: {e}")
            return {'type': 'unknown', 'error': str(e)}

    def walk(self, path: str) -> List[Tuple[str | None, list[str] | None, list[str] | None]]:
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                raise OSError(f"Path does not exist: {path}")

            # Convert generator to list
            return list(path_obj.walk())
        except OSError as e:
            config.logger.error(f"Failed to walk path {path}: {e}")
            return [(None, None, None)]

    def read_file_chunks(self, path: str, chunk_size: int = 65536):
        with open(path, 'rb') as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                yield data

    def readlink(self, path: str) -> str:
        return str(Path(path).readlink())


class RestHashStorage(HashStorageInterface):
    """Hash storage implementation using REST connector"""
    def __init__(self, rest_processor):
        self.rest_processor = rest_processor

    def put_hashtable(self, hash_info: Dict[str, Any]) -> int:
        return self.rest_processor.put_hashtable(hash_info)

    def get_hashtable(self, path: str) -> Optional[Dict[str, Any]]:
        return self.rest_processor.get_hashtable(path)

    def get_single_hash(self, path: str) -> Optional[str]:
        return self.rest_processor.get_single_hash(path)

    def get_oldest_updates(self, percent: int = 10) -> list[str]:
        return self.rest_processor.get_oldest_updates(config.get('root_path'), percent)

    def get_priority_updates(self) -> list[str] | None:
        return self.rest_processor.get_priority_updates()

    def get_health(self) -> dict | None:
        return self.rest_processor.get_health()

    def put_log(self, message: str, detailed_message: str=None, log_level: str=None, session_id: str=None) -> int:
        return self.rest_processor.put_log(message=message, detailed_message=detailed_message, log_level=log_level, session_id=session_id)


class SHA256HashFunction(HashFunction):
    """SHA-256 hash function implementation"""

    def create_hasher(self):
        return hashlib.sha256()

    def hash_string(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()


class SHA1HashFunction(HashFunction):
    """SHA-1 hash function implementation"""

    def create_hasher(self):
        return hashlib.sha1()

    def hash_string(self, data: str) -> str:
        return hashlib.sha1(data.encode()).hexdigest()
