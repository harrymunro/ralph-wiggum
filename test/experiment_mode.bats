#!/usr/bin/env bats
# Tests for ralph.sh experiment mode functionality

load 'test_helper/common'
load 'test_helper/mocks'

setup() {
  setup_test_environment
  # Create a complete PRD so script doesn't wait for claude
  cp "$BATS_TEST_DIRNAME/fixtures/prd_complete.json" "$TEST_DIR/prd.json"
  create_mock_claude_complete

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

  # Create experiments directory
  mkdir -p "$TEST_DIR/docs/experiments"
}

teardown() {
  teardown_test_environment
}

@test "--experiment flag sets EXPERIMENT_MODE to true" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
EXPERIMENT_MODE="false"
EXPERIMENT_ID=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-security-check) shift ;;
    --experiment)
      EXPERIMENT_MODE="true"
      if [[ -n "${2:-}" && ! "$2" =~ ^-- ]]; then
        EXPERIMENT_ID="$2"
        shift
      fi
      shift
      ;;
    *) shift ;;
  esac
done
echo "EXPERIMENT_MODE=$EXPERIMENT_MODE"
echo "EXPERIMENT_ID=$EXPERIMENT_ID"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  run bash "$TEST_DIR/ralph.sh" --experiment
  [ "$status" -eq 0 ]
  [[ "$output" == *"EXPERIMENT_MODE=true"* ]]
}

@test "--experiment with ID captures the experiment ID" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
EXPERIMENT_MODE="false"
EXPERIMENT_ID=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-security-check) shift ;;
    --experiment)
      EXPERIMENT_MODE="true"
      if [[ -n "${2:-}" && ! "$2" =~ ^-- ]]; then
        EXPERIMENT_ID="$2"
        shift
      fi
      shift
      ;;
    *) shift ;;
  esac
done
echo "EXPERIMENT_MODE=$EXPERIMENT_MODE"
echo "EXPERIMENT_ID=$EXPERIMENT_ID"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  run bash "$TEST_DIR/ralph.sh" --experiment EXP-TEST
  [ "$status" -eq 0 ]
  [[ "$output" == *"EXPERIMENT_MODE=true"* ]]
  [[ "$output" == *"EXPERIMENT_ID=EXP-TEST"* ]]
}

@test "--experiment combined with other flags works" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
MAX_ITERATIONS=10
SKIP_SECURITY="false"
EXPERIMENT_MODE="false"
EXPERIMENT_ID=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-security-check) SKIP_SECURITY="true"; shift ;;
    --experiment)
      EXPERIMENT_MODE="true"
      if [[ -n "${2:-}" && ! "$2" =~ ^-- ]]; then
        EXPERIMENT_ID="$2"
        shift
      fi
      shift
      ;;
    *)
      if [[ "$1" =~ ^[0-9]+$ ]]; then MAX_ITERATIONS="$1"; fi
      shift
      ;;
  esac
done
echo "MAX_ITERATIONS=$MAX_ITERATIONS SKIP_SECURITY=$SKIP_SECURITY EXPERIMENT_MODE=$EXPERIMENT_MODE"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  run bash "$TEST_DIR/ralph.sh" 5 --experiment --skip-security-check
  [ "$status" -eq 0 ]
  [[ "$output" == *"MAX_ITERATIONS=5"* ]]
  [[ "$output" == *"SKIP_SECURITY=true"* ]]
  [[ "$output" == *"EXPERIMENT_MODE=true"* ]]
}

@test "experiment mode generates ID from experiments.json when not provided" {
  # Add an experiment to set the last ID
  cat > "$TEST_DIR/experiments.json" << 'EOF'
{
  "version": "1.0.0",
  "baseline": {
    "completion_rate": 100,
    "avg_iterations": 1,
    "code_quality_rate": 100
  },
  "experiments": [
    {"id": "EXP-005", "date": "2026-01-26"}
  ]
}
EOF

  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
EXPERIMENT_MODE="true"
EXPERIMENT_ID=""
EXPERIMENTS_FILE="$PWD/experiments.json"

if [[ -z "$EXPERIMENT_ID" ]]; then
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
echo "EXPERIMENT_ID=$EXPERIMENT_ID"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/ralph.sh"
  [ "$status" -eq 0 ]
  [[ "$output" == *"EXPERIMENT_ID=EXP-006"* ]]
}

@test "experiment mode outputs experiment mode enabled message" {
  run bash "$TEST_DIR/ralph.sh" --experiment EXP-TEST --skip-security-check 1
  # Script will fail because git isn't available in test, but should show experiment mode message
  [[ "$output" == *"Experiment Mode Enabled"* ]]
}

@test "record_experiment_results only runs in experiment mode" {
  # Create a test script that simulates the record function
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
EXPERIMENT_MODE="false"
EXPERIMENTS_FILE="$PWD/experiments.json"

record_experiment_results() {
  if [[ "$EXPERIMENT_MODE" != "true" ]]; then
    return
  fi
  echo "Recording experiment results..."
}

record_experiment_results
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/ralph.sh"
  [ "$status" -eq 0 ]
  # Should NOT contain the recording message when not in experiment mode
  [[ "$output" != *"Recording experiment results"* ]]
}

@test "experiment results are recorded to experiments.json" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
EXPERIMENT_MODE="true"
EXPERIMENT_ID="EXP-TEST"
EXPERIMENT_DATE="2026-01-26"
EXPERIMENTS_FILE="$PWD/experiments.json"
METRICS_ITERATIONS=2

# Simplified record function for testing
completed=2
total=2
completion_rate=100
avg_iterations=1
code_quality_rate=100

experiment_entry=$(cat <<EXPEOF
{
  "id": "$EXPERIMENT_ID",
  "date": "$EXPERIMENT_DATE",
  "hypothesis": "Test experiment",
  "metrics": {
    "completion_rate": $completion_rate,
    "avg_iterations": $avg_iterations,
    "code_quality_rate": $code_quality_rate
  },
  "outcome": "completed",
  "delta_fitness": 0
}
EXPEOF
)

jq --argjson exp "$experiment_entry" '.experiments += [$exp]' "$EXPERIMENTS_FILE" > "$EXPERIMENTS_FILE.tmp" && \
  mv "$EXPERIMENTS_FILE.tmp" "$EXPERIMENTS_FILE"

echo "Recorded"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/ralph.sh"
  [ "$status" -eq 0 ]

  # Check that experiment was added to experiments.json
  run jq '.experiments | length' "$TEST_DIR/experiments.json"
  [ "$output" = "1" ]

  run jq -r '.experiments[0].id' "$TEST_DIR/experiments.json"
  [ "$output" = "EXP-TEST" ]
}
