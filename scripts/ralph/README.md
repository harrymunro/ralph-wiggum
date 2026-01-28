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

## Three-Layer Validation Model

V-Ralph implements a rigorous three-layer validation approach to ensure code quality:

### Layer 1: Coder Implementation
The coding agent implements the user story according to the acceptance criteria. It writes code, updates documentation, and follows project patterns.

### Layer 2: Automated Validation
After implementation, automated checks run:
- Type checking (e.g., `python -m py_compile`)
- Linting (e.g., `npm run lint`)
- Test suite (e.g., `pytest`)

A green build is necessary but not sufficient - it proves the code runs, not that it's correct.

### Layer 3: Semantic Audit
A separate, stateless Claude instance reviews the implementation as an adversarial QA engineer. The auditor:
- Only sees the spec and the diff (no context from the coding session)
- Checks if the implementation satisfies the **spirit** of the spec, not just the letter
- Looks for edge cases, unstated assumptions, and quality red flags
- Returns one of three verdicts:
  - **PASS** - Implementation is correct, proceed to commit
  - **RETRY** - Found fixable issues, loop back to coder with feedback
  - **ESCALATE** - Spec ambiguity requires human input, stop the loop

This three-layer approach catches "green build hallucinations" where code compiles and tests pass but doesn't actually solve the problem.

## Prompt Customization

V-Ralph uses template-based prompts that can be customized for different project needs.

### Prompt Templates

Prompt templates are located in `micro_v/prompts/`:

- **`coder.md`** - Instructions for the coding agent that implements user stories
- **`auditor.md`** - Instructions for the semantic auditor that reviews implementations

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
