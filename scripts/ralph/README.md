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

### Run Command

The `run` command executes pending user stories autonomously.

```bash
# Execute all pending stories
python v_ralph.py run

# Execute with custom retry limit
python v_ralph.py run --max-retries 3

# Execute a specific story only
python v_ralph.py run --story US-003

# Preview what would run without executing
python v_ralph.py run --dry-run

# Specify custom PRD and progress file paths
python v_ralph.py run --prd /path/to/prd.json --progress /path/to/progress.txt
```

**Flags:**

| Flag | Description |
|------|-------------|
| `--prd PATH` | Path to prd.json or prd.yml file (default: prd.json in current directory) |
| `--progress PATH` | Path to progress.txt file (default: progress.txt in current directory) |
| `--max-retries N` | Maximum retry attempts per story (default: 5) |
| `--story US-XXX` | Run only the specified story ID |
| `--dry-run` | Show what would run without executing |

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | All requested stories completed successfully (or nothing to run) |
| 1 | Error (file not found, invalid story ID, etc.) |
| 2 | Story escalated (requires human input) |

**Behavior:**

- On **success**: Commits changes, updates prd.json to mark story as passed, appends entry to progress.txt
- On **escalation**: Stops execution immediately, displays reason, exits with code 2
- On **circuit breaker** (max retries exceeded): Logs failure, moves to next pending story

### Status Command

The `status` command displays the current state of all user stories in a formatted table.

```bash
# Show status of all stories (reads prd.json from current directory)
python v_ralph.py status

# Specify a custom PRD file path
python v_ralph.py status --prd /path/to/prd.json
```

**Output includes:**
- Project name and branch name from the PRD
- Table with columns: ID, Title, Status (pass/fail/escalated), Attempts
- Progress summary showing X/Y stories complete

**Example output:**
```
Project: V-Ralph
Branch: ralph/v-ralph

ID      Title                                      Status     Attempts
----------------------------------------------------------------------
US-001  Project scaffolding and CLI entry point    pass       0
US-002  prd.yml read/write module                  pass       0
US-003  Claude CLI wrapper                         fail       2

Progress: 2/3 stories complete
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

## Planning with V-Ralph

V-Ralph includes a Claude Code skill for interactive spec refinement that produces machine-verifiable specifications.

### Invoking the Planning Skill

In Claude Code, use the `/v-ralph-planning` command or say "create v-ralph spec" to start planning:

```
/v-ralph-planning
```

Or trigger it naturally:
- "v-ralph planning for my new feature"
- "create v-ralph spec"
- "plan for ralph"
- "verifiable spec"

### What the Planning Skill Does

1. **Gathers requirements** through clarifying questions with lettered options for quick responses
2. **Enforces verifiability** - every acceptance criterion must have a corresponding verification command
3. **Requires mandatory elements**:
   - Files whitelist for every story (prevents scope creep)
   - README update criterion (keeps docs in sync)
   - Typecheck/test pass criteria (quality gates)
4. **Outputs valid prd.yml** ready for `v_ralph.py run`

### Verifiable Criteria Examples

The skill enforces machine-verifiable criteria:

| Bad (Vague) | Good (Verifiable) |
|-------------|-------------------|
| "Works correctly" | "Returns 200 status for valid input" |
| "Good error handling" | "Raises ValueError with message 'Invalid ID'" |
| "Proper testing" | "tests/test_feature.py exists and passes" |

### Skill Location

The planning skill is at `.claude/skills/v-ralph-planning/SKILL.md` and can be customized for project-specific needs.

## Development

### Running Tests

```bash
python -m pytest tests/ -v
```

### Type Checking

```bash
python -m py_compile v_ralph.py
```
