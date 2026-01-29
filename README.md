<div align="center">

# Ralph Wiggum

**An autonomous AI agent loop for Claude Code that runs until all PRD items are complete.**

**Each iteration is a fresh instance with clean context. Memory persists via git history.**

[![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Compatible-orange?style=for-the-badge)](https://docs.anthropic.com/en/docs/claude-code)

<img src="ralph.png" alt="Ralph" width="200">

Based on [Geoffrey Huntley's Ralph pattern](https://ghuntley.com/ralph/).

> **Fork:** This project is a fork of [snarktank/ralph](https://github.com/snarktank/ralph).

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

**Step 1: Copy V-Ralph to your project**

```bash
# From your project root
mkdir -p scripts/ralph
cp -r /path/to/ralph-wiggum/scripts/ralph/* scripts/ralph/
```

**Step 2: Install the planning skill (optional)**

```bash
# Install globally
cp -r /path/to/ralph-wiggum/.claude/skills/v-ralph-planning ~/.claude/skills/

# Or install locally to project
mkdir -p .claude/skills
cp -r /path/to/ralph-wiggum/.claude/skills/v-ralph-planning .claude/skills/
```

---

## Workflow

### 1. Create a PRD

Use the V-Ralph planning skill to generate a machine-verifiable specification:

```
/v-ralph-planning
```

Answer the clarifying questions. The skill produces a `prd.json` with verifiable acceptance criteria.

### 2. Run V-Ralph

```bash
cd scripts/ralph

# Check status of all stories
python v_ralph.py status

# Execute pending stories
python v_ralph.py run

# Execute a specific story
python v_ralph.py run --story US-001

# Preview what would run
python v_ralph.py run --dry-run
```

---

## Commands

| Command | Description |
|---------|-------------|
| `python v_ralph.py status` | Show status of all stories |
| `python v_ralph.py run` | Execute all pending stories |
| `python v_ralph.py run --story US-001` | Execute a specific story |
| `python v_ralph.py run --dry-run` | Preview without executing |
| `python v_ralph.py run --max-retries 3` | Set retry limit per story |
| `python v_ralph.py --help` | Show all available options |

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

---

## Critical Concepts

### Three-Layer Validation

V-Ralph implements rigorous validation to catch "green build hallucinations":

1. **Coder** - Implements the story according to acceptance criteria
2. **Validation** - Runs typecheck, lint, and tests (necessary but not sufficient)
3. **Auditor** - Separate Claude instance reviews if implementation satisfies the *spirit* of the spec

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

### Verifiable Acceptance Criteria

The planning skill enforces machine-verifiable criteria:

| Bad (Vague) | Good (Verifiable) |
|-------------|-------------------|
| "Works correctly" | "Returns 200 status for valid input" |
| "Good error handling" | "Raises ValueError with message 'Invalid ID'" |
| "Proper testing" | "tests/test_feature.py exists and passes" |

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

# Run only unit tests
python -m pytest tests/ -v --ignore=tests/test_integration.py

# Run integration tests
python -m pytest tests/test_integration.py -v
```

---

## Acknowledgments

This project is a fork of [snarktank/ralph](https://github.com/snarktank/ralph), originally created by the snarktank team. We are grateful for their foundational work on the Ralph agent pattern.

The original project is licensed under the MIT License, and this derivative work maintains that license with the original copyright notice preserved.

---

## References

- [Original Ralph repository (snarktank/ralph)](https://github.com/snarktank/ralph)
- [Geoffrey Huntley's Ralph article](https://ghuntley.com/ralph/)
- [Claude Code documentation](https://docs.anthropic.com/en/docs/claude-code)
