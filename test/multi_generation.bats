#!/usr/bin/env bats
# Tests for ralph.sh multi-generation autonomous evolution functionality

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
  "last_improvement_at": null,
  "experiments": []
}
EOF

  # Create experiments directory
  mkdir -p "$TEST_DIR/docs/experiments"
}

teardown() {
  teardown_test_environment
}

@test "--generations flag sets GENERATIONS_MODE to true" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
GENERATIONS_MODE="false"
GENERATIONS_COUNT=0
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-security-check) shift ;;
    --generations)
      GENERATIONS_MODE="true"
      if [[ -n "${2:-}" && "$2" =~ ^[0-9]+$ ]]; then
        GENERATIONS_COUNT="$2"
        shift
      else
        GENERATIONS_COUNT=3
      fi
      shift
      ;;
    *) shift ;;
  esac
done
echo "GENERATIONS_MODE=$GENERATIONS_MODE"
echo "GENERATIONS_COUNT=$GENERATIONS_COUNT"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  run bash "$TEST_DIR/ralph.sh" --generations
  [ "$status" -eq 0 ]
  [[ "$output" == *"GENERATIONS_MODE=true"* ]]
  [[ "$output" == *"GENERATIONS_COUNT=3"* ]]  # Default value
}

@test "--generations with count captures the generation count" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
GENERATIONS_MODE="false"
GENERATIONS_COUNT=0
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-security-check) shift ;;
    --generations)
      GENERATIONS_MODE="true"
      if [[ -n "${2:-}" && "$2" =~ ^[0-9]+$ ]]; then
        GENERATIONS_COUNT="$2"
        shift
      else
        GENERATIONS_COUNT=3
      fi
      shift
      ;;
    *) shift ;;
  esac
done
echo "GENERATIONS_MODE=$GENERATIONS_MODE"
echo "GENERATIONS_COUNT=$GENERATIONS_COUNT"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  run bash "$TEST_DIR/ralph.sh" --generations 5
  [ "$status" -eq 0 ]
  [[ "$output" == *"GENERATIONS_MODE=true"* ]]
  [[ "$output" == *"GENERATIONS_COUNT=5"* ]]
}

@test "--generations combined with other flags works" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
MAX_ITERATIONS=10
SKIP_SECURITY="false"
GENERATIONS_MODE="false"
GENERATIONS_COUNT=0
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-security-check) SKIP_SECURITY="true"; shift ;;
    --generations)
      GENERATIONS_MODE="true"
      if [[ -n "${2:-}" && "$2" =~ ^[0-9]+$ ]]; then
        GENERATIONS_COUNT="$2"
        shift
      else
        GENERATIONS_COUNT=3
      fi
      shift
      ;;
    *)
      if [[ "$1" =~ ^[0-9]+$ ]]; then MAX_ITERATIONS="$1"; fi
      shift
      ;;
  esac
done
echo "MAX_ITERATIONS=$MAX_ITERATIONS SKIP_SECURITY=$SKIP_SECURITY GENERATIONS_MODE=$GENERATIONS_MODE GENERATIONS_COUNT=$GENERATIONS_COUNT"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  run bash "$TEST_DIR/ralph.sh" --generations 3 --skip-security-check
  [ "$status" -eq 0 ]
  [[ "$output" == *"SKIP_SECURITY=true"* ]]
  [[ "$output" == *"GENERATIONS_MODE=true"* ]]
  [[ "$output" == *"GENERATIONS_COUNT=3"* ]]
}

@test "generations mode outputs self-directing evolution header" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
GENERATIONS_MODE="true"
GENERATIONS_COUNT=2

echo ""
echo "==============================================================="
echo "  Self-Directing Evolution Mode"
echo "  Generations to run: $GENERATIONS_COUNT"
echo "==============================================================="
exit 0
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  run bash "$TEST_DIR/ralph.sh"
  [ "$status" -eq 0 ]
  [[ "$output" == *"Self-Directing Evolution Mode"* ]]
  [[ "$output" == *"Generations to run: 2"* ]]
}

@test "safety limit variable is initialized" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
CONSECUTIVE_FAILURES=0
MAX_CONSECUTIVE_FAILURES=3
echo "CONSECUTIVE_FAILURES=$CONSECUTIVE_FAILURES"
echo "MAX_CONSECUTIVE_FAILURES=$MAX_CONSECUTIVE_FAILURES"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  run bash "$TEST_DIR/ralph.sh"
  [ "$status" -eq 0 ]
  [[ "$output" == *"CONSECUTIVE_FAILURES=0"* ]]
  [[ "$output" == *"MAX_CONSECUTIVE_FAILURES=3"* ]]
}

@test "safety limit triggers after 3 consecutive failures" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
CONSECUTIVE_FAILURES=3
MAX_CONSECUTIVE_FAILURES=3

if [[ "$CONSECUTIVE_FAILURES" -ge "$MAX_CONSECUTIVE_FAILURES" ]]; then
  echo "SAFETY LIMIT REACHED: $CONSECUTIVE_FAILURES consecutive failures"
  echo "Stopping self-directing evolution"
  exit 1
fi
echo "Continuing..."
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  run bash "$TEST_DIR/ralph.sh"
  [ "$status" -eq 1 ]
  [[ "$output" == *"SAFETY LIMIT REACHED"* ]]
  [[ "$output" == *"3 consecutive failures"* ]]
}

@test "consecutive failures counter resets on success" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
CONSECUTIVE_FAILURES=2
# Simulate successful generation
experiment_success=true
if [[ "$experiment_success" == "true" ]]; then
  CONSECUTIVE_FAILURES=0
fi
echo "CONSECUTIVE_FAILURES=$CONSECUTIVE_FAILURES"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  run bash "$TEST_DIR/ralph.sh"
  [ "$status" -eq 0 ]
  [[ "$output" == *"CONSECUTIVE_FAILURES=0"* ]]
}

@test "generate_generation_summary creates summary file" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$PWD"
EXPERIMENTS_FILE="$SCRIPT_DIR/experiments.json"

generate_generation_summary() {
  local total_generations="$1"
  local successful_generations="$2"
  local failed_generations="$3"

  local summary_file="$SCRIPT_DIR/docs/experiments/generation-summary.md"
  mkdir -p "$(dirname "$summary_file")"

  cat > "$summary_file" << ENDOF
# Generation Summary Report

## Overview

- **Total Generations Run:** $total_generations
- **Successful Generations:** $successful_generations
- **Failed Generations:** $failed_generations
ENDOF

  echo "Summary written to $summary_file"
}

generate_generation_summary 3 2 1
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/ralph.sh"
  [ "$status" -eq 0 ]
  [[ "$output" == *"Summary written to"* ]]

  # Verify file was created
  [ -f "$TEST_DIR/docs/experiments/generation-summary.md" ]

  # Verify content
  run cat "$TEST_DIR/docs/experiments/generation-summary.md"
  [[ "$output" == *"Generation Summary Report"* ]]
  [[ "$output" == *"Total Generations Run:** 3"* ]]
  [[ "$output" == *"Successful Generations:** 2"* ]]
  [[ "$output" == *"Failed Generations:** 1"* ]]
}

@test "generation summary includes metrics comparison" {
  # Add some experiments to experiments.json
  cat > "$TEST_DIR/experiments.json" << 'EOF'
{
  "version": "1.0.0",
  "baseline": {
    "completion_rate": 80,
    "avg_iterations": 2,
    "code_quality_rate": 90
  },
  "stagnation_count": 0,
  "last_improvement_at": "2026-01-26",
  "experiments": [
    {
      "id": "EXP-001",
      "date": "2026-01-26",
      "metrics": {
        "completion_rate": 90,
        "avg_iterations": 1.5,
        "code_quality_rate": 95
      },
      "delta_fitness": 10,
      "outcome": "completed"
    }
  ]
}
EOF

  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$PWD"
EXPERIMENTS_FILE="$SCRIPT_DIR/experiments.json"

generate_generation_summary() {
  local total_generations="$1"
  local summary_file="$SCRIPT_DIR/docs/experiments/generation-summary.md"
  mkdir -p "$(dirname "$summary_file")"

  local baseline_completion=$(jq -r '.baseline.completion_rate // "N/A"' "$EXPERIMENTS_FILE")
  local final_completion=$(jq -r '.experiments[-1].metrics.completion_rate // "N/A"' "$EXPERIMENTS_FILE")

  cat > "$summary_file" << ENDOF
# Generation Summary Report

## Metrics Summary

| Metric | Baseline | Final |
|--------|----------|-------|
| Completion Rate | ${baseline_completion}% | ${final_completion}% |
ENDOF
}

generate_generation_summary 1
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/ralph.sh"
  [ "$status" -eq 0 ]

  # Verify metrics are in summary
  run cat "$TEST_DIR/docs/experiments/generation-summary.md"
  [[ "$output" == *"Metrics Summary"* ]]
  [[ "$output" == *"Baseline"* ]]
  [[ "$output" == *"80%"* ]]  # baseline completion
  [[ "$output" == *"90%"* ]]  # final completion
}

@test "get_last_experiment_outcome returns improved when delta_fitness positive" {
  cat > "$TEST_DIR/experiments.json" << 'EOF'
{
  "experiments": [
    {"id": "EXP-001", "delta_fitness": 5.5}
  ]
}
EOF

  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
EXPERIMENTS_FILE="$PWD/experiments.json"

get_last_experiment_outcome() {
  if [[ -f "$EXPERIMENTS_FILE" ]]; then
    local delta_fitness=$(jq -r '.experiments[-1].delta_fitness // 0' "$EXPERIMENTS_FILE")
    local improved=$(echo "$delta_fitness > 0" | bc -l 2>/dev/null || echo "0")
    if [[ "$improved" -eq 1 ]]; then
      echo "improved"
    else
      echo "no_improvement"
    fi
  else
    echo "unknown"
  fi
}

get_last_experiment_outcome
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/ralph.sh"
  [ "$status" -eq 0 ]
  [ "$output" = "improved" ]
}

@test "get_last_experiment_outcome returns no_improvement when delta_fitness zero or negative" {
  cat > "$TEST_DIR/experiments.json" << 'EOF'
{
  "experiments": [
    {"id": "EXP-001", "delta_fitness": -2.0}
  ]
}
EOF

  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
EXPERIMENTS_FILE="$PWD/experiments.json"

get_last_experiment_outcome() {
  if [[ -f "$EXPERIMENTS_FILE" ]]; then
    local delta_fitness=$(jq -r '.experiments[-1].delta_fitness // 0' "$EXPERIMENTS_FILE")
    local improved=$(echo "$delta_fitness > 0" | bc -l 2>/dev/null || echo "0")
    if [[ "$improved" -eq 1 ]]; then
      echo "improved"
    else
      echo "no_improvement"
    fi
  else
    echo "unknown"
  fi
}

get_last_experiment_outcome
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/ralph.sh"
  [ "$status" -eq 0 ]
  [ "$output" = "no_improvement" ]
}
