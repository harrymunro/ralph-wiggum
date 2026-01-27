#!/usr/bin/env bats
# Tests for ralph.sh metrics tracking and summary

load 'test_helper/common'
load 'test_helper/mocks'

setup() {
  setup_test_environment
}

teardown() {
  teardown_test_environment
}

@test "Outputs metrics summary on successful completion" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_complete.json" "$TEST_DIR/prd.json"
  create_mock_claude_complete

  run bash "$TEST_DIR/ralph.sh" 1 --skip-security-check

  [ "$status" -eq 0 ]
  [[ "$output" == *"Ralph Metrics Summary"* ]]
  [[ "$output" == *"Stories:"* ]]
  [[ "$output" == *"Completed:"* ]]
  [[ "$output" == *"Iterations:"* ]]
}

@test "Outputs metrics summary on max iterations reached" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_incomplete.json" "$TEST_DIR/prd.json"
  create_mock_claude_continue "Working..."

  run bash "$TEST_DIR/ralph.sh" 2 --skip-security-check

  [ "$status" -eq 1 ]
  [[ "$output" == *"Ralph Metrics Summary"* ]]
  [[ "$output" == *"Stories:"* ]]
}

@test "Metrics show correct completion count" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_complete.json" "$TEST_DIR/prd.json"
  create_mock_claude_complete

  run bash "$TEST_DIR/ralph.sh" 1 --skip-security-check

  [ "$status" -eq 0 ]
  # prd_complete.json has 2 stories, both passing
  [[ "$output" == *"Completed: 2 / 2"* ]]
}

@test "Metrics show completion rate" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_complete.json" "$TEST_DIR/prd.json"
  create_mock_claude_complete

  run bash "$TEST_DIR/ralph.sh" 1 --skip-security-check

  [ "$status" -eq 0 ]
  [[ "$output" == *"Completion Rate:"* ]]
}

@test "Metrics track iteration count" {
  cp "$BATS_TEST_DIRNAME/fixtures/prd_incomplete.json" "$TEST_DIR/prd.json"
  create_mock_claude_continue "Working..."

  run bash "$TEST_DIR/ralph.sh" 3 --skip-security-check

  [ "$status" -eq 1 ]
  [[ "$output" == *"Total iterations: 3"* ]]
}
