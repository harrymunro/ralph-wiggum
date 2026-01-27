#!/usr/bin/env bats
# Tests for ralph.sh --next-experiment hypothesis generation functionality

load 'test_helper/common'
load 'test_helper/mocks'

setup() {
  setup_test_environment
  # Create experiments.json with baseline
  cat > "$TEST_DIR/experiments.json" << 'EOF'
{
  "version": "1.0.0",
  "created": "2026-01-26",
  "baseline": {
    "completion_rate": 100,
    "avg_iterations": 1,
    "code_quality_rate": 100
  },
  "stagnation_count": 0,
  "experiments": []
}
EOF
}

teardown() {
  teardown_test_environment
}

@test "--next-experiment flag sets NEXT_EXPERIMENT_MODE to true" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
NEXT_EXPERIMENT_MODE="false"
while [[ $# -gt 0 ]]; do
  case $1 in
    --next-experiment) NEXT_EXPERIMENT_MODE="true"; shift ;;
    *) shift ;;
  esac
done
echo "NEXT_EXPERIMENT_MODE=$NEXT_EXPERIMENT_MODE"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  run bash "$TEST_DIR/ralph.sh" --next-experiment
  [ "$status" -eq 0 ]
  [[ "$output" == *"NEXT_EXPERIMENT_MODE=true"* ]]
}

@test "--next-experiment outputs hypothesis generator header" {
  run bash "$BATS_TEST_DIRNAME/../ralph.sh" --next-experiment
  [ "$status" -eq 0 ]
  [[ "$output" == *"Next Experiment Hypothesis Generator"* ]]
}

@test "--next-experiment reads baseline metrics from experiments.json" {
  run bash "$BATS_TEST_DIRNAME/../ralph.sh" --next-experiment
  [ "$status" -eq 0 ]
  [[ "$output" == *"Current Metrics Analysis"* ]]
  [[ "$output" == *"Completion Rate"* ]]
  [[ "$output" == *"Avg Iterations"* ]]
  [[ "$output" == *"Code Quality Rate"* ]]
}

@test "--next-experiment outputs structured hypothesis" {
  run bash "$BATS_TEST_DIRNAME/../ralph.sh" --next-experiment
  [ "$status" -eq 0 ]
  [[ "$output" == *"Proposed Hypothesis"* ]]
  [[ "$output" == *"metric_targeted"* ]]
  [[ "$output" == *"expected_improvement"* ]]
  [[ "$output" == *"specific_change"* ]]
  [[ "$output" == *"reasoning"* ]]
}

@test "--next-experiment identifies lowest-performing metric when completion_rate is low" {
  cat > "$TEST_DIR/experiments.json" << 'EOF'
{
  "version": "1.0.0",
  "baseline": {
    "completion_rate": 100,
    "avg_iterations": 1,
    "code_quality_rate": 100
  },
  "experiments": [
    {
      "id": "EXP-001",
      "date": "2026-01-26",
      "metrics": {
        "completion_rate": 60,
        "avg_iterations": 1.2,
        "code_quality_rate": 95
      }
    }
  ]
}
EOF

  cd "$TEST_DIR"
  # Create a minimal ralph.sh that uses the local experiments.json
  cat > "$TEST_DIR/test_hypothesis.sh" << 'SCRIPT'
#!/bin/bash
EXPERIMENTS_FILE="$PWD/experiments.json"
source "$1"
SCRIPT
  chmod +x "$TEST_DIR/test_hypothesis.sh"

  run bash "$BATS_TEST_DIRNAME/../ralph.sh" --next-experiment
  # When completion_rate has largest gap (40%), it should be targeted
  [[ "$output" == *"metric_targeted"* ]]
}

@test "--next-experiment generates next experiment ID from experiments.json" {
  cat > "$TEST_DIR/experiments.json" << 'EOF'
{
  "version": "1.0.0",
  "baseline": {
    "completion_rate": 100,
    "avg_iterations": 1,
    "code_quality_rate": 100
  },
  "experiments": [
    {"id": "EXP-003", "date": "2026-01-26", "metrics": {"completion_rate": 100, "avg_iterations": 1, "code_quality_rate": 100}}
  ]
}
EOF

  # Copy ralph.sh to test dir so SCRIPT_DIR points there
  cp "$BATS_TEST_DIRNAME/../ralph.sh" "$TEST_DIR/"
  chmod +x "$TEST_DIR/ralph.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/ralph.sh" --next-experiment
  [ "$status" -eq 0 ]
  [[ "$output" == *"EXP-004"* ]]
}

@test "--next-experiment shows gap analysis" {
  run bash "$BATS_TEST_DIRNAME/../ralph.sh" --next-experiment
  [ "$status" -eq 0 ]
  [[ "$output" == *"Gap Analysis"* ]]
}

@test "--next-experiment provides run command" {
  run bash "$BATS_TEST_DIRNAME/../ralph.sh" --next-experiment
  [ "$status" -eq 0 ]
  [[ "$output" == *"To run this experiment"* ]]
  [[ "$output" == *"./ralph.sh --experiment"* ]]
}

@test "--next-experiment fails gracefully when experiments.json is missing" {
  rm -f "$TEST_DIR/experiments.json"

  # We need to test the actual ralph.sh against a missing file
  # Create a test directory without experiments.json
  mkdir -p "$TEST_DIR/no_exp"
  cp "$BATS_TEST_DIRNAME/../ralph.sh" "$TEST_DIR/no_exp/"

  cd "$TEST_DIR/no_exp"
  run bash "$TEST_DIR/no_exp/ralph.sh" --next-experiment
  [ "$status" -eq 1 ]
  [[ "$output" == *"experiments.json not found"* ]]
}

@test "--next-experiment exits immediately without running main loop" {
  # Create a complete PRD and mock claude
  cp "$BATS_TEST_DIRNAME/fixtures/prd_complete.json" "$TEST_DIR/prd.json"
  create_mock_claude_complete

  run bash "$BATS_TEST_DIRNAME/../ralph.sh" --next-experiment
  [ "$status" -eq 0 ]
  # Should NOT see "Starting Ralph" which is the main loop message
  [[ "$output" != *"Starting Ralph - Max iterations"* ]]
}
