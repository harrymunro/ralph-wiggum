# PRD: Evolutionary Self-Improvement System

## Introduction

Bootstrap an evolutionary system where Ralph improves itself through experimentation. Instead of predetermined features, Ralph runs experiments with hypotheses, measures fitness metrics, and selects successful mutations. The system becomes self-directing over time.

This is not a traditional PRD. It bootstraps an ongoing evolutionary process that has no end state.

## Goals

- Establish baseline metrics for Ralph's current performance
- Create infrastructure for tracking experiments and results
- Run a complete evolutionary loop end-to-end (proof of concept)
- Enable Ralph to generate its own hypotheses based on data
- Build escape hatches for local maxima (stagnation detection)

## Fitness Metrics

All experiments measure improvement against these dimensions:

| Metric | Description | How Measured |
|--------|-------------|--------------|
| Completion Rate | % of stories Ralph completes successfully | `passes: true` count / total stories |
| Iteration Efficiency | Average iterations needed per story | Total iterations / completed stories |
| Code Quality | % of iterations with clean lint/type/test | Clean runs / total runs |
| Recovery Rate | % of failures that recover in next iteration | Recovered failures / total failures |

## Experiments

### EXP-001: Establish Baseline Metrics

**Hypothesis:** We cannot improve what we don't measure. Establishing baseline metrics enables future experiments to demonstrate improvement.

**Mutation:**
- Create `experiments.json` schema with baseline metrics structure
- Add metrics collection to ralph.sh (capture iteration counts, pass/fail per story)
- Run ralph on `prd.json.example` (or create a test PRD) to establish baseline numbers

**Acceptance Criteria:**
- experiments.json exists with schema: `{ baseline: {...}, experiments: [...] }`
- ralph.sh outputs metrics summary at end of run
- Baseline metrics recorded for: completion_rate, avg_iterations, code_quality_rate
- `make test` passes

**Fitness Test:** N/A (this establishes the baseline)

---

### EXP-002: Create Experiment Recording Infrastructure

**Hypothesis:** Structured experiment recording enables Ralph to analyze past results and generate informed hypotheses.

**Mutation:**
- Create `docs/experiments/` directory structure
- Add experiment template: `docs/experiments/TEMPLATE.md`
- Update CLAUDE.md with instructions for recording experiment results
- Create helper in ralph.sh to initialize new experiment files

**Acceptance Criteria:**
- `docs/experiments/TEMPLATE.md` exists with sections: Hypothesis, Mutation, Results, Learnings
- CLAUDE.md contains "Experiment Recording" section with clear instructions
- Running `./ralph.sh` creates experiment record when in experiment mode
- `make test` passes

**Fitness Test:** Infrastructure only - no fitness comparison yet

---

### EXP-003: First Complete Evolutionary Loop

**Hypothesis:** A complete experiment cycle (hypothesize → mutate → measure → select → record) can run end-to-end, proving the evolutionary system works.

**Mutation:**
- Update CLAUDE.md with full experiment lifecycle instructions
- Add `--experiment` flag to ralph.sh that enables experiment mode
- Implement: branch creation, mutation, measurement, comparison to baseline, recording
- Run one real experiment: "Improve error message clarity in CLAUDE.md"

**Acceptance Criteria:**
- `./ralph.sh --experiment` runs full lifecycle
- Experiment creates feature branch automatically
- Metrics collected and compared to baseline
- Results recorded in experiments.json and docs/experiments/EXP-003.md
- Decision made: merge (improved) or discard (no improvement)
- `make test` passes

**Fitness Test:** Compare metrics to EXP-001 baseline. Success = loop completes, regardless of fitness change.

---

### EXP-004: Automated Hypothesis Generation

**Hypothesis:** Ralph can analyze past experiment results and propose the next experiment without human guidance.

**Mutation:**
- Add "Hypothesis Generation" section to CLAUDE.md
- Include analysis framework: review experiments.json, identify lowest-performing metric, propose targeted improvement
- Add `--next-experiment` flag that outputs proposed hypothesis without running
- Test: Ralph proposes a sensible next experiment based on EXP-001-003 data

**Acceptance Criteria:**
- CLAUDE.md contains hypothesis generation instructions
- `./ralph.sh --next-experiment` outputs a structured hypothesis
- Hypothesis references actual data from experiments.json
- Proposed experiment targets a real weakness in current metrics
- `make test` passes

**Fitness Test:** Qualitative - does the proposed hypothesis make sense given the data?

---

### EXP-005: Stagnation Detection and Big Mutations

**Hypothesis:** Without escape hatches, the system may get stuck in local maxima. Detecting stagnation and forcing "big mutations" enables exploration of new solution spaces.

**Mutation:**
- Add stagnation detection: track last N experiments, flag if no fitness improvement
- Define "big mutation" catalog: major structural changes vs incremental tweaks
- Add `--force-big-mutation` flag for manual trigger
- Auto-trigger big mutation after 3 stagnant experiments

**Acceptance Criteria:**
- experiments.json tracks `stagnation_count` field
- ralph.sh detects when last 3 experiments showed no improvement
- Big mutation catalog exists in CLAUDE.md (at least 5 major change ideas)
- Stagnation triggers selection from big mutation catalog
- `make test` passes

**Fitness Test:** Simulate stagnation scenario, verify big mutation triggers correctly.

---

### EXP-006: Self-Directing Evolution

**Hypothesis:** With all infrastructure in place, Ralph can run multiple experiment generations autonomously, with humans only reviewing results.

**Mutation:**
- Combine all previous capabilities into autonomous mode
- Add `--generations N` flag to run N experiment cycles
- Add safety limits: max iterations, cost tracking, auto-stop on repeated failures
- Create summary report generation after N generations

**Acceptance Criteria:**
- `./ralph.sh --generations 3` runs 3 complete experiment cycles
- Each generation: proposes hypothesis → runs experiment → records results → proposes next
- Safety limits prevent runaway (stops after 3 consecutive failures)
- Summary report generated: `docs/experiments/generation-summary.md`
- `make test` passes

**Fitness Test:** Run 3 generations. Success = at least one metric improves across the run.

---

## Non-Goals

- Perfect optimization (we're aiming for continuous improvement, not perfection)
- Guaranteed improvement every experiment (failures are learning opportunities)
- Human-free operation (humans review, just don't direct)
- Replacing the core ralph.sh loop (we're augmenting, not replacing)

## Technical Considerations

- All experiments run on feature branches (main stays stable)
- `make test` is the smoke test gate for all mutations
- Failed experiments are reverted but documented
- experiments.json is the source of truth for metrics and history

## Safety Mechanisms

| Risk | Mitigation |
|------|------------|
| Self-breaking | Git branches + test gates + auto-rollback |
| Infinite loops | Existing circuit breaker (MAX_ATTEMPTS_PER_STORY) |
| Local maxima | Stagnation detection + big mutation trigger |
| Runaway costs | Generation limits + consecutive failure stops |

## Success Metrics

The evolutionary system is working when:
1. Fitness metrics trend upward over 5+ generations
2. Experiment diversity is maintained (not stuck on one area)
3. Self-modification success rate > 50% (experiments pass smoke tests)
4. Ralph proposes sensible hypotheses without human guidance

## Open Questions

- What's the right stagnation threshold (3 experiments? 5?)
- Should big mutations be random or targeted at weakest metric?
- How do we measure "experiment diversity" quantitatively?
- Should there be a "hall of fame" for most successful experiments?
