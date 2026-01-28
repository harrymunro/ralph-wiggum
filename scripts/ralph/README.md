# V-Ralph

V-Ralph is a Python-based V-Lifecycle Agent that implements autonomous code execution with semantic validation. It replaces the shell-based ralph.sh with a more robust, testable Python implementation.

## Installation

V-Ralph requires Python 3.8 or later.

```bash
# Clone the repository
git clone <repo-url>
cd ralph-wiggum/scripts/ralph

# No additional dependencies required for basic usage
```

## Usage

### Basic Commands

```bash
# Show help and available commands
python v_ralph.py --help

# Show version
python v_ralph.py --version

# Check status of all stories
python v_ralph.py status

# Execute pending stories
python v_ralph.py run
```

### Project Structure

```
scripts/ralph/
├── v_ralph.py        # Main CLI entry point
├── macro_v/          # Macro-V lifecycle components
├── micro_v/          # Micro-V lifecycle components (executor, auditor)
├── shared/           # Common utilities (prd, claude, progress, git)
├── tests/            # Unit and integration tests
├── prd.json          # Project requirements document
├── progress.txt      # Progress tracking log
└── README.md         # This file
```

## Development

### Running Tests

```bash
python -m pytest tests/ -v
```

### Type Checking

```bash
python -m py_compile v_ralph.py
```
