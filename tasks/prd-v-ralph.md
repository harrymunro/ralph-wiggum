# PRD: V-Ralph (Fractal V-Lifecycle Agent)

## Introduction

V-Ralph is a Python-based autonomous coding agent that replaces the existing `ralph.sh` bash implementation. It enforces rigor at both ends of the V-lifecycle: **watertight specs** (left arm) through interactive refinement, and **watertight validation** (right arm) through three-layer verification including an adversarial semantic audit.

The system separates "Thinking" (Macro-V: planning inside Claude Code) from "Doing" (Micro-V: stateless execution from terminal), solving the core problems of Context Rot and Semantic Drift that plague autonomous coding agents.

## Goals

- Replace `ralph.sh` with a Python implementation that's easier to extend and maintain
- Enforce machine-verifiable acceptance criteria before execution begins
- Catch "green build hallucinations" where tests pass but code doesn't match intent
- Preserve knowledge across stateless iterations via structured progress tracking
- Provide clear escalation paths for genuine design decisions (not bugs)
- Include README updates as first-class acceptance criteria for every story

## User Stories

### US-001: Project scaffolding and CLI entry point
**Description:** As a developer, I want the basic V-Ralph project structure so I can begin implementing the core modules.

**Acceptance Criteria:**
- [ ] `v_ralph.py` exists and is executable (`python v_ralph.py --help` works)
- [ ] Directory structure created: `macro_v/`, `micro_v/`, `shared/`, `tests/`
- [ ] Each module has `__init__.py`
- [ ] CLI shows `run`, `status` commands in help output
- [ ] `python v_ralph.py --version` outputs version string
- [ ] README.md documents installation and basic usage
- [ ] Typecheck passes (`python -m py_compile v_ralph.py`)

### US-002: prd.yml read/write module
**Description:** As the execution engine, I need to read story definitions and update their status so progress persists across iterations.

**Acceptance Criteria:**
- [ ] `shared/prd.py` module exists
- [ ] `load_prd(path)` reads and parses prd.yml, returns typed dataclass
- [ ] `save_prd(prd, path)` writes prd.yml preserving comments where possible
- [ ] `get_pending_stories(prd)` returns stories where `passes: false`
- [ ] `mark_story_passed(prd, story_id)` sets `passes: true` and resets attempts
- [ ] `increment_attempts(prd, story_id)` increments attempt counter
- [ ] Handles missing file gracefully with clear error message
- [ ] Unit tests in `tests/test_prd.py` cover all functions
- [ ] README.md documents prd.yml format with example
- [ ] Typecheck passes

### US-003: Claude CLI wrapper
**Description:** As the execution engine, I need a clean interface to spawn stateless Claude instances so I can implement the retry loop.

**Acceptance Criteria:**
- [ ] `shared/claude.py` module exists
- [ ] `invoke_claude(prompt, timeout=300)` spawns `claude -p` subprocess
- [ ] Returns tuple of `(stdout, stderr, exit_code)`
- [ ] Handles timeout gracefully, kills process, returns timeout error
- [ ] `build_coder_prompt(story, context)` assembles prompt from story + learnings
- [ ] Process is fully terminated after call (no zombie processes)
- [ ] Unit tests mock subprocess for testing
- [ ] README.md documents Claude CLI requirements
- [ ] Typecheck passes

### US-004: Micro-V executor loop (without semantic audit)
**Description:** As the execution engine, I need the core retry loop that writes code and runs validation so stories can be implemented autonomously.

**Acceptance Criteria:**
- [ ] `micro_v/executor.py` module exists
- [ ] `execute_story(story, config)` implements the retry loop
- [ ] Loop steps: invoke coder → run validation_command → check result
- [ ] On validation failure: retry with error output as context
- [ ] Circuit breaker: stop after `max_retries` (default 5, configurable)
- [ ] Returns structured result: `success | failed | escalated`
- [ ] Logs each iteration with clear status output to terminal
- [ ] Unit tests cover success path, failure path, circuit breaker
- [ ] README.md documents the execution flow
- [ ] Typecheck passes

### US-005: Coder prompt template
**Description:** As the coding agent, I need clear instructions so I implement stories correctly and update documentation.

**Acceptance Criteria:**
- [ ] `micro_v/prompts/coder.md` exists
- [ ] Prompt includes: story goal, files whitelist, acceptance criteria
- [ ] Prompt instructs agent to update README as part of implementation
- [ ] Prompt forbids touching files outside whitelist
- [ ] Prompt forbids forbidden shortcuts (@ts-ignore, eslint-disable, etc.)
- [ ] Prompt includes learnings from progress.md (patterns + recent history)
- [ ] Template uses clear placeholders: `{{goal}}`, `{{files}}`, `{{criteria}}`, `{{learnings}}`
- [ ] README.md explains prompt customization
- [ ] Manual review confirms prompt is clear and unambiguous

### US-006: Semantic auditor module
**Description:** As the validation layer, I need an adversarial reviewer to catch cases where tests pass but code doesn't match intent.

**Acceptance Criteria:**
- [ ] `micro_v/auditor.py` module exists
- [ ] `audit_implementation(spec, diff)` spawns fresh `claude -p` call
- [ ] Auditor has NO context from coding session (spec + diff only)
- [ ] Returns enum: `PASS | RETRY(feedback) | ESCALATE(reason)`
- [ ] Process is killed immediately after returning verdict
- [ ] `ESCALATE` only returned for genuine design ambiguity (high bar)
- [ ] Unit tests verify each return type
- [ ] README.md documents what triggers escalation vs retry
- [ ] Typecheck passes

### US-007: Adversarial auditor prompt
**Description:** As the semantic auditor, I need instructions that make me skeptical and thorough so I catch subtle mismatches.

**Acceptance Criteria:**
- [ ] `micro_v/prompts/auditor.md` exists
- [ ] Prompt frames auditor as "skeptical QA engineer trying to find gaps"
- [ ] Prompt lists specific things to check: edge cases, intent vs letter, assumptions
- [ ] Prompt defines clear output format: `PASS` | `RETRY: [feedback]` | `ESCALATE: [reason]`
- [ ] Prompt emphasizes high bar for ESCALATE (design questions only, not bugs)
- [ ] Examples included showing PASS, RETRY, and ESCALATE scenarios
- [ ] README.md explains the three-layer validation model
- [ ] Manual review confirms prompt is adversarial, not rubber-stamp

### US-008: Integrate semantic audit into executor
**Description:** As the execution engine, I need the auditor as the third validation layer so semantic drift is caught before commit.

**Acceptance Criteria:**
- [ ] `executor.py` calls auditor after validation_command passes
- [ ] On `RETRY`: loop back with auditor feedback as context
- [ ] On `ESCALATE`: exit loop, return escalated result with reason
- [ ] On `PASS`: proceed to commit
- [ ] Audit retries count toward circuit breaker limit
- [ ] Integration tests cover: pass-through, retry loop, escalation
- [ ] README.md documents the full three-layer validation flow
- [ ] Typecheck passes

### US-009: Progress tracking with two-tier structure
**Description:** As the execution engine, I need to read learnings and append new ones so knowledge persists across iterations without bloating context.

**Acceptance Criteria:**
- [ ] `shared/progress.py` module exists
- [ ] `load_learnings(path)` returns Patterns section + last 5 Recent History entries
- [ ] `append_progress(path, entry)` adds new entry to Recent History
- [ ] `promote_pattern(path, pattern)` adds item to Codebase Patterns section
- [ ] Older history entries remain in file but aren't loaded for context
- [ ] Handles missing file gracefully (creates with template)
- [ ] Unit tests verify two-tier loading, appending, promotion
- [ ] README.md documents progress.md format
- [ ] Typecheck passes

### US-010: Status command
**Description:** As a user, I want to see the current state of all stories so I know what's done and what's pending.

**Acceptance Criteria:**
- [ ] `python v_ralph.py status` reads prd.yml and displays table
- [ ] Table shows: ID, Title, Status (pass/fail/escalated), Attempts
- [ ] Color coding: green=passed, red=failed, yellow=escalated
- [ ] Shows total progress: "4/6 stories complete"
- [ ] Shows current branch name
- [ ] Handles missing prd.yml with helpful error message
- [ ] README.md documents the status command
- [ ] Typecheck passes

### US-011: Run command with full integration
**Description:** As a user, I want to execute all pending stories autonomously so I can fire-and-forget the agent.

**Acceptance Criteria:**
- [ ] `python v_ralph.py run` executes all stories where `passes: false`
- [ ] `--max-retries N` flag overrides default (5) retry limit
- [ ] `--story US-XXX` flag runs single story only
- [ ] `--dry-run` flag shows what would run without executing
- [ ] On story success: commits changes, updates prd.yml, appends progress.md
- [ ] On escalation: stops loop, displays reason, exits with code 2
- [ ] On circuit breaker: marks story escalated, moves to next story
- [ ] Displays clear progress output during execution
- [ ] README.md documents all CLI flags
- [ ] Typecheck passes

### US-012: Git integration for commits
**Description:** As the execution engine, I need to commit completed work so progress is captured in version control.

**Acceptance Criteria:**
- [ ] `shared/git.py` module exists (or inline in executor)
- [ ] `commit_story(story_id, title)` stages and commits with message format: `feat: [ID] - [Title]`
- [ ] Only commits files in story's whitelist (not unrelated changes)
- [ ] Verifies working directory is clean before commit (fails if dirty with unrelated files)
- [ ] Returns commit SHA on success
- [ ] Unit tests mock git commands
- [ ] README.md notes git requirements
- [ ] Typecheck passes

### US-013: Macro-V planning skill for Claude Code
**Description:** As a user planning a feature inside Claude Code, I want interactive refinement that produces machine-verifiable specs.

**Acceptance Criteria:**
- [ ] Skill file exists at appropriate location for Claude Code
- [ ] Skill guides Claude to ask clarifying questions until all criteria are verifiable
- [ ] Each acceptance criterion must have a `verify` command (grep, test, file exists, etc.)
- [ ] Skill enforces README update criterion for every story
- [ ] Skill enforces files whitelist for every story
- [ ] Outputs valid prd.yml to project directory
- [ ] Skill includes examples of good vs bad acceptance criteria
- [ ] README.md explains how to invoke the planning skill
- [ ] Manual test: run skill, verify output is valid prd.yml

### US-014: End-to-end integration test
**Description:** As a developer, I need a test that proves the full V-model flow works so I have confidence in the system.

**Acceptance Criteria:**
- [ ] Test fixture: minimal project with simple prd.yml (1-2 trivial stories)
- [ ] Test runs `v_ralph.py run` against fixture
- [ ] Verifies: story executed, validation passed, audit passed, commit created
- [ ] Verifies: prd.yml updated with `passes: true`
- [ ] Verifies: progress.md has new entry
- [ ] Verifies: README.md was updated (per story criteria)
- [ ] Test can run in CI (mocked Claude calls for determinism)
- [ ] README.md documents how to run integration tests
- [ ] Test passes reliably

## Functional Requirements

- FR-1: V-Ralph must be a standalone Python tool that operates on any project directory containing a `prd.yml`
- FR-2: All Claude invocations must use `claude -p` (print mode) for stateless execution
- FR-3: Each iteration must be fully stateless - context comes only from files (prd.yml, progress.md, CLAUDE.md)
- FR-4: The semantic auditor must be a separate Claude invocation with no context from the coding session
- FR-5: Escalation must only occur for genuine design ambiguity, not for bugs or missing edge cases
- FR-6: Circuit breaker must stop retries after configurable limit (default 5)
- FR-7: Every story must include README update as an acceptance criterion
- FR-8: Every acceptance criterion must have a machine-verifiable `verify` command
- FR-9: Progress.md must use two-tier structure: Patterns (always loaded) + Recent History (last 5 only)
- FR-10: Commits must follow format: `feat: [Story ID] - [Story Title]`
- FR-11: Stories must define a files whitelist; agent cannot touch files outside whitelist
- FR-12: The tool must provide clear terminal output showing iteration progress and status

## Non-Goals

- No direct Claude API integration (CLI only via `claude -p`)
- No parallel story execution (sequential only)
- No web UI or dashboard
- No cost tracking or token counting
- No backward compatibility with `prd.json` format
- No automatic migration from `ralph.sh`
- No evolutionary/experiment features (may port later)
- No support for Python < 3.12

## Technical Considerations

### Dependencies
- Python 3.12+
- PyYAML for prd.yml parsing
- Rich (optional) for terminal output formatting
- Claude Code CLI installed and configured

### File Formats

**prd.yml:**
```yaml
project: "Project Name"
branch: "ralph/feature-name"

stories:
  - id: US-001
    title: "Story title"
    goal: |
      Natural language description.
    files:
      - src/file.ts
      - README.md
    acceptance_criteria:
      - criterion: "Description"
        verify: "grep -q 'pattern' file"
    validation_command: "pytest tests/"
    passes: false
    attempts: 0
    escalated: false
    escalation_reason: null
```

**progress.md:**
```markdown
# Progress

## Codebase Patterns
<!-- Max ~30 items, always included in context -->
- Pattern 1
- Pattern 2

## Recent History
<!-- Last 5 iterations included in context -->

### [Date] US-001: Title
**What worked:** ...
**Gotchas:** ...
**Files:** ...

---

## Archive
<!-- Historical record, NOT included in context -->
```

### Architecture
```
v-ralph/
├── v_ralph.py              # CLI entry point (argparse)
├── macro_v/
│   ├── __init__.py
│   ├── refiner.py          # Interactive spec refinement
│   └── prompts/
│       └── refinement.md
├── micro_v/
│   ├── __init__.py
│   ├── executor.py         # Retry loop
│   ├── auditor.py          # Semantic audit
│   └── prompts/
│       ├── coder.md
│       └── auditor.md
├── shared/
│   ├── __init__.py
│   ├── prd.py              # prd.yml handling
│   ├── progress.py         # progress.md handling
│   ├── claude.py           # claude -p wrapper
│   └── git.py              # Git operations
└── tests/
    ├── test_prd.py
    ├── test_progress.py
    ├── test_executor.py
    ├── test_auditor.py
    └── test_integration.py
```

## Success Metrics

- Agent completes stories without human intervention (except genuine design questions)
- Semantic auditor catches at least some "green build hallucinations" in testing
- README is updated as part of every story completion
- Progress.md context stays under 2000 tokens even after many iterations
- Clean break from bash - `ralph.sh` can be archived

## Open Questions

- Should the auditor prompt be customizable per-project via a config file?
- Should there be a `v-ralph init` command to scaffold prd.yml and progress.md?
- How should the tool handle stories with failing validation_command that never passes (e.g., typo in command)?
- Should there be a `--verbose` flag for debugging prompt assembly?
