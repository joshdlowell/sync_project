There are several ways to make a Python package runnable. Here are the most common approaches:

## 1. Using `__main__.py` (Recommended)

Create a `__main__.py` file in your package directory. This allows users to run your package with `python -m package_name`.

**Directory structure:**
```
mypackage/
├── __init__.py
├── __main__.py
├── core.py
└── utils.py
```

**Example `__main__.py`:**
```python
# mypackage/__main__.py
from .core import main

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
python -m mypackage
```

## 2. Using setuptools entry points

Define entry points in your `setup.py` or `pyproject.toml` to create console commands.

**setup.py approach:**
```python
from setuptools import setup, find_packages

setup(
    name="mypackage",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "mypackage=mypackage.core:main",
            "mypackage-cli=mypackage.cli:cli_main",
        ],
    },
)
```

**pyproject.toml approach:**
```toml
[project]
name = "mypackage"
version = "0.1.0"

[project.scripts]
mypackage = "mypackage.core:main"
mypackage-cli = "mypackage.cli:cli_main"
```

**Usage after installation:**
```bash
pip install .
mypackage
mypackage-cli
```

## 3. Creating a CLI script

Create a separate script file that imports and runs your package.

**cli.py:**
```python
#!/usr/bin/env python3
from mypackage.core import main

if __name__ == "__main__":
    main()
```

Make it executable:
```bash
chmod +x cli.py
./cli.py
```

## 4. Complete example

Here's a complete example structure:

```
mypackage/
├── __init__.py
├── __main__.py
├── core.py
├── cli.py
└── setup.py
```

**mypackage/__init__.py:**
```python
__version__ = "0.1.0"
```

**mypackage/core.py:**
```python
def main():
    print("Hello from mypackage!")
    print("Package is running successfully!")

def greet(name):
    return f"Hello, {name}!"
```

**mypackage/__main__.py:**
```python
from .core import main

if __name__ == "__main__":
    main()
```

**mypackage/cli.py:**
```python
import argparse
from .core import main, greet

def cli_main():
    parser = argparse.ArgumentParser(description="My Package CLI")
    parser.add_argument("--name", help="Name to greet")
    args = parser.parse_args()
    
    if args.name:
        print(greet(args.name))
    else:
        main()

if __name__ == "__main__":
    cli_main()
```

**setup.py:**
```python
from setuptools import setup, find_packages

setup(
    name="mypackage",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "mypackage=mypackage.core:main",
            "mypackage-cli=mypackage.cli:cli_main",
        ],
    },
)
```

## Usage examples:

```bash
# Run as module
python -m mypackage

# Install and run as command
pip install .
mypackage
mypackage-cli --name "World"

# Run CLI directly
python -m mypackage.cli --name "Python"
```

The `__main__.py` approach is generally recommended as it's the most standard and doesn't require installation to test your package.