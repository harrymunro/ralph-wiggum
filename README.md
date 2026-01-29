<div align="center">

# Ralph Wiggum

**An autonomous AI agent loop for Claude Code that runs until all PRD items are complete.**

**Each iteration is a fresh instance with clean context. Memory persists via git history.**

[![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Compatible-orange?style=for-the-badge)](https://docs.anthropic.com/en/docs/claude-code)

<img src="ralph.png" alt="Ralph" width="200">

Based on [Geoffrey Huntley's Ralph pattern](https://ghuntley.com/ralph/).

</div>

---

## Security Warning

**Ralph runs AI agents autonomously with full access to your codebase.** Before running:

- **Never expose production credentials** - Ralph could accidentally commit, log, or transmit sensitive values like `AWS_ACCESS_KEY_ID`, `DATABASE_URL`, or API keys
- **Use sandboxing** - Run Ralph in a Docker container, VM, or isolated sandbox environment to limit potential damage
- **Review commits before pushing** - Always review what Ralph committed before pushing to remote

---

## Why This Exists

AI coding assistants lose context on large tasks. By the time they reach the end, they have forgotten the beginning.

Ralph solves this by:
- **Starting fresh each iteration** - Every task begins with full context capacity
- **Persisting memory in git** - Commits, `progress.txt`, and `prd.json` carry knowledge forward
- **Keeping tasks small** - Each story fits comfortably in one context window

The result: autonomous task completion that does not degrade over time.

---

## Who This Is For

- **Solo developers** who want to ship while they sleep
- **Small teams** who want to multiply their output
- **Anyone** who has a clear PRD and wants autonomous execution

Ralph works best when you have:
- Well-defined, testable acceptance criteria
- A codebase with type checking and tests
- Tasks that can be broken into small, independent stories

---

## How It Works

V-Ralph implements a three-layer validation model:

```
┌─────────────────────────────────────────────────────────────┐
│                    V-Ralph Execution Loop                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   1. Read prd.json → pick next story (passes: false)        │
│                          ↓                                  │
│   2. CODER: Implement the story with Claude Code            │
│                          ↓                                  │
│   3. VALIDATION: Run quality checks (typecheck, lint, test) │
│                          ↓                                  │
│   4. AUDITOR: Semantic review by separate Claude instance   │
│       - PASS → commit and mark story complete               │
│       - RETRY → loop back to coder with feedback            │
│       - ESCALATE → stop and request human input             │
│                          ↓                                  │
│   5. All stories done? → EXIT                               │
│      More stories? → LOOP (back to step 1)                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Getting Started

### Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated (`npm install -g @anthropic-ai/claude-code`)
- Python 3.8 or later
- A git repository for your project

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/ralph-wiggum
cd ralph-wiggum/scripts/ralph
```

**Optional: Install the planning skill**

```bash
# Install globally
cp -r .claude/skills/v-ralph-planning ~/.claude/skills/

# Or install locally to project
mkdir -p .claude/skills
cp -r .claude/skills/v-ralph-planning .claude/skills/
```

---

## Usage

### Commands

| Command | Description |
|---------|-------------|
| `python v_ralph.py --help` | Show help and available commands |
| `python v_ralph.py --version` | Show version |
| `python v_ralph.py status` | Show status of all stories |
| `python v_ralph.py run` | Execute all pending stories |
| `python v_ralph.py run --story US-001` | Execute a specific story |
| `python v_ralph.py run --dry-run` | Preview without executing |
| `python v_ralph.py run --max-retries 3` | Set retry limit per story |

### Run Command Flags

| Flag | Description |
|------|-------------|
| `--prd PATH` | Path to prd.json or prd.yml file (default: prd.json in current directory) |
| `--progress PATH` | Path to progress.txt file (default: progress.txt in current directory) |
| `--max-retries N` | Maximum retry attempts per story (default: 5) |
| `--story US-XXX` | Run only the specified story ID |
| `--dry-run` | Show what would run without executing |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All requested stories completed successfully (or nothing to run) |
| 1 | Error (file not found, invalid story ID, etc.) |
| 2 | Story escalated (requires human input) |

### Behavior

- On **success**: Commits changes, updates prd.json to mark story as passed, appends entry to progress.txt
- On **escalation**: Stops execution immediately, displays reason, exits with code 2
- On **circuit breaker** (max retries exceeded): Logs failure, moves to next pending story

### Status Command

```bash
# Show status of all stories (reads prd.json from current directory)
python v_ralph.py status

# Specify a custom PRD file path
python v_ralph.py status --prd /path/to/prd.json
```

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

---

## Three-Layer Validation

V-Ralph implements rigorous validation to catch "green build hallucinations":

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

---

## Key Files

| File | Purpose |
|------|---------|
| `scripts/ralph/v_ralph.py` | Main CLI entry point |
| `scripts/ralph/micro_v/` | Executor and auditor components |
| `scripts/ralph/shared/` | Common utilities (PRD, git, progress) |
| `scripts/ralph/CLAUDE.md` | Instructions for coding agents |
| `prd.json` | User stories with `passes` status |
| `progress.txt` | Append-only learnings for future iterations |

### Project Structure

```
scripts/ralph/
├── v_ralph.py        # Main CLI entry point
├── macro_v/          # Macro-V lifecycle components
├── micro_v/          # Micro-V lifecycle components (executor, auditor)
├── shared/           # Common utilities (prd, claude, progress, git)
├── tests/            # Unit and integration tests
├── prd.json          # Project requirements document
└── progress.txt      # Progress tracking log
```

---

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

---

## Planning with V-Ralph

V-Ralph includes a Claude Code skill for interactive spec refinement that produces machine-verifiable specifications.

### Invoking the Planning Skill

In Claude Code, use the `/v-ralph-planning` command:

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
4. **Outputs valid prd.json** ready for `v_ralph.py run`

### Verifiable Criteria Examples

The skill enforces machine-verifiable criteria:

| Bad (Vague) | Good (Verifiable) |
|-------------|-------------------|
| "Works correctly" | "Returns 200 status for valid input" |
| "Good error handling" | "Raises ValueError with message 'Invalid ID'" |
| "Proper testing" | "tests/test_feature.py exists and passes" |

### Skill Location

The planning skill is at `.claude/skills/v-ralph-planning/SKILL.md` and can be customized for project-specific needs.

---

## Critical Concepts

### Each Iteration = Fresh Context

Each iteration spawns a **new Claude Code instance** with clean context. The only memory between iterations is:
- Git history (commits from previous iterations)
- `progress.txt` (learnings and context)
- `prd.json` (which stories are done)

### Small Tasks

Each PRD item should be small enough to complete in one context window. If a task is too big, the LLM runs out of context before finishing and produces poor code.

**Right-sized stories:**
- Add a database column and migration
- Add a UI component to an existing page
- Update a server action with new logic
- Add a filter dropdown to a list

**Too big (split these):**
- "Build the entire dashboard"
- "Add authentication"
- "Refactor the API"

### Feedback Loops

Ralph only works if there are feedback loops:
- Typecheck catches type errors
- Tests verify behavior
- CI must stay green (broken code compounds across iterations)

### Stop Condition

When all stories have `passes: true`, V-Ralph exits with code 0.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Story keeps failing after multiple iterations | Check if acceptance criteria are clear and verifiable. Split into smaller stories if needed. |
| Ralph commits broken code | Ensure quality gates (typecheck, lint, test) are configured in your project. |
| Context runs out mid-story | Story is too big. Split it into smaller, focused changes. |
| Progress not persisting | Check that `progress.txt` exists and is being committed. |
| Wrong branch | Verify `branchName` in `prd.json` matches your intended branch. |
| Story escalated | Human input needed - review the escalation reason and clarify the spec. |

---

## Development

### Running Tests

```bash
cd scripts/ralph

# Run all tests
python -m pytest tests/ -v

# Run only unit tests (faster)
python -m pytest tests/ -v --ignore=tests/test_integration.py

# Run only integration tests
python -m pytest tests/test_integration.py -v
```

### Integration Tests

The integration tests in `tests/test_integration.py` verify the complete V-model flow with mocked Claude calls. These tests are designed for CI environments with deterministic behavior.

**What they test:**
1. Story execution with mocked Claude coder
2. Validation pass/retry flow
3. Semantic audit pass/retry/escalate verdicts
4. PRD update (marking stories as passed)
5. Progress file updates

**Test fixtures:**

The `tests/fixtures/` directory contains a minimal project for testing:
- `prd.json` - Simple PRD with one test story
- `progress.txt` - Progress file with patterns
- `sample.py` - Placeholder Python file
- `test_sample.py` - Placeholder test file

**Running in CI:**

The integration tests use mocked responses and don't require actual Claude CLI access:

```bash
python -m pytest tests/test_integration.py -v --tb=short
```

All mocks produce deterministic results, making tests reproducible across environments.

### Type Checking

```bash
python -m py_compile v_ralph.py
```

---

## Acknowledgments

Originally forked from [snarktank/ralph](https://github.com/snarktank/ralph). We are grateful for their foundational work on the Ralph agent pattern.

---

## References

- [Geoffrey Huntley's Ralph article](https://ghuntley.com/ralph/)
- [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code)
