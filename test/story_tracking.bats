#!/usr/bin/env bats
# Tests for ralph.sh story tracking and circuit breaker functionality

load 'test_helper/common'
load 'test_helper/mocks'

setup() {
  setup_test_environment
  create_mock_claude_continue
}

teardown() {
  teardown_test_environment
}

@test "get_current_story returns first failing story" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_incomplete.json" "$TEST_DIR/prd.json"
  source_ralph_functions

  result=$(get_current_story)
  [ "$result" = "US-001" ]
}

@test "get_current_story returns empty when all stories pass" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_complete.json" "$TEST_DIR/prd.json"
  source_ralph_functions

  result=$(get_current_story)
  [ -z "$result" ]
}

@test "get_story_attempts returns 0 for new story" {
  echo '{}' > "$TEST_DIR/.story-attempts"
  source_ralph_functions

  result=$(get_story_attempts "US-001")
  [ "$result" = "0" ]
}

@test "get_story_attempts returns count for existing story" {
  echo '{"US-001": 3, "US-002": 1}' > "$TEST_DIR/.story-attempts"
  source_ralph_functions

  result=$(get_story_attempts "US-001")
  [ "$result" = "3" ]

  result=$(get_story_attempts "US-002")
  [ "$result" = "1" ]
}

@test "increment_story_attempts increases count by 1" {
  echo '{"US-001": 2}' > "$TEST_DIR/.story-attempts"
  source_ralph_functions

  result=$(increment_story_attempts "US-001")
  [ "$result" = "3" ]

  # Verify file was updated
  stored=$(jq -r '.["US-001"]' "$TEST_DIR/.story-attempts")
  [ "$stored" = "3" ]
}

@test "increment_story_attempts handles new story" {
  echo '{}' > "$TEST_DIR/.story-attempts"
  source_ralph_functions

  result=$(increment_story_attempts "US-NEW")
  [ "$result" = "1" ]

  stored=$(jq -r '.["US-NEW"]' "$TEST_DIR/.story-attempts")
  [ "$stored" = "1" ]
}

@test "circuit breaker trips at max attempts" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_incomplete.json" "$TEST_DIR/prd.json"
  echo '{"US-001": 5}' > "$TEST_DIR/.story-attempts"
  export MAX_ATTEMPTS_PER_STORY=5
  source_ralph_functions

  run check_circuit_breaker "US-001"
  [ "$status" -eq 0 ]  # 0 = true, circuit breaker tripped
}

@test "circuit breaker does not trip below max attempts" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_incomplete.json" "$TEST_DIR/prd.json"
  echo '{"US-001": 3}' > "$TEST_DIR/.story-attempts"
  export MAX_ATTEMPTS_PER_STORY=5
  source_ralph_functions

  run check_circuit_breaker "US-001"
  [ "$status" -eq 1 ]  # 1 = false, circuit breaker not tripped
}

@test "mark_story_skipped adds notes to PRD" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_incomplete.json" "$TEST_DIR/prd.json"
  source_ralph_functions

  mark_story_skipped "US-001" 5

  # Check that notes were added
  notes=$(jq -r '.userStories[] | select(.id == "US-001") | .notes' "$TEST_DIR/prd.json")
  [[ "$notes" == *"Skipped"* ]]
  [[ "$notes" == *"5 attempts"* ]]
}

@test "mark_story_skipped preserves other stories" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_incomplete.json" "$TEST_DIR/prd.json"
  source_ralph_functions

  mark_story_skipped "US-001" 5

  # Check US-002 is unchanged
  us002_notes=$(jq -r '.userStories[] | select(.id == "US-002") | .notes' "$TEST_DIR/prd.json")
  [ "$us002_notes" = "" ]

  us002_passes=$(jq -r '.userStories[] | select(.id == "US-002") | .passes' "$TEST_DIR/prd.json")
  [ "$us002_passes" = "false" ]
}
