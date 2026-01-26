#!/usr/bin/env bats
# Integration tests for ralph.sh main loop

load 'test_helper/common'
load 'test_helper/mocks'

setup() {
  setup_test_environment
}

teardown() {
  teardown_test_environment
}

@test "Detects COMPLETE signal and exits successfully" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_complete.json" "$TEST_DIR/prd.json"
  create_mock_claude_complete

  run bash "$TEST_DIR/ralph.sh" 1 --skip-security-check

  [ "$status" -eq 0 ]
  [[ "$output" == *"COMPLETE signal received"* ]]
  [[ "$output" == *"Ralph completed all tasks"* ]]
}

@test "Verifies all stories pass after COMPLETE signal" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_complete.json" "$TEST_DIR/prd.json"
  create_mock_claude_complete

  run bash "$TEST_DIR/ralph.sh" 1 --skip-security-check

  [ "$status" -eq 0 ]
  [[ "$output" == *"Verification passed"* ]]
  [[ "$output" == *"All stories have passes:true"* ]]
}

@test "Catches false COMPLETE when stories remain incomplete" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_incomplete.json" "$TEST_DIR/prd.json"
  create_mock_claude_complete  # Returns COMPLETE but PRD still has failing stories

  # Run with max 2 iterations
  run bash "$TEST_DIR/ralph.sh" 2 --skip-security-check

  # Should NOT exit successfully - should continue or fail
  [[ "$output" == *"WARNING: COMPLETE claimed but verification failed"* ]] || \
  [[ "$output" == *"still have passes:false"* ]]
}

@test "Detects consecutive failures on same story" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_incomplete.json" "$TEST_DIR/prd.json"
  create_mock_claude_continue "Working on US-001..."

  # Set up as if we've already tried this story
  echo "US-001" > "$TEST_DIR/.last-story"
  echo '{"US-001": 1}' > "$TEST_DIR/.story-attempts"

  # Run one iteration
  run bash "$TEST_DIR/ralph.sh" 1 --skip-security-check

  [[ "$output" == *"Consecutive attempt on story: US-001"* ]]
  [[ "$output" == *"Attempts on US-001:"* ]]
}

@test "Recognizes new story start" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_incomplete.json" "$TEST_DIR/prd.json"
  create_mock_claude_continue "Working on US-001..."

  # Last story was different
  echo "US-000" > "$TEST_DIR/.last-story"
  echo '{}' > "$TEST_DIR/.story-attempts"

  run bash "$TEST_DIR/ralph.sh" 1 --skip-security-check

  [[ "$output" == *"Starting story: US-001"* ]]
  [[ "$output" == *"attempt 1/"* ]]
}

@test "Exits with error when max iterations reached" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_incomplete.json" "$TEST_DIR/prd.json"
  create_mock_claude_continue "Still working..."

  run bash "$TEST_DIR/ralph.sh" 2 --skip-security-check

  [ "$status" -eq 1 ]
  [[ "$output" == *"reached max iterations"* ]]
}

@test "Circuit breaker skips story after max attempts" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_incomplete.json" "$TEST_DIR/prd.json"
  create_mock_claude_continue "Working..."

  # Story has already failed max attempts
  echo "US-001" > "$TEST_DIR/.last-story"
  echo '{"US-001": 5}' > "$TEST_DIR/.story-attempts"
  export MAX_ATTEMPTS_PER_STORY=5

  run bash "$TEST_DIR/ralph.sh" 1 --skip-security-check

  [[ "$output" == *"Circuit breaker"* ]]
  [[ "$output" == *"max attempts"* ]]
}

@test "Initializes progress file if missing" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_complete.json" "$TEST_DIR/prd.json"
  create_mock_claude_complete

  # Remove progress file
  rm -f "$TEST_DIR/progress.txt"

  run bash "$TEST_DIR/ralph.sh" 1 --skip-security-check

  [ "$status" -eq 0 ]
  [ -f "$TEST_DIR/progress.txt" ]

  progress_content=$(cat "$TEST_DIR/progress.txt")
  [[ "$progress_content" == *"# Ralph Progress Log"* ]]
}

@test "Initializes story attempts file if missing" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_complete.json" "$TEST_DIR/prd.json"
  create_mock_claude_complete

  # Remove attempts file
  rm -f "$TEST_DIR/.story-attempts"

  run bash "$TEST_DIR/ralph.sh" 1 --skip-security-check

  [ "$status" -eq 0 ]
  [ -f "$TEST_DIR/.story-attempts" ]
}

@test "Outputs iteration progress" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_complete.json" "$TEST_DIR/prd.json"
  create_mock_claude_complete

  run bash "$TEST_DIR/ralph.sh" 1 --skip-security-check

  [[ "$output" == *"Ralph Iteration 1"* ]]
  [[ "$output" == *"Starting Ralph"* ]]
}
