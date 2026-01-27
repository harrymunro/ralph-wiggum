#!/bin/bash
# Ralph Wiggum - Long-running AI agent loop for Claude Code
# Usage: ./ralph.sh [max_iterations] [--skip-security-check]

set -e

# Parse arguments
MAX_ITERATIONS=10
MAX_ATTEMPTS_PER_STORY="${MAX_ATTEMPTS_PER_STORY:-5}"
SKIP_SECURITY="${SKIP_SECURITY_CHECK:-false}"

while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-security-check)
      SKIP_SECURITY="true"
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
exit 1
