# Merkle Tree File Integrity System

A Python-based file system integrity checker that uses Merkle tree data structures to create cryptographic fingerprints of directory hierarchies and detect changes in real-time.

## Overview

This system recursively traverses directory structures, computes SHA-1 hashes for all files, directories, and links, then builds a Merkle tree to create tamper-evident snapshots of your file system. It can efficiently detect when files are created, modified, or deleted by comparing current states against previously stored hash values.

## Key Features

- **Merkle Tree Architecture**: Creates hierarchical hash structures where parent directory hashes depend on all child content
- **Comprehensive Coverage**: Handles regular files, directories, symbolic links, and hard links
- **Change Detection**: Automatically identifies created, modified, and deleted files
- **Efficient Updates**: Only recomputes necessary portions of the tree when changes occur
- **REST API Integration**: Stores and retrieves hash data via REST endpoints for persistence
- **Cross-Platform**: Uses pathlib for platform-independent path operations

## Installation

### Prerequisites

- Python 3.8+
- `rest_connector` module (custom dependency for hash storage)
- Standard library modules: `hashlib`, `pathlib`, `time`

### Setup

```bash
# Clone or download the module
# Ensure rest_connector module is available in your Python path
```

## Usage

### Basic Usage

```python
from merkle_file_integrity import DFS_merkle

# Hash a directory and detect changes
root_path = "/home/user/documents"
target_dir = "/home/user/documents/project"

dir_hash, changes = DFS_merkle(root_path, target_dir)

if dir_hash:
    print(f"Directory hash: {dir_hash}")
    print(f"Created files: {changes['Created']}")
    print(f"Modified files: {changes['Modified']}")
    print(f"Deleted files: {changes['Deleted']}")
else:
    print("Error: Target directory not within root path")
```

### Monitoring File System Changes

```python
import time
from merkle_file_integrity import DFS_merkle

def monitor_directory(root_path, check_interval=60):
    """Monitor a directory for changes every 60 seconds"""
    while True:
        hash_val, changes = DFS_merkle(root_path, root_path)
        
        if any(changes.values()):
            print(f"Changes detected at {time.ctime()}:")
            for change_type, files in changes.items():
                if files:
                    print(f"  {change_type}: {len(files)} files")
                    for file in list(files)[:5]:  # Show first 5
                        print(f"    {file}")
        
        time.sleep(check_interval)

# Monitor your documents folder
monitor_directory("/home/user/documents")
```

## API Reference

### Main Functions

#### `DFS_merkle(root_path: str, dir_path: str) -> tuple[str, dict] | tuple[None, None]`

Primary entry point for hashing a directory tree and detecting changes.

**Parameters:**
- `root_path`: Absolute path to the root directory (monitoring boundary)
- `dir_path`: Absolute path to the directory to hash (must be within root_path)

**Returns:**
- `tuple[str, dict]`: Directory hash and changes dictionary on success
- `tuple[None, None]`: On error (invalid paths)

**Changes Dictionary Structure:**
```python
{
    'Created': set(),   # Newly created files
    'Modified': set(),  # Changed files
    'Deleted': set()    # Removed files
}
```

#### `recompute_root(root_path: str, dir_path: str, change_dict: dict) -> None`

Updates parent directory hashes after a child directory changes.

**Parameters:**
- `root_path`: Root boundary for hash updates
- `dir_path`: Changed directory path
- `change_dict`: Changes dictionary to update in-place

### Utility Functions

#### `get_hash_func()`
Returns the SHA-1 hash function used throughout the module.

#### `perform_hash(hash_string: str) -> str`
Generates SHA-1 hash of input string.

#### `get_link_hashable(link_path: str) -> str`
Creates hashable representation of symbolic/hard links.

## How It Works

### Merkle Tree Construction

1. **File Hashing**: Each file is read in 64KB chunks and hashed with SHA-1
2. **Link Hashing**: Symbolic and hard links are hashed based on their target paths
3. **Directory Hashing**: Each directory's hash is computed from its contents:
   - Subdirectory hashes (recursive)
   - File hashes
   - Link hashes
4. **Tree Building**: Parent directories depend on all child hashes, creating tamper-evident structure

### Change Detection

The system compares current hash values against previously stored values to identify:
- **Created**: New files/directories that didn't exist before
- **Modified**: Existing files with different hash values
- **Deleted**: Previously tracked files that no longer exist

### Hash Propagation

When a file changes:
1. Its hash is updated
2. Parent directory hash is recalculated
3. Changes propagate up to the root directory
4. Only affected portions of the tree are recomputed

## Examples

### Check Single Directory

```python
from merkle_file_integrity import DFS_merkle

# Check a specific project folder
hash_val, changes = DFS_merkle(
    root_path="/home/user/projects",
    dir_path="/home/user/projects/myapp"
)

if changes['Modified']:
    print("Modified files detected:")
    for file_path in changes['Modified']:
        print(f"  {file_path}")
```

### Recursive Monitoring Script

```python
#!/usr/bin/env python3
import sys
from merkle_file_integrity import DFS_merkle

def audit_directory(path):
    """Perform integrity audit of directory"""
    hash_val, changes = DFS_merkle(path, path)
    
    total_changes = sum(len(files) for files in changes.values())
    
    if total_changes == 0:
        print(f"✓ No changes detected in {path}")
        return True
    else:
        print(f"⚠ {total_changes} changes detected in {path}")
        for change_type, files in changes.items():
            if files:
                print(f"  {change_type}: {len(files)} files")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python audit.py <directory_path>")
        sys.exit(1)
    
    directory = sys.argv[1]
    is_clean = audit_directory(directory)
    sys.exit(0 if is_clean else 1)
```

## Configuration

### Hash Function

The system uses SHA-1 by default for performance. To change the hash function:

```python
# Modify get_hash_func() in the module
def get_hash_func():
    return hashlib.sha256  # Use SHA-256 instead
```

### Chunk Size

File reading chunk size is set to 64KB. Modify in `_DFS_merkle()`:

```python
data = f.read(65536)  # Change to desired chunk size
```

## Error Handling

Common exceptions and solutions:

- **FileNotFoundError**: Directory doesn't exist
- **PermissionError**: Insufficient read permissions
- **OSError**: System-level file access issues

```python
try:
    hash_val, changes = DFS_merkle(root_path, dir_path)
except PermissionError:
    print("Permission denied accessing directory")
except FileNotFoundError:
    print("Directory not found")
```

## Performance Considerations

- **Large Files**: 64KB chunk reading minimizes memory usage
- **Deep Hierarchies**: Recursive design handles arbitrary directory depth
- **Partial Updates**: Only changed subtrees are recalculated
- **Storage**: Hash data is persisted via REST API (external storage required)

## Dependencies

- **rest_connector**: Custom module for hash persistence (implementation required)
- **hashlib**: SHA-1 cryptographic hashing
- **pathlib**: Cross-platform path operations
- **time**: Timestamp generation

## Limitations

- Requires `rest_connector` module implementation
- SHA-1 is not cryptographically secure (suitable for integrity checking only)
- Performance scales with directory size and depth
- Requires read access to all monitored files

## Contributing

When contributing to this module:

1. Maintain backward compatibility with existing APIs
2. Add comprehensive docstrings for new functions
3. Update this README for new features
4. Consider performance impact of changes

## License

Please refer to your project's license file for usage terms.

## Version History

- **v1.0** (06/01/2024): Initial implementation
- **v1.1** (06/18/2025): Enhanced documentation and error handling

## Author

**Jdlowel**  
Created: 06/01/2024  
Last Modified: 06/18/2025