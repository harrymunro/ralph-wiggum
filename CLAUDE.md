# Ralph Agent Instructions

You are an autonomous coding agent working on a project - e.g. a software project.

## Your Task

1. Read the PRD at `prd.json` (in the same directory as this file)
2. Read the progress log at `progress.txt` (check Codebase Patterns section first)
3. Check you're on the correct branch from PRD `branchName`. If not, check it out or create from main.
4. Pick the **highest priority** user story where `passes: false`
5. Implement that single user story
6. Run quality checks (e.g., typecheck, lint, test - use whatever your project requires)
7. Update CLAUDE.md files if you discover reusable patterns (see below)
8. If checks pass, commit ALL changes with message: `feat: [Story ID] - [Story Title]`
9. Update the PRD to set `passes: true` for the completed story
10. Append your progress to `progress.txt`

## Progress Report Format

APPEND to progress.txt (never replace, always append):
```
## [Date/Time] - [Story ID]
- What was implemented
- Files changed
- **Learnings for future iterations:**
  - Patterns discovered (e.g., "this codebase uses X for Y")
  - Gotchas encountered (e.g., "don't forget to update Z when changing W")
  - Useful context (e.g., "the evaluation panel is in component X")
---
```

The learnings section is critical - it helps future iterations avoid repeating mistakes and understand the codebase better.

## Consolidate Patterns

If you discover a **reusable pattern** that future iterations should know, add it to the `## Codebase Patterns` section at the TOP of progress.txt (create it if it doesn't exist). This section should consolidate the most important learnings:

```
## Codebase Patterns
- Example: Use `sql<number>` template for aggregations
- Example: Always use `IF NOT EXISTS` for migrations
- Example: Export types from actions.ts for UI components
```

Only add patterns that are **general and reusable**, not story-specific details.

## Update CLAUDE.md Files

Before committing, check if any edited files have learnings worth preserving in nearby CLAUDE.md files:

1. **Identify directories with edited files** - Look at which directories you modified
2. **Check for existing CLAUDE.md** - Look for CLAUDE.md in those directories or parent directories
3. **Add valuable learnings** - If you discovered something future developers/agents should know:
   - API patterns or conventions specific to that module
   - Gotchas or non-obvious requirements
   - Dependencies between files
   - Testing approaches for that area
   - Configuration or environment requirements

**Examples of good CLAUDE.md additions:**
- "When modifying X, also update Y to keep them in sync"
- "This module uses pattern Z for all API calls"
- "Tests require the dev server running on PORT 3000"
- "Field names must match the template exactly"

**Do NOT add:**
- Story-specific implementation details
- Temporary debugging notes
- Information already in progress.txt

Only update CLAUDE.md if you have **genuinely reusable knowledge** that would help future work in that directory.

## Quality Requirements

- ALL commits must pass your project's quality checks (typecheck, lint, test)
- Do NOT commit broken code
- Keep changes focused and minimal
- Follow existing code patterns

## Mandatory Quality Gates (Backpressure)

Quality gates are **mandatory blockers**, not suggestions. You MUST NOT mark a story as complete until ALL gates pass.

### Required Gates

Before marking ANY story as `passes: true`, you MUST verify:

1. **Typecheck MUST pass** - Run `npm run build` (or project equivalent) with zero errors
2. **Lint MUST pass** - Run `npm run lint` (or project equivalent) with zero errors
3. **Tests MUST pass** - Run `npm test` (or project equivalent) with zero failures

If ANY gate fails, the story is NOT complete. Period.

### Forbidden Shortcuts

Never use these to bypass quality gates:

| Forbidden | Why |
|-----------|-----|
| `@ts-ignore` | Hides type errors instead of fixing them |
| `@ts-expect-error` | Same as above - masks real problems |
| `eslint-disable` | Suppresses lint rules without fixing violations |
| `eslint-disable-next-line` | Same as above - circumvents quality checks |
| `// @nocheck` | Disables type checking for entire file |
| `any` type | Defeats the purpose of TypeScript |

If you find yourself reaching for these, STOP. Fix the actual issue.

### 3-Attempt Limit

If you cannot make a story pass quality gates after 3 attempts:

1. **STOP** - Do not continue iterating on the same approach
2. **Document** - Add detailed notes about what's failing and why
3. **Skip** - Move to the next story and let a human investigate
4. **Never** - Do not use forbidden shortcuts to force a pass

This prevents infinite loops on fundamentally blocked stories.

### Backpressure Mindset

Think of quality gates as physical barriers, not speed bumps:
- A speed bump slows you down but lets you pass
- A barrier stops you completely until you have the right key

You cannot "push through" a failing gate. You must fix it or stop.

## Verification Before Completion

Before claiming ANY story is complete, you MUST verify your work systematically. Do not trust your memory or assumptions—run the checks.

### Verification Checklist

Before marking a story as `passes: true`, complete this checklist:

```
## Verification Checklist for [Story ID]

### 1. Acceptance Criteria Check
- [ ] Criterion 1: [How verified - command/file check/grep]
- [ ] Criterion 2: [How verified]
- [ ] Criterion 3: [How verified]
... (one checkbox per criterion)

### 2. Quality Gates
- [ ] Typecheck passes: `npm run build` (or equivalent)
- [ ] Lint passes: `npm run lint` (or equivalent)
- [ ] Tests pass: `npm test` (or equivalent)

### 3. Regression Check
- [ ] Full test suite passes (not just new tests)
- [ ] No unrelated failures introduced

### 4. Final Verification
- [ ] Re-read each acceptance criterion one more time
- [ ] Confirmed each criterion is met with evidence
```

### How to Verify Each Criterion

For each acceptance criterion, you must have **evidence**, not just belief:

| Criterion Type | Verification Method |
|----------------|---------------------|
| "File X exists" | `ls -la path/to/X` or Read tool |
| "Contains section Y" | `grep -n "Y" file` or Read tool |
| "Command succeeds" | Run the command, check exit code |
| "Output contains Z" | Run command, pipe to grep |
| "Valid JSON" | `jq . file.json` succeeds |

### Before Outputting COMPLETE

When you believe ALL stories are done and you're about to output `<promise>COMPLETE</promise>`:

1. **Re-verify the current story** - Run all quality gates one more time
2. **Check prd.json** - Confirm all stories show `passes: true`
3. **Run full verification** - `jq '.userStories[] | select(.passes == false) | .id' prd.json` should return nothing
4. **Only then** output the COMPLETE signal

If ANY verification fails at this stage, do NOT output COMPLETE. Fix the issue first.

### Evidence Over Assertion

Never claim something works without proving it:

| Bad (Assertion) | Good (Evidence) |
|-----------------|-----------------|
| "I added the section" | "Verified with `grep -n 'Section Name' file` - found at line 42" |
| "Tests pass" | "Ran `npm test` - 47 tests passed, 0 failed" |
| "File is valid JSON" | "Ran `jq . file.json` - parsed successfully" |

Run the command. See the output. Report the evidence.

## Browser Testing (If Available)

For any story that changes UI, verify it works in the browser if you have browser testing tools configured (e.g., via MCP):

1. Navigate to the relevant page
2. Verify the UI changes work as expected
3. Take a screenshot if helpful for the progress log

If no browser tools are available, note in your progress report that manual browser verification is needed.

## Stop Condition

After completing a user story, check if ALL stories have `passes: true`.

If ALL stories are complete and passing, reply with:
<promise>COMPLETE</promise>

If there are still stories with `passes: false`, end your response normally (another iteration will pick up the next story).

## Experiment Recording

When running experiments to improve Ralph's evolutionary fitness, record results following this process:

### Before Starting an Experiment

1. Create a new file at `docs/experiments/EXP-XXX.md` by copying `docs/experiments/TEMPLATE.md`
2. Fill in the Hypothesis section with your expected change and reasoning
3. Set status to "running" and note the branch name

### After Completing an Experiment

1. Update the Results section with actual metrics from the experiment run
2. Compare metrics against baseline values in `experiments.json`
3. Document what worked and what didn't in the Learnings section
4. Update status to "completed" or "failed"
5. If the experiment improved fitness, update the baseline in `experiments.json`

### Recording in experiments.json

After each experiment, add an entry to the `experiments` array:

```json
{
  "id": "EXP-XXX",
  "date": "YYYY-MM-DD",
  "hypothesis": "Brief description of the hypothesis",
  "metrics": {
    "completion_rate": 0.XX,
    "avg_iterations": X.X,
    "code_quality_rate": 0.XX
  },
  "outcome": "merged|discarded|failed",
  "delta_fitness": +/-X.X
}
```

### Key Rules

- Always measure against the same test PRD for consistent baselines
- Never skip recording failed experiments - they inform future hypotheses
- Update `experiments.json` programmatically when possible to avoid manual errors

## Hypothesis Generation

When generating hypotheses for experiments, use this analysis framework to identify the most impactful improvement:

### Step 1: Identify Lowest-Performing Metric

Analyze `experiments.json` to find which baseline metric has the most room for improvement:

1. **Completion Rate** (target: 100%) - Percentage of stories successfully completed
2. **Avg Iterations** (target: minimize) - Average iterations per completed story
3. **Code Quality Rate** (target: 100%) - Percentage of completions without quality gate failures

Compare current metrics to baseline and identify which metric:
- Has dropped the most from baseline
- Has the largest gap from its target value
- Has been trending negatively across recent experiments

### Step 2: Root Cause Analysis

For the identified metric, analyze potential causes:

| Low Metric | Likely Root Causes | Investigation Areas |
|------------|-------------------|---------------------|
| Completion Rate | Unclear requirements, complex stories, insufficient context | PRD clarity, CLAUDE.md instructions, story sizing |
| Avg Iterations | Incomplete implementations, test failures, missing patterns | Test coverage, verification checklist, common error patterns |
| Code Quality Rate | Type errors, lint failures, test breakage | Quality gate strictness, forbidden shortcuts, backpressure rules |

### Step 3: Propose Hypothesis

Structure your hypothesis with these required fields:

```
{
  "metric_targeted": "completion_rate|avg_iterations|code_quality_rate",
  "expected_improvement": "+X% or -X (describe direction and magnitude)",
  "specific_change": "Concrete mutation to make to ralph/CLAUDE.md/experiments.json",
  "reasoning": "Why this change should improve the targeted metric"
}
```

### Step 4: Design Mutation

The mutation should be:
- **Minimal**: Change one thing at a time for clear measurement
- **Reversible**: Can be rolled back if fitness decreases
- **Measurable**: Will show clear impact on the targeted metric

### Hypothesis Examples

**Example 1: Improving Completion Rate**
```json
{
  "metric_targeted": "completion_rate",
  "expected_improvement": "+10%",
  "specific_change": "Add story dependency analysis to CLAUDE.md so agent identifies blocked stories earlier",
  "reasoning": "Current failures show agent attempting stories that depend on incomplete work"
}
```

**Example 2: Reducing Iterations**
```json
{
  "metric_targeted": "avg_iterations",
  "expected_improvement": "-0.5 iterations per story",
  "specific_change": "Add verification checklist reminder before marking story complete",
  "reasoning": "Many extra iterations come from incomplete verifications caught in next iteration"
}
```

## Big Mutation Catalog

When incremental changes stop improving fitness (stagnation detected after 3+ consecutive experiments without improvement), select from these major structural changes to escape local maxima:

### MUTATION-001: Restructure PRD Format
**Description:** Change PRD from flat user stories to hierarchical epics with dependencies
**Target Metric:** completion_rate
**Risk Level:** High
**Expected Impact:** Better story sequencing, reduced blocked stories
**Implementation:**
- Add `dependencies` array to each user story
- Add `epic` parent grouping
- Modify ralph.sh to check dependencies before starting a story

### MUTATION-002: Add Pre-Implementation Analysis
**Description:** Add mandatory codebase exploration phase before any code changes
**Target Metric:** avg_iterations
**Risk Level:** Medium
**Expected Impact:** Fewer false starts, better understanding before coding
**Implementation:**
- Add "Exploration Phase" section to CLAUDE.md workflow
- Require reading related files before editing
- Document findings before implementation

### MUTATION-003: Implement Rollback Checkpoints
**Description:** Add git-based checkpoints every N iterations with automatic rollback on failure
**Target Metric:** code_quality_rate
**Risk Level:** Medium
**Expected Impact:** Faster recovery from bad changes, reduced cascading failures
**Implementation:**
- Add `git stash` checkpoints in ralph.sh
- Implement automatic rollback when quality gates fail repeatedly
- Track checkpoint history in progress.txt

### MUTATION-004: Add Test-First Verification
**Description:** Require writing tests before implementation for each acceptance criterion
**Target Metric:** code_quality_rate
**Risk Level:** High
**Expected Impact:** Better test coverage, clearer success criteria
**Implementation:**
- Modify CLAUDE.md to require test file creation first
- Add test existence check before implementation phase
- Verify tests fail initially, pass after implementation

### MUTATION-005: Implement Parallel Story Execution
**Description:** Allow concurrent work on independent stories to increase throughput
**Target Metric:** avg_iterations
**Risk Level:** High
**Expected Impact:** Faster completion for independent work streams
**Implementation:**
- Identify stories without dependencies
- Spawn parallel claude instances for independent stories
- Merge results and resolve conflicts

### MUTATION-006: Add Context Compression
**Description:** Summarize progress.txt periodically to prevent context window exhaustion
**Target Metric:** completion_rate
**Risk Level:** Low
**Expected Impact:** Maintain context quality in long-running sessions
**Implementation:**
- Add summary generation every N iterations
- Archive detailed logs, keep summaries in main progress.txt
- Preserve critical patterns and learnings

### MUTATION-007: Implement Semantic Chunking
**Description:** Break large stories into semantic units that can be verified independently
**Target Metric:** completion_rate, code_quality_rate
**Risk Level:** Medium
**Expected Impact:** More granular progress, easier debugging of failures
**Implementation:**
- Add story decomposition phase
- Create sub-tasks with individual verification
- Track completion at chunk level

### When to Use Big Mutations

Big mutations should only be selected when:
1. **Stagnation is confirmed** - 3+ consecutive experiments showed no fitness improvement
2. **Incremental changes exhausted** - Standard hypothesis generation isn't identifying new improvements
3. **Clear metric target** - The big mutation addresses the specific struggling metric

After selecting a big mutation:
1. Create a dedicated experiment branch
2. Implement the full mutation
3. Run against the test PRD
4. Compare results to baseline
5. Merge if fitness improves, discard if not

## Important

- Work on ONE story per iteration
- Commit frequently
- Keep CI green
- Read the Codebase Patterns section in progress.txt before starting
