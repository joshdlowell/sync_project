# Merkle Tree File Integrity System Documentation
prompt generate a "read the docs" for this file
## Overview

The Merkle Tree File Integrity System is a Python module that implements a cryptographic hash-based file system integrity checker. It creates Merkle trees of directory structures and their contents, enabling efficient detection of file system changes including created, modified, or deleted files.

## Features

- **Recursive Directory Traversal**: Builds complete Merkle trees of directory structures
- **Multi-type File Support**: Handles regular files, directories, symbolic links, and hard links
- **Change Detection**: Identifies Created, Modified, and Deleted files by comparing current state against stored hashes
- **REST API Integration**: Stores and retrieves hash information via REST API
- **Efficient Updates**: Supports partial tree updates when only subdirectories change
- **Cross-platform Compatibility**: Uses pathlib for platform-independent path operations

## Installation

### Prerequisites

- Python 3.8 or higher
- Custom `rest_connector` module (for hash storage/retrieval)

### Dependencies

```python
import hashlib
from time import time
from pathlib import Path
import rest_connector  # Custom module - see REST API Integration
```

## Quick Start

```python
from merkle_integrity import DFS_merkle

# Monitor a directory for changes
root_path = '/home/user/documents'
target_path = '/home/user/documents/project'

# Get hash and detect changes
hash_value, changes = DFS_merkle(root_path, target_path)

if hash_value:
    print(f"Directory hash: {hash_value}")
    print(f"Created files: {changes['Created']}")
    print(f"Modified files: {changes['Modified']}")
    print(f"Deleted files: {changes['Deleted']}")
```

## API Reference

### Main Functions

#### `DFS_merkle(root_path: str, dir_path: str) -> tuple[str, dict] | tuple[None, None]`

**Primary entry point** for hashing a directory tree and detecting changes.

**Parameters:**
- `root_path` (str): Absolute path to the root directory of the monitored file system tree
- `dir_path` (str): Absolute path to the directory to hash (must be within root_path)

**Returns:**
- `tuple[str, dict]`: Hash value and changes dictionary on success
- `tuple[None, None]`: On error (dir_path not within root_path)

**Changes Dictionary Structure:**
```python
{
    'Created': set(),    # Newly created files/directories
    'Modified': set(),   # Modified files/directories  
    'Deleted': set()     # Deleted files/directories
}
```

**Example:**
```python
hash_val, changes = DFS_merkle('/home/user/docs', '/home/user/docs/project')
if hash_val:
    print(f"Project directory hash: {hash_val}")
    for change_type, files in changes.items():
        if files:
            print(f"{change_type}: {files}")
```

#### `recompute_root(root_path: str, dir_path: str, change_dict: dict) -> None`

**Updates parent directory hashes** after child directory changes to maintain Merkle tree integrity.

**Parameters:**
- `root_path` (str): Root directory path (stopping point for updates)
- `dir_path` (str): Directory that was changed
- `change_dict` (dict): Changes dictionary to update in-place

**Usage:**
```python
# Typically called internally by DFS_merkle
# Manual usage for specific scenarios:
recompute_root('/home/user', '/home/user/docs/project', changes)
```

### Utility Functions

#### `get_hash_func()`

Returns the hash function used throughout the module (SHA-1).

**Returns:** `hashlib.sha1` function

#### `perform_hash(hash_string: str) -> str`

Generates a hash of the input string using the configured hash function.

**Parameters:**
- `hash_string` (str): String to hash

**Returns:** Hexadecimal hash string

#### `get_link_hashable(link_path: str) -> str`

Generates a hashable representation of symbolic or hard links.

**Parameters:**
- `link_path` (str): Full path to the link

**Returns:** Formatted string "link_path -> target_path"

## Hash Computation Process

The module follows this process for hash computation:

1. **Directory Traversal**: Recursively walk through directory structure
2. **Subdirectory Hashing**: Hash all subdirectories first (depth-first)
3. **Link Hashing**: Hash symbolic/hard links by their target paths
4. **File Hashing**: Hash file contents in 64KB chunks for memory efficiency
5. **Directory Hash Combination**: Combine all child hashes to create parent hash
6. **Parent Updates**: Update parent directory hashes up to root

### Hash String Format

For directories, the hash is computed from:
```
subdirectory_hash1 + subdirectory_hash2 + ... + 
file_hash1 + file_hash2 + ... + 
link_hash1 + link_hash2 + ...
```

Empty categories are represented as: `{dir_path}/{category}: EMPTY `

## Change Detection

The system detects changes by comparing current hash values against previously stored values:

- **Created**: New files/directories not in previous hash table
- **Modified**: Files/directories with different hash values
- **Deleted**: Files/directories in previous hash table but not found in current scan

## REST API Integration

The module requires a `rest_connector` module with these functions:

```python
# Required rest_connector functions:
def get_hashtable(dir_path: str) -> dict:
    """Get stored hash information for directory"""
    pass

def get_single_hash(item_path: str) -> str:
    """Get stored hash for single item"""
    pass

def put_hashtable(hash_info: dict) -> dict:
    """Store hash information and return detected changes"""
    pass
```

## Error Handling

### Common Exceptions

- **FileNotFoundError**: Directory path doesn't exist
- **PermissionError**: Insufficient permissions to read files/directories
- **OSError**: Issues reading symbolic links or file system errors

### Validation

The module validates that:
- `dir_path` is within `root_path`
- Directories exist and are accessible
- Links can be resolved

## Performance Considerations

### Memory Usage

- Files are read in 64KB chunks to minimize memory usage
- Hash information is processed incrementally
- Large directory trees are handled efficiently

### Optimization Tips

1. **Partial Updates**: Use subdirectory-specific calls when only part of tree changes
2. **Batch Operations**: Process multiple directories in single session
3. **Network Optimization**: Minimize REST API calls by batching hash operations

## Examples

### Basic Directory Monitoring

```python
import os
from merkle_integrity import DFS_merkle

def monitor_directory(root_dir, target_dir):
    """Monitor a directory for changes"""
    try:
        hash_val, changes = DFS_merkle(root_dir, target_dir)
        
        if hash_val is None:
            print("Error: Invalid directory path")
            return
            
        print(f"Directory hash: {hash_val}")
        
        # Report changes
        if any(changes.values()):
            print("Changes detected:")
            for change_type, files in changes.items():
                if files:
                    print(f"  {change_type}: {len(files)} items")
                    for file in sorted(files):
                        print(f"    - {file}")
        else:
            print("No changes detected")
            
    except Exception as e:
        print(f"Error monitoring directory: {e}")

# Usage
monitor_directory('/home/user/docs', '/home/user/docs/project')
```

### Recursive Project Monitoring

```python
def monitor_project_structure(project_root):
    """Monitor entire project structure"""
    changes_summary = {
        'Created': set(),
        'Modified': set(), 
        'Deleted': set()
    }
    
    # Process each subdirectory
    for subdir in os.listdir(project_root):
        subdir_path = os.path.join(project_root, subdir)
        if os.path.isdir(subdir_path):
            hash_val, changes = DFS_merkle(project_root, subdir_path)
            
            if hash_val:
                # Accumulate changes
                for change_type in changes_summary:
                    changes_summary[change_type].update(changes[change_type])
    
    return changes_summary
```

## Best Practices

1. **Regular Monitoring**: Run integrity checks periodically
2. **Incremental Updates**: Process only changed subdirectories when possible
3. **Error Handling**: Always check return values and handle exceptions
4. **Path Validation**: Ensure paths are absolute and within expected boundaries
5. **Performance Monitoring**: Track execution time for large directory trees

## Troubleshooting

### Common Issues

**"Requested path is not a child of the given root_path"**
- Ensure `dir_path` is within `root_path`
- Use absolute paths consistently

**Permission Errors**
- Verify read permissions for all files and directories
- Run with appropriate user privileges

**REST API Connection Issues**
- Verify `rest_connector` module is properly configured
- Check network connectivity and API endpoints

### Debug Tips

1. **Enable Logging**: Add logging statements to track hash computation
2. **Path Validation**: Print and verify all path parameters
3. **Small Test Sets**: Test with small directory structures first
4. **Manual Hash Verification**: Compare computed hashes with expected values

## Version History

- **v1.0** (06/01/2024): Initial implementation
- **v1.1** (06/18/2025): Enhanced error handling and documentation

## Author

**Jdlowel**  
Created: 06/01/2024  
Last Modified: 06/18/2025