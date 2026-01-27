#!/bin/bash
# Common test helper functions for ralph.sh tests

# Directory where ralph.sh lives
export RALPH_DIR="$(cd "$(dirname "${BATS_TEST_DIRNAME}")" && pwd)"
export RALPH_SCRIPT="$RALPH_DIR/ralph.sh"

# Create a temporary test directory for each test
setup_test_environment() {
  export TEST_DIR="$(mktemp -d)"
  export SCRIPT_DIR="$TEST_DIR"

  # Copy ralph.sh to test directory
  cp "$RALPH_SCRIPT" "$TEST_DIR/ralph.sh"

  # Create minimal CLAUDE.md
  cat > "$TEST_DIR/CLAUDE.md" << 'EOF'
# Test CLAUDE.md
Test instructions
EOF

  # Set up PATH to use mock claude
  export ORIGINAL_PATH="$PATH"
  export PATH="$TEST_DIR/bin:$PATH"

  # Create bin directory for mocks
  mkdir -p "$TEST_DIR/bin"
}

# Cleanup test environment after each test
teardown_test_environment() {
  if [ -n "$TEST_DIR" ] && [ -d "$TEST_DIR" ]; then
    rm -rf "$TEST_DIR"
  fi
  export PATH="$ORIGINAL_PATH"
}

# Create a PRD file with specified content
create_prd() {
  local content="$1"
  echo "$content" > "$TEST_DIR/prd.json"
}

# Create a progress file
create_progress_file() {
  local content="${1:-# Ralph Progress Log}"
  echo "$content" > "$TEST_DIR/progress.txt"
}

# Create .last-branch file
create_last_branch() {
  local branch="$1"
  echo "$branch" > "$TEST_DIR/.last-branch"
}

# Create .story-attempts file
create_story_attempts() {
  local content="${1:-{}}"
  echo "$content" > "$TEST_DIR/.story-attempts"
}

# Create .last-story file
create_last_story() {
  local story="$1"
  echo "$story" > "$TEST_DIR/.last-story"
}

# Source ralph.sh functions without running main script
# This sources only the function definitions
source_ralph_functions() {
  # Extract and source just the functions from ralph.sh
  # We need to be careful to not execute the main script logic

  # Set required variables that would normally be set during script execution
  export PRD_FILE="$TEST_DIR/prd.json"
  export PROGRESS_FILE="$TEST_DIR/progress.txt"
  export ARCHIVE_DIR="$TEST_DIR/archive"
  export LAST_BRANCH_FILE="$TEST_DIR/.last-branch"
  export ATTEMPTS_FILE="$TEST_DIR/.story-attempts"
  export LAST_STORY_FILE="$TEST_DIR/.last-story"
  export MAX_ATTEMPTS_PER_STORY="${MAX_ATTEMPTS_PER_STORY:-5}"

  # Source the function definitions
  eval "$(sed -n '/^get_current_story()/,/^}/p' "$RALPH_SCRIPT")"
  eval "$(sed -n '/^get_story_attempts()/,/^}/p' "$RALPH_SCRIPT")"
  eval "$(sed -n '/^increment_story_attempts()/,/^}/p' "$RALPH_SCRIPT")"
  eval "$(sed -n '/^mark_story_skipped()/,/^}/p' "$RALPH_SCRIPT")"
  eval "$(sed -n '/^check_circuit_breaker()/,/^}/p' "$RALPH_SCRIPT")"
}

# Run ralph.sh with arguments in test directory
run_ralph() {
  cd "$TEST_DIR"
  bash ralph.sh "$@"
}

# Run ralph.sh and capture output (doesn't exit on failure)
run_ralph_capture() {
  cd "$TEST_DIR"
  bash ralph.sh "$@" 2>&1 || true
}

# Assert file exists
assert_file_exists() {
  local file="$1"
  if [ ! -f "$file" ]; then
    echo "Expected file to exist: $file" >&2
    return 1
  fi
}

# Assert file contains string
assert_file_contains() {
  local file="$1"
  local expected="$2"
  if ! grep -q "$expected" "$file"; then
    echo "Expected file $file to contain: $expected" >&2
    echo "Actual contents:" >&2
    cat "$file" >&2
    return 1
  fi
}

# Assert output contains string
assert_output_contains() {
  local expected="$1"
  if [[ "$output" != *"$expected"* ]]; then
    echo "Expected output to contain: $expected" >&2
    echo "Actual output: $output" >&2
    return 1
  fi
}

# Assert output does not contain string
assert_output_not_contains() {
  local unexpected="$1"
  if [[ "$output" == *"$unexpected"* ]]; then
    echo "Expected output NOT to contain: $unexpected" >&2
    echo "Actual output: $output" >&2
    return 1
  fi
}

# Create a PRD with incomplete stories (for hypothesis generation tests)
create_incomplete_prd() {
  cat > "$TEST_DIR/prd.json" << 'EOF'
{
  "project": "test-project",
  "branchName": "ralph/test",
  "description": "Test PRD with incomplete stories",
  "userStories": [
    {
      "id": "US-001",
      "title": "Test Story",
      "description": "A test story",
      "acceptanceCriteria": ["Test passes"],
      "priority": 1,
      "passes": false,
      "notes": ""
    }
  ]
}
EOF
}
