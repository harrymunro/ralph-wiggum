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

## Prompt Customization

V-Ralph uses template-based prompts that can be customized for different project needs.

### Prompt Templates

Prompt templates are located in `micro_v/prompts/`:

- **`coder.md`** - Instructions for the coding agent that implements user stories

### Template Placeholders

The coder prompt supports the following placeholders that are automatically filled at runtime:

| Placeholder | Description |
|-------------|-------------|
| `{{goal}}` | The user story title and description |
| `{{files}}` | Whitelist of files the agent may edit |
| `{{criteria}}` | The acceptance criteria to satisfy |
| `{{learnings}}` | Relevant patterns and learnings from progress.txt |

### Customizing Prompts

To customize the coder behavior:

1. Edit `micro_v/prompts/coder.md`
2. Keep all four placeholders (`{{goal}}`, `{{files}}`, `{{criteria}}`, `{{learnings}}`)
3. Modify the rules and guidelines sections as needed

**Important**: Do not remove the forbidden shortcuts section - it prevents agents from using quality-bypassing hacks.

## Development

### Running Tests

```bash
python -m pytest tests/ -v
```

### Type Checking

```bash
python -m py_compile v_ralph.py
```
