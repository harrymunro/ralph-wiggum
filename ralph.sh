#!/bin/bash
# Ralph Wiggum - Long-running AI agent loop for Claude Code
# Usage: ./ralph.sh [max_iterations] [--skip-security-check]

set -e

# Parse arguments
MAX_ITERATIONS=10
MAX_ATTEMPTS_PER_STORY="${MAX_ATTEMPTS_PER_STORY:-5}"
SKIP_SECURITY="${SKIP_SECURITY_CHECK:-false}"
EXPERIMENT_MODE="false"
EXPERIMENT_ID=""
NEXT_EXPERIMENT_MODE="false"

while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-security-check)
      SKIP_SECURITY="true"
      shift
      ;;
    --experiment)
      EXPERIMENT_MODE="true"
      # Check if next argument is an experiment ID (not another flag)
      if [[ -n "${2:-}" && ! "$2" =~ ^-- ]]; then
        EXPERIMENT_ID="$2"
        shift
      fi
      shift
      ;;
    --next-experiment)
      NEXT_EXPERIMENT_MODE="true"
      shift
      ;;
    *)
      # Assume it's max_iterations if it's a number
      if [[ "$1" =~ ^[0-9]+$ ]]; then
        MAX_ITERATIONS="$1"
      fi
      shift
      ;;
  esac
done

# Security Pre-Flight Check
if [[ "$SKIP_SECURITY" != "true" ]]; then
  echo ""
  echo "==============================================================="
  echo "  Security Pre-Flight Check"
  echo "==============================================================="
  echo ""

  SECURITY_WARNINGS=()

  if [[ -n "${AWS_ACCESS_KEY_ID:-}" ]]; then
    SECURITY_WARNINGS+=("AWS_ACCESS_KEY_ID is set - production credentials may be exposed")
  fi

  if [[ -n "${DATABASE_URL:-}" ]]; then
    SECURITY_WARNINGS+=("DATABASE_URL is set - database credentials may be exposed")
  fi

  if [[ ${#SECURITY_WARNINGS[@]} -gt 0 ]]; then
    echo "WARNING: Potential credential exposure detected:"
    echo ""
    for warning in "${SECURITY_WARNINGS[@]}"; do
      echo "  - $warning"
    done
    echo ""
    echo "Running an autonomous agent with these credentials set could expose"
    echo "them in logs, commit messages, or API calls."
    echo ""
    echo "See docs/SECURITY.md for sandboxing guidance."
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Aborted. Unset credentials or use --skip-security-check to bypass."
      exit 1
    fi
  else
    echo "No credential exposure risks detected."
  fi
  echo ""
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRD_FILE="$SCRIPT_DIR/prd.json"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
ARCHIVE_DIR="$SCRIPT_DIR/archive"
LAST_BRANCH_FILE="$SCRIPT_DIR/.last-branch"
EXPERIMENTS_FILE="$SCRIPT_DIR/experiments.json"

# Function to check if stagnation is detected (3+ consecutive experiments with no improvement)
check_stagnation() {
  if [[ ! -f "$EXPERIMENTS_FILE" ]]; then
    echo "false"
    return
  fi

  local stagnation_count=$(jq -r '.stagnation_count // 0' "$EXPERIMENTS_FILE")
  if [[ "$stagnation_count" -ge 3 ]]; then
    echo "true"
  else
    echo "false"
  fi
}

# Function to update stagnation count after an experiment
update_stagnation_count() {
  local delta_fitness="$1"

  if [[ ! -f "$EXPERIMENTS_FILE" ]]; then
    return
  fi

  # Check if there was improvement (delta_fitness > 0)
  local improved=$(echo "$delta_fitness > 0" | bc -l 2>/dev/null || echo "0")

  if [[ "$improved" -eq 1 ]]; then
    # Reset stagnation count and update last_improvement_at
    local current_date=$(date +%Y-%m-%d)
    jq --arg date "$current_date" '.stagnation_count = 0 | .last_improvement_at = $date' "$EXPERIMENTS_FILE" > "$EXPERIMENTS_FILE.tmp" && \
      mv "$EXPERIMENTS_FILE.tmp" "$EXPERIMENTS_FILE"
    echo "  Fitness improved - stagnation count reset to 0"
  else
    # Increment stagnation count
    local new_count=$(jq -r '.stagnation_count + 1' "$EXPERIMENTS_FILE")
    jq '.stagnation_count += 1' "$EXPERIMENTS_FILE" > "$EXPERIMENTS_FILE.tmp" && \
      mv "$EXPERIMENTS_FILE.tmp" "$EXPERIMENTS_FILE"
    echo "  No improvement - stagnation count: $new_count"

    if [[ "$new_count" -ge 3 ]]; then
      echo ""
      echo "  WARNING: Stagnation detected ($new_count consecutive experiments without improvement)"
      echo "  Consider using a big mutation from the catalog in CLAUDE.md"
    fi
  fi
}

# Big Mutation Catalog - major structural changes to escape local maxima
BIG_MUTATIONS=(
  "MUTATION-001|Restructure PRD Format|Change PRD from flat user stories to hierarchical epics with dependencies"
  "MUTATION-002|Add Pre-Implementation Analysis|Add mandatory codebase exploration phase before any code changes"
  "MUTATION-003|Implement Rollback Checkpoints|Add git-based checkpoints every N iterations with automatic rollback on failure"
  "MUTATION-004|Add Test-First Verification|Require writing tests before implementation for each acceptance criterion"
  "MUTATION-005|Implement Parallel Story Execution|Allow concurrent work on independent stories to increase throughput"
  "MUTATION-006|Add Context Compression|Summarize progress.txt periodically to prevent context window exhaustion"
  "MUTATION-007|Implement Semantic Chunking|Break large stories into semantic units that can be verified independently"
)

# Function to select a big mutation from the catalog
select_big_mutation() {
  if [[ ! -f "$EXPERIMENTS_FILE" ]]; then
    echo "Error: experiments.json not found"
    return 1
  fi

  echo ""
  echo "==============================================================="
  echo "  Big Mutation Selection (Stagnation Escape)"
  echo "==============================================================="
  echo ""

  # Get list of previously tried mutations from experiments
  local tried_mutations=$(jq -r '.experiments[]? | select(.hypothesis | test("MUTATION-[0-9]+")) | .hypothesis' "$EXPERIMENTS_FILE" 2>/dev/null | grep -o 'MUTATION-[0-9]*' || echo "")

  echo "  Stagnation detected - selecting from big mutation catalog..."
  echo ""

  # Find first untried mutation
  local selected_mutation=""
  for mutation in "${BIG_MUTATIONS[@]}"; do
    local mutation_id=$(echo "$mutation" | cut -d'|' -f1)
    local mutation_name=$(echo "$mutation" | cut -d'|' -f2)
    local mutation_desc=$(echo "$mutation" | cut -d'|' -f3)

    if [[ ! "$tried_mutations" =~ "$mutation_id" ]]; then
      selected_mutation="$mutation"
      break
    fi
  done

  if [[ -z "$selected_mutation" ]]; then
    echo "  All big mutations have been tried. Consider defining new mutations."
    echo ""
    # Return the first mutation as fallback
    selected_mutation="${BIG_MUTATIONS[0]}"
  fi

  local mutation_id=$(echo "$selected_mutation" | cut -d'|' -f1)
  local mutation_name=$(echo "$selected_mutation" | cut -d'|' -f2)
  local mutation_desc=$(echo "$selected_mutation" | cut -d'|' -f3)

  echo "  Selected Big Mutation:"
  echo "    ID:          $mutation_id"
  echo "    Name:        $mutation_name"
  echo "    Description: $mutation_desc"
  echo ""

  # Output as JSON for programmatic use
  echo "  {"
  echo "    \"mutation_id\": \"$mutation_id\","
  echo "    \"mutation_name\": \"$mutation_name\","
  echo "    \"mutation_description\": \"$mutation_desc\""
  echo "  }"
  echo ""
  echo "==============================================================="
}

# Function to generate next experiment hypothesis
generate_next_hypothesis() {
  if [[ ! -f "$EXPERIMENTS_FILE" ]]; then
    echo "Error: experiments.json not found at $EXPERIMENTS_FILE"
    exit 1
  fi

  # Check for stagnation first
  local is_stagnated=$(check_stagnation)

  if [[ "$is_stagnated" == "true" ]]; then
    select_big_mutation
    return
  fi

  echo ""
  echo "==============================================================="
  echo "  Next Experiment Hypothesis Generator"
  echo "==============================================================="
  echo ""

  # Read baseline metrics
  local baseline_completion=$(jq -r '.baseline.completion_rate // 100' "$EXPERIMENTS_FILE")
  local baseline_avg_iter=$(jq -r '.baseline.avg_iterations // 1' "$EXPERIMENTS_FILE")
  local baseline_quality=$(jq -r '.baseline.code_quality_rate // 100' "$EXPERIMENTS_FILE")

  # Read latest experiment metrics (or use baseline if no experiments)
  local exp_count=$(jq '.experiments | length' "$EXPERIMENTS_FILE")
  local current_completion=$baseline_completion
  local current_avg_iter=$baseline_avg_iter
  local current_quality=$baseline_quality

  if [[ "$exp_count" -gt 0 ]]; then
    current_completion=$(jq -r '.experiments[-1].metrics.completion_rate // 100' "$EXPERIMENTS_FILE")
    current_avg_iter=$(jq -r '.experiments[-1].metrics.avg_iterations // 1' "$EXPERIMENTS_FILE")
    current_quality=$(jq -r '.experiments[-1].metrics.code_quality_rate // 100' "$EXPERIMENTS_FILE")
  fi

  echo "  Current Metrics Analysis:"
  echo "    Completion Rate:    ${current_completion}% (baseline: ${baseline_completion}%)"
  echo "    Avg Iterations:     ${current_avg_iter} (baseline: ${baseline_avg_iter})"
  echo "    Code Quality Rate:  ${current_quality}% (baseline: ${baseline_quality}%)"
  echo ""

  # Calculate gaps from ideal (completion 100%, iterations 1, quality 100%)
  local completion_gap=$(echo "100 - $current_completion" | bc 2>/dev/null || echo "0")
  local iteration_gap=$(echo "$current_avg_iter - 1" | bc 2>/dev/null || echo "0")
  local quality_gap=$(echo "100 - $current_quality" | bc 2>/dev/null || echo "0")

  # Identify lowest-performing metric (largest gap from ideal)
  local metric_targeted="completion_rate"
  local expected_improvement="+5%"
  local specific_change=""
  local reasoning=""

  # Compare gaps - iteration gap is scaled (1 iteration gap = 10% equivalent)
  local scaled_iteration_gap=$(echo "$iteration_gap * 10" | bc 2>/dev/null || echo "0")

  echo "  Gap Analysis (distance from ideal):"
  echo "    Completion Rate gap: ${completion_gap}%"
  echo "    Avg Iterations gap:  ${iteration_gap} (scaled: ${scaled_iteration_gap}%)"
  echo "    Code Quality gap:    ${quality_gap}%"
  echo ""

  # Determine which metric to target based on largest gap
  if (( $(echo "$completion_gap >= $scaled_iteration_gap && $completion_gap >= $quality_gap" | bc -l 2>/dev/null || echo "0") )); then
    metric_targeted="completion_rate"
    expected_improvement="+5%"
    specific_change="Add clearer story acceptance criteria validation to CLAUDE.md before marking complete"
    reasoning="Completion rate has the largest gap from ideal. Improving validation before completion should reduce incomplete stories."
  elif (( $(echo "$scaled_iteration_gap > $completion_gap && $scaled_iteration_gap >= $quality_gap" | bc -l 2>/dev/null || echo "0") )); then
    metric_targeted="avg_iterations"
    expected_improvement="-0.3 iterations"
    specific_change="Add pre-implementation checklist to CLAUDE.md that identifies required changes before coding"
    reasoning="High iteration count suggests rework. Better upfront planning should reduce iterations needed."
  else
    metric_targeted="code_quality_rate"
    expected_improvement="+5%"
    specific_change="Strengthen quality gate enforcement in ralph.sh with earlier failure detection"
    reasoning="Code quality rate needs improvement. Earlier detection of quality issues will reduce failed attempts."
  fi

  # Generate next experiment ID
  local next_exp_num=1
  if [[ "$exp_count" -gt 0 ]]; then
    local last_exp_num=$(jq -r '.experiments[-1].id // "EXP-000"' "$EXPERIMENTS_FILE" | sed 's/EXP-//' | sed 's/^0*//')
    if [[ -z "$last_exp_num" || "$last_exp_num" == "null" ]]; then
      last_exp_num=0
    fi
    next_exp_num=$((last_exp_num + 1))
  fi
  local next_exp_id=$(printf "EXP-%03d" "$next_exp_num")

  echo "  Proposed Hypothesis:"
  echo "  ===================="
  echo ""
  echo "  {"
  echo "    \"experiment_id\": \"$next_exp_id\","
  echo "    \"metric_targeted\": \"$metric_targeted\","
  echo "    \"expected_improvement\": \"$expected_improvement\","
  echo "    \"specific_change\": \"$specific_change\","
  echo "    \"reasoning\": \"$reasoning\""
  echo "  }"
  echo ""
  echo "==============================================================="
  echo ""
  echo "To run this experiment:"
  echo "  ./ralph.sh --experiment $next_exp_id"
  echo ""
}

# Handle --next-experiment flag
if [[ "$NEXT_EXPERIMENT_MODE" == "true" ]]; then
  generate_next_hypothesis
  exit 0
fi

# Experiment mode setup
if [[ "$EXPERIMENT_MODE" == "true" ]]; then
  echo ""
  echo "==============================================================="
  echo "  Experiment Mode Enabled"
  echo "==============================================================="
  echo ""

  # Generate experiment ID if not provided
  if [[ -z "$EXPERIMENT_ID" ]]; then
    # Get next experiment number from experiments.json
    if [[ -f "$EXPERIMENTS_FILE" ]]; then
      LAST_EXP_NUM=$(jq -r '.experiments[-1].id // "EXP-000"' "$EXPERIMENTS_FILE" | sed 's/EXP-//' | sed 's/^0*//')
      if [[ -z "$LAST_EXP_NUM" || "$LAST_EXP_NUM" == "null" ]]; then
        LAST_EXP_NUM=0
      fi
      NEXT_EXP_NUM=$((LAST_EXP_NUM + 1))
      EXPERIMENT_ID=$(printf "EXP-%03d" "$NEXT_EXP_NUM")
    else
      EXPERIMENT_ID="EXP-001"
    fi
  fi

  echo "  Experiment ID: $EXPERIMENT_ID"

  # Create experiment feature branch
  EXPERIMENT_BRANCH="ralph/experiment-${EXPERIMENT_ID,,}"
  CURRENT_GIT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")

  if [[ -n "$CURRENT_GIT_BRANCH" ]]; then
    echo "  Current branch: $CURRENT_GIT_BRANCH"
    echo "  Creating experiment branch: $EXPERIMENT_BRANCH"

    # Check if branch already exists
    if git show-ref --verify --quiet "refs/heads/$EXPERIMENT_BRANCH" 2>/dev/null; then
      echo "  Branch already exists, checking it out..."
      git checkout "$EXPERIMENT_BRANCH"
    else
      git checkout -b "$EXPERIMENT_BRANCH"
    fi
    echo "  Experiment branch created/checked out: $EXPERIMENT_BRANCH"
  else
    echo "  WARNING: Not in a git repository, skipping branch creation"
  fi

  # Record experiment start time
  EXPERIMENT_START_TIME=$(date +%s)
  EXPERIMENT_DATE=$(date +%Y-%m-%d)
  echo ""
fi

# Archive previous run if branch changed
if [ -f "$PRD_FILE" ] && [ -f "$LAST_BRANCH_FILE" ]; then
  CURRENT_BRANCH=$(jq -r '.branchName // empty' "$PRD_FILE" 2>/dev/null || echo "")
  LAST_BRANCH=$(cat "$LAST_BRANCH_FILE" 2>/dev/null || echo "")

  if [ -n "$CURRENT_BRANCH" ] && [ -n "$LAST_BRANCH" ] && [ "$CURRENT_BRANCH" != "$LAST_BRANCH" ]; then
    # Archive the previous run
    DATE=$(date +%Y-%m-%d)
    # Strip "ralph/" prefix from branch name for folder
    FOLDER_NAME=$(echo "$LAST_BRANCH" | sed 's|^ralph/||')
    ARCHIVE_FOLDER="$ARCHIVE_DIR/$DATE-$FOLDER_NAME"

    echo "Archiving previous run: $LAST_BRANCH"
    mkdir -p "$ARCHIVE_FOLDER"
    [ -f "$PRD_FILE" ] && cp "$PRD_FILE" "$ARCHIVE_FOLDER/"
    [ -f "$PROGRESS_FILE" ] && cp "$PROGRESS_FILE" "$ARCHIVE_FOLDER/"
    echo "   Archived to: $ARCHIVE_FOLDER"

    # Reset progress file for new run
    echo "# Ralph Progress Log" > "$PROGRESS_FILE"
    echo "Started: $(date)" >> "$PROGRESS_FILE"
    echo "---" >> "$PROGRESS_FILE"
  fi
fi

# Track current branch
if [ -f "$PRD_FILE" ]; then
  CURRENT_BRANCH=$(jq -r '.branchName // empty' "$PRD_FILE" 2>/dev/null || echo "")
  if [ -n "$CURRENT_BRANCH" ]; then
    echo "$CURRENT_BRANCH" > "$LAST_BRANCH_FILE"
  fi
fi

# Initialize progress file if it doesn't exist
if [ ! -f "$PROGRESS_FILE" ]; then
  echo "# Ralph Progress Log" > "$PROGRESS_FILE"
  echo "Started: $(date)" >> "$PROGRESS_FILE"
  echo "---" >> "$PROGRESS_FILE"
fi

# Circuit breaker: track attempts per story
ATTEMPTS_FILE="$SCRIPT_DIR/.story-attempts"
LAST_STORY_FILE="$SCRIPT_DIR/.last-story"

# Initialize attempts tracking
if [ ! -f "$ATTEMPTS_FILE" ]; then
  echo "{}" > "$ATTEMPTS_FILE"
fi

# Function to get current story being worked on
get_current_story() {
  if [ -f "$PRD_FILE" ]; then
    jq -r '.userStories[] | select(.passes == false) | .id' "$PRD_FILE" 2>/dev/null | head -1
  fi
}

# Function to get attempts for a story
get_story_attempts() {
  local story_id="$1"
  jq -r --arg id "$story_id" '.[$id] // 0' "$ATTEMPTS_FILE" 2>/dev/null || echo "0"
}

# Function to increment attempts for a story
increment_story_attempts() {
  local story_id="$1"
  local current=$(get_story_attempts "$story_id")
  local new_count=$((current + 1))
  jq --arg id "$story_id" --argjson count "$new_count" '.[$id] = $count' "$ATTEMPTS_FILE" > "$ATTEMPTS_FILE.tmp" && mv "$ATTEMPTS_FILE.tmp" "$ATTEMPTS_FILE"
  echo "$new_count"
}

# Function to mark story as skipped due to max attempts
mark_story_skipped() {
  local story_id="$1"
  local max_attempts="$2"
  local note="Skipped: exceeded $max_attempts attempts without passing"
  jq --arg id "$story_id" --arg note "$note" '
    .userStories = [.userStories[] | if .id == $id then .notes = $note else . end]
  ' "$PRD_FILE" > "$PRD_FILE.tmp" && mv "$PRD_FILE.tmp" "$PRD_FILE"
  echo "Circuit breaker: Marked story $story_id as skipped after $max_attempts attempts"
}

# Function to check and apply circuit breaker
check_circuit_breaker() {
  local story_id="$1"
  local attempts=$(get_story_attempts "$story_id")

  if [ "$attempts" -ge "$MAX_ATTEMPTS_PER_STORY" ]; then
    echo "Circuit breaker: Story $story_id has reached max attempts ($attempts/$MAX_ATTEMPTS_PER_STORY)"
    mark_story_skipped "$story_id" "$MAX_ATTEMPTS_PER_STORY"
    return 0  # true - circuit breaker tripped
  fi
  return 1  # false - circuit breaker not tripped
}

# Initialize metrics tracking
METRICS_ITERATIONS=0
METRICS_STORIES_COMPLETED=0
METRICS_STORIES_FAILED=0
METRICS_QUALITY_PASSES=0
METRICS_QUALITY_FAILS=0

# Function to count completed stories
count_completed_stories() {
  if [ -f "$PRD_FILE" ]; then
    jq '[.userStories[] | select(.passes == true)] | length' "$PRD_FILE" 2>/dev/null || echo "0"
  else
    echo "0"
  fi
}

# Function to count total stories
count_total_stories() {
  if [ -f "$PRD_FILE" ]; then
    jq '[.userStories[]] | length' "$PRD_FILE" 2>/dev/null || echo "0"
  else
    echo "0"
  fi
}

# Function to count skipped stories
count_skipped_stories() {
  if [ -f "$PRD_FILE" ]; then
    jq '[.userStories[] | select(.notes | contains("Skipped"))] | length' "$PRD_FILE" 2>/dev/null || echo "0"
  else
    echo "0"
  fi
}

# Function to compare metrics with baseline and record experiment results
record_experiment_results() {
  if [[ "$EXPERIMENT_MODE" != "true" ]]; then
    return
  fi

  local completed=$(count_completed_stories)
  local total=$(count_total_stories)
  local skipped=$(count_skipped_stories)
  local completion_rate=0
  local avg_iterations=0

  if [ "$total" -gt 0 ]; then
    completion_rate=$(echo "scale=2; $completed * 100 / $total" | bc 2>/dev/null || echo "0")
  fi

  if [ "$completed" -gt 0 ]; then
    avg_iterations=$(echo "scale=2; $METRICS_ITERATIONS / $completed" | bc 2>/dev/null || echo "0")
  fi

  # Calculate code quality rate (passed / (passed + skipped))
  local passed_and_skipped=$((completed + skipped))
  local code_quality_rate=100
  if [ "$passed_and_skipped" -gt 0 ]; then
    code_quality_rate=$(echo "scale=2; $completed * 100 / $passed_and_skipped" | bc 2>/dev/null || echo "100")
  fi

  echo ""
  echo "==============================================================="
  echo "  Experiment Results: $EXPERIMENT_ID"
  echo "==============================================================="
  echo ""

  # Read baseline from experiments.json
  if [[ -f "$EXPERIMENTS_FILE" ]]; then
    local baseline_completion=$(jq -r '.baseline.completion_rate // 0' "$EXPERIMENTS_FILE")
    local baseline_avg_iter=$(jq -r '.baseline.avg_iterations // 0' "$EXPERIMENTS_FILE")
    local baseline_quality=$(jq -r '.baseline.code_quality_rate // 100' "$EXPERIMENTS_FILE")

    # Calculate deltas
    local delta_completion=$(echo "scale=2; $completion_rate - $baseline_completion" | bc 2>/dev/null || echo "0")
    local delta_avg_iter=$(echo "scale=2; $avg_iterations - $baseline_avg_iter" | bc 2>/dev/null || echo "0")
    local delta_quality=$(echo "scale=2; $code_quality_rate - $baseline_quality" | bc 2>/dev/null || echo "0")

    echo "  Metrics Comparison to Baseline:"
    echo "    Completion Rate: ${completion_rate}% (baseline: ${baseline_completion}%, delta: ${delta_completion}%)"
    echo "    Avg Iterations:  ${avg_iterations} (baseline: ${baseline_avg_iter}, delta: ${delta_avg_iter})"
    echo "    Code Quality:    ${code_quality_rate}% (baseline: ${baseline_quality}%, delta: ${delta_quality}%)"
    echo ""

    # Determine outcome
    local outcome="completed"
    local success=$([[ "$completion_rate" == "100" || "$completion_rate" == "100.00" ]] && echo "true" || echo "false")

    # Calculate fitness delta (simple: average of improvements across metrics)
    # For avg_iterations, negative is good (fewer iterations = better)
    local delta_fitness=$(echo "scale=2; ($delta_completion - $delta_avg_iter * 10 + $delta_quality) / 3" | bc 2>/dev/null || echo "0")

    echo "  Fitness Delta: ${delta_fitness}"
    echo ""

    # Record to experiments.json
    local experiment_entry=$(cat <<EOF
{
  "id": "$EXPERIMENT_ID",
  "date": "$EXPERIMENT_DATE",
  "hypothesis": "Experiment run",
  "metrics": {
    "completion_rate": $completion_rate,
    "avg_iterations": $avg_iterations,
    "code_quality_rate": $code_quality_rate
  },
  "outcome": "$outcome",
  "delta_fitness": $delta_fitness
}
EOF
)

    # Add experiment to experiments.json
    jq --argjson exp "$experiment_entry" '.experiments += [$exp]' "$EXPERIMENTS_FILE" > "$EXPERIMENTS_FILE.tmp" && \
      mv "$EXPERIMENTS_FILE.tmp" "$EXPERIMENTS_FILE"

    echo "  Results recorded to experiments.json"

    # Create experiment markdown file
    local exp_md_file="$SCRIPT_DIR/docs/experiments/${EXPERIMENT_ID}.md"
    mkdir -p "$(dirname "$exp_md_file")"

    cat > "$exp_md_file" <<EOF
# Experiment: $EXPERIMENT_ID

## Metadata
- **Date:** $EXPERIMENT_DATE
- **Status:** completed
- **Branch:** $EXPERIMENT_BRANCH

## Hypothesis

> Evolutionary loop experiment run.

## Mutation

### Changes Made
- Experiment run automatically by ralph.sh --experiment

### Files Modified
- Various files modified during experiment run

## Results

### Metrics (compared to baseline)

| Metric | Baseline | This Experiment | Delta |
|--------|----------|-----------------|-------|
| Completion Rate | ${baseline_completion}% | ${completion_rate}% | ${delta_completion}% |
| Avg Iterations | ${baseline_avg_iter} | ${avg_iterations} | ${delta_avg_iter} |
| Code Quality Rate | ${baseline_quality}% | ${code_quality_rate}% | ${delta_quality}% |

### Outcome
- [x] **Completed** - Experiment finished
- Fitness Delta: ${delta_fitness}

## Learnings

### What Worked
- (To be filled in manually)

### What Didn't Work
- (To be filled in manually)

### Unexpected Discoveries
- (To be filled in manually)

## Next Hypothesis

Based on these results, the next experiment should explore:

> (To be determined based on analysis)
EOF

    echo "  Experiment documented in $exp_md_file"

    # Update stagnation tracking
    update_stagnation_count "$delta_fitness"
  else
    echo "  WARNING: experiments.json not found, cannot compare to baseline"
  fi

  echo "==============================================================="
}

# Function to output metrics summary
output_metrics_summary() {
  local completed=$(count_completed_stories)
  local total=$(count_total_stories)
  local skipped=$(count_skipped_stories)
  local completion_rate=0

  if [ "$total" -gt 0 ]; then
    completion_rate=$(echo "scale=2; $completed * 100 / $total" | bc 2>/dev/null || echo "0")
  fi

  echo ""
  echo "==============================================================="
  echo "  Ralph Metrics Summary"
  echo "==============================================================="
  echo ""
  echo "  Stories:"
  echo "    - Completed: $completed / $total"
  echo "    - Skipped:   $skipped"
  echo "    - Completion Rate: ${completion_rate}%"
  echo ""
  echo "  Iterations:"
  echo "    - Total iterations: $METRICS_ITERATIONS"
  if [ "$completed" -gt 0 ]; then
    local avg_iterations=$(echo "scale=2; $METRICS_ITERATIONS / $completed" | bc 2>/dev/null || echo "N/A")
    echo "    - Avg iterations per story: $avg_iterations"
  fi
  echo ""
  echo "==============================================================="
}

echo "Starting Ralph - Max iterations: $MAX_ITERATIONS - Max attempts per story: $MAX_ATTEMPTS_PER_STORY"

# Record initial completed count to track progress
INITIAL_COMPLETED=$(count_completed_stories)

for i in $(seq 1 $MAX_ITERATIONS); do
  METRICS_ITERATIONS=$i
  echo ""
  echo "==============================================================="
  echo "  Ralph Iteration $i of $MAX_ITERATIONS"
  echo "==============================================================="

  # Get current story and check circuit breaker
  CURRENT_STORY=$(get_current_story)

  if [ -n "$CURRENT_STORY" ]; then
    # Check if this is the same story as last iteration (consecutive failure detection)
    LAST_STORY=""
    if [ -f "$LAST_STORY_FILE" ]; then
      LAST_STORY=$(cat "$LAST_STORY_FILE" 2>/dev/null || echo "")
    fi

    if [ "$CURRENT_STORY" == "$LAST_STORY" ]; then
      echo "Consecutive attempt on story: $CURRENT_STORY"
      ATTEMPTS=$(increment_story_attempts "$CURRENT_STORY")
      echo "Attempts on $CURRENT_STORY: $ATTEMPTS/$MAX_ATTEMPTS_PER_STORY"

      # Check circuit breaker
      if check_circuit_breaker "$CURRENT_STORY"; then
        echo "Skipping to next story..."
        echo "$CURRENT_STORY" > "$LAST_STORY_FILE"
        sleep 1
        continue
      fi
    else
      # New story, record first attempt
      if [ -n "$CURRENT_STORY" ]; then
        ATTEMPTS=$(increment_story_attempts "$CURRENT_STORY")
        echo "Starting story: $CURRENT_STORY (attempt $ATTEMPTS/$MAX_ATTEMPTS_PER_STORY)"
      fi
    fi

    # Record current story for next iteration
    echo "$CURRENT_STORY" > "$LAST_STORY_FILE"
  else
    echo "No incomplete stories found"
  fi

  # Run Claude Code with the ralph prompt
  OUTPUT=$(claude --dangerously-skip-permissions --print < "$SCRIPT_DIR/CLAUDE.md" 2>&1 | tee /dev/stderr) || true

  # Check for completion signal
  if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
    echo ""
    echo "COMPLETE signal received. Verifying all stories pass..."

    # Verify all stories actually have passes:true
    INCOMPLETE_STORIES=$(jq -r '.userStories[] | select(.passes == false) | .id' "$PRD_FILE" 2>/dev/null || echo "")

    if [ -z "$INCOMPLETE_STORIES" ]; then
      echo "Verification passed: All stories have passes:true"
      echo ""
      echo "Ralph completed all tasks!"
      echo "Completed at iteration $i of $MAX_ITERATIONS"
      output_metrics_summary
      record_experiment_results
      exit 0
    else
      echo ""
      echo "WARNING: COMPLETE claimed but verification failed!"
      echo "The following stories still have passes:false:"
      echo "$INCOMPLETE_STORIES" | while read -r story_id; do
        echo "  - $story_id"
      done
      echo ""
      echo "Continuing iteration to fix incomplete stories..."
    fi
  fi

  echo "Iteration $i complete. Continuing..."
  sleep 2
done

echo ""
echo "Ralph reached max iterations ($MAX_ITERATIONS) without completing all tasks."
echo "Check $PROGRESS_FILE for status."
output_metrics_summary
record_experiment_results
exit 1
