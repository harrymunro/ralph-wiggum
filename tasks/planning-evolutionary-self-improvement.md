# Planning Summary: Evolutionary Self-Improvement System

Generated: 2026-01-26
Status: Ready for PRD

---

## Round 1: Problem Understanding

- **Problem:** The ralph-wiggum project needs recursive self-improvement, but traditional spec-driven development doesn't fit an evolving system
- **Affected users:** Developers using ralph for autonomous coding loops
- **Current state:** Working MVP with basic loop, circuit breaker, archiving, and test suite
- **Impact:** A self-evolving ralph creates compounding improvements over time

## Round 2: Scope Definition

- **Approach:** Evolutionary/experimental, not spec-driven waterfall
- **Unit of work:** Experiments with hypotheses, not features
- **Fitness metrics:**
  - Loop completion rate (does ralph complete more stories?)
  - Iteration efficiency (fewer iterations per story?)
  - Code quality (fewer lint/type/test failures?)
  - Recovery from failure (better error handling?)
- **Recording locations:**
  - `experiments.json` - Structured metrics and results
  - `progress.txt` - Narrative log (existing)
  - `docs/experiments/` - Detailed analysis per experiment
- **Selection pressure:** Successful mutations persist, failures documented and discarded

## Round 3: Technical Constraints

- **Baseline:** None exists - first experiment must establish metrics baseline
- **Experiment selection:** Fully automated - Ralph analyzes results and generates next hypothesis
- **Failed experiments:** Context-dependent
  - Revert breaking changes (tests fail)
  - Keep non-breaking learnings inline
- **Key infrastructure needed:**
  - Metrics collection system
  - experiments.json schema
  - Hypothesis generation logic in CLAUDE.md
  - Decision framework for revert vs keep

## Round 4: Edge Cases

- **Local maximum escape:** Time-box approach
  - After N experiments with no fitness improvement, force a "big mutation"
  - Big mutation = major structural change vs incremental tweak
- **Self-breaking protection:** Full safety net
  - Always run experiments on branches (main stays stable)
  - Must pass `make test` before experiment considered complete
  - Auto-rollback if tests fail after mutation
- **Runaway prevention:** Existing circuit breaker (MAX_ATTEMPTS_PER_STORY) is sufficient

## Round 5: Verification Strategy

- **System health metrics:**
  - Fitness trend - are metrics improving over generations?
  - Experiment diversity - exploring different areas or stuck?
  - Self-modification success rate - % of experiments passing smoke tests
- **First generation:** Full loop proof
  - Establish baseline → make mutation → measure → record → propose next
  - Proves the evolutionary loop works end-to-end
- **Completion definition:** Never "done"
  - PRD bootstraps an ongoing evolutionary process
  - Success = self-sustaining improvement cycle
- **Ultimate goal:** Ralph becomes fully self-directing
  - Humans review results but don't guide direction
  - Ralph proposes its own hypotheses based on data

---

## Key Design Decisions

1. **Experiments, not features** - Each "story" is a hypothesis to test, not a spec to implement
2. **Multi-dimensional fitness** - Track 4+ metrics to avoid optimizing for wrong thing
3. **Full automation goal** - Ralph should eventually select its own experiments
4. **Safety-first evolution** - Git branches + test gates + auto-rollback
5. **Escape hatches** - Time-boxed big mutations prevent local maxima traps
6. **Perpetual process** - No end state, just ongoing improvement

---

## Experiment Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    EXPERIMENT LIFECYCLE                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. HYPOTHESIZE                                             │
│     └── Ralph analyzes current metrics + past experiments   │
│     └── Generates hypothesis: "If X then Y improves"        │
│     └── Records in experiments.json (status: proposed)      │
│                                                             │
│  2. MUTATE                                                  │
│     └── Create feature branch                               │
│     └── Implement the change                                │
│     └── Run smoke tests (make test)                         │
│     └── If tests fail → rollback, record failure, goto 1    │
│                                                             │
│  3. MEASURE                                                 │
│     └── Run ralph loop on test problem                      │
│     └── Collect metrics: completion, iterations, quality    │
│     └── Compare to baseline                                 │
│                                                             │
│  4. SELECT                                                  │
│     └── If fitness improved → merge to main, update baseline│
│     └── If no improvement → keep learnings, discard change  │
│     └── If stagnant (N experiments) → trigger big mutation  │
│                                                             │
│  5. RECORD                                                  │
│     └── Update experiments.json with results                │
│     └── Write docs/experiments/EXP-NNN.md analysis          │
│     └── Append summary to progress.txt                      │
│     └── Goto 1 (next generation)                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. Create PRD with experiment-based stories (not feature-based)
2. First experiments should bootstrap the infrastructure
3. Later experiments use that infrastructure to evolve ralph itself
