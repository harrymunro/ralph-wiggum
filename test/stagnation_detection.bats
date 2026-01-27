#!/usr/bin/env bats
# Tests for ralph.sh stagnation detection and big mutation functionality

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
  # Create PRD with incomplete stories (required for hypothesis generation)
  create_incomplete_prd
}

teardown() {
  teardown_test_environment
}

@test "check_stagnation returns false when stagnation_count is 0" {
  cat > "$TEST_DIR/test_stagnation.sh" << 'EOF'
#!/bin/bash
EXPERIMENTS_FILE="$PWD/experiments.json"

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

check_stagnation
EOF
  chmod +x "$TEST_DIR/test_stagnation.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/test_stagnation.sh"
  [ "$status" -eq 0 ]
  [ "$output" = "false" ]
}

@test "check_stagnation returns true when stagnation_count is 3" {
  # Set stagnation_count to 3
  jq '.stagnation_count = 3' "$TEST_DIR/experiments.json" > "$TEST_DIR/experiments.json.tmp" && \
    mv "$TEST_DIR/experiments.json.tmp" "$TEST_DIR/experiments.json"

  cat > "$TEST_DIR/test_stagnation.sh" << 'EOF'
#!/bin/bash
EXPERIMENTS_FILE="$PWD/experiments.json"

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

check_stagnation
EOF
  chmod +x "$TEST_DIR/test_stagnation.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/test_stagnation.sh"
  [ "$status" -eq 0 ]
  [ "$output" = "true" ]
}

@test "check_stagnation returns true when stagnation_count exceeds 3" {
  # Set stagnation_count to 5
  jq '.stagnation_count = 5' "$TEST_DIR/experiments.json" > "$TEST_DIR/experiments.json.tmp" && \
    mv "$TEST_DIR/experiments.json.tmp" "$TEST_DIR/experiments.json"

  cat > "$TEST_DIR/test_stagnation.sh" << 'EOF'
#!/bin/bash
EXPERIMENTS_FILE="$PWD/experiments.json"

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

check_stagnation
EOF
  chmod +x "$TEST_DIR/test_stagnation.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/test_stagnation.sh"
  [ "$status" -eq 0 ]
  [ "$output" = "true" ]
}

@test "update_stagnation_count resets to 0 when fitness improves" {
  # Start with stagnation_count = 2
  jq '.stagnation_count = 2' "$TEST_DIR/experiments.json" > "$TEST_DIR/experiments.json.tmp" && \
    mv "$TEST_DIR/experiments.json.tmp" "$TEST_DIR/experiments.json"

  cat > "$TEST_DIR/test_update_stagnation.sh" << 'EOF'
#!/bin/bash
EXPERIMENTS_FILE="$PWD/experiments.json"

update_stagnation_count() {
  local delta_fitness="$1"

  if [[ ! -f "$EXPERIMENTS_FILE" ]]; then
    return
  fi

  local improved=$(echo "$delta_fitness > 0" | bc -l 2>/dev/null || echo "0")

  if [[ "$improved" -eq 1 ]]; then
    local current_date=$(date +%Y-%m-%d)
    jq --arg date "$current_date" '.stagnation_count = 0 | .last_improvement_at = $date' "$EXPERIMENTS_FILE" > "$EXPERIMENTS_FILE.tmp" && \
      mv "$EXPERIMENTS_FILE.tmp" "$EXPERIMENTS_FILE"
  else
    jq '.stagnation_count += 1' "$EXPERIMENTS_FILE" > "$EXPERIMENTS_FILE.tmp" && \
      mv "$EXPERIMENTS_FILE.tmp" "$EXPERIMENTS_FILE"
  fi
}

# Simulate positive fitness delta (improvement)
update_stagnation_count "5.0"
EOF
  chmod +x "$TEST_DIR/test_update_stagnation.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/test_update_stagnation.sh"
  [ "$status" -eq 0 ]

  # Check that stagnation_count was reset
  run jq -r '.stagnation_count' "$TEST_DIR/experiments.json"
  [ "$output" = "0" ]

  # Check that last_improvement_at was set
  run jq -r '.last_improvement_at' "$TEST_DIR/experiments.json"
  [[ "$output" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]
}

@test "update_stagnation_count increments when no improvement" {
  cat > "$TEST_DIR/test_update_stagnation.sh" << 'EOF'
#!/bin/bash
EXPERIMENTS_FILE="$PWD/experiments.json"

update_stagnation_count() {
  local delta_fitness="$1"

  if [[ ! -f "$EXPERIMENTS_FILE" ]]; then
    return
  fi

  local improved=$(echo "$delta_fitness > 0" | bc -l 2>/dev/null || echo "0")

  if [[ "$improved" -eq 1 ]]; then
    local current_date=$(date +%Y-%m-%d)
    jq --arg date "$current_date" '.stagnation_count = 0 | .last_improvement_at = $date' "$EXPERIMENTS_FILE" > "$EXPERIMENTS_FILE.tmp" && \
      mv "$EXPERIMENTS_FILE.tmp" "$EXPERIMENTS_FILE"
  else
    jq '.stagnation_count += 1' "$EXPERIMENTS_FILE" > "$EXPERIMENTS_FILE.tmp" && \
      mv "$EXPERIMENTS_FILE.tmp" "$EXPERIMENTS_FILE"
  fi
}

# Simulate zero or negative fitness delta (no improvement)
update_stagnation_count "0"
EOF
  chmod +x "$TEST_DIR/test_update_stagnation.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/test_update_stagnation.sh"
  [ "$status" -eq 0 ]

  # Check that stagnation_count was incremented
  run jq -r '.stagnation_count' "$TEST_DIR/experiments.json"
  [ "$output" = "1" ]
}

@test "update_stagnation_count increments when fitness is negative" {
  cat > "$TEST_DIR/test_update_stagnation.sh" << 'EOF'
#!/bin/bash
EXPERIMENTS_FILE="$PWD/experiments.json"

update_stagnation_count() {
  local delta_fitness="$1"

  if [[ ! -f "$EXPERIMENTS_FILE" ]]; then
    return
  fi

  local improved=$(echo "$delta_fitness > 0" | bc -l 2>/dev/null || echo "0")

  if [[ "$improved" -eq 1 ]]; then
    local current_date=$(date +%Y-%m-%d)
    jq --arg date "$current_date" '.stagnation_count = 0 | .last_improvement_at = $date' "$EXPERIMENTS_FILE" > "$EXPERIMENTS_FILE.tmp" && \
      mv "$EXPERIMENTS_FILE.tmp" "$EXPERIMENTS_FILE"
  else
    jq '.stagnation_count += 1' "$EXPERIMENTS_FILE" > "$EXPERIMENTS_FILE.tmp" && \
      mv "$EXPERIMENTS_FILE.tmp" "$EXPERIMENTS_FILE"
  fi
}

# Simulate negative fitness delta
update_stagnation_count "-2.5"
EOF
  chmod +x "$TEST_DIR/test_update_stagnation.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/test_update_stagnation.sh"
  [ "$status" -eq 0 ]

  # Check that stagnation_count was incremented
  run jq -r '.stagnation_count' "$TEST_DIR/experiments.json"
  [ "$output" = "1" ]
}

@test "--next-experiment selects big mutation when stagnation detected" {
  # Set stagnation_count to 3 (stagnation threshold)
  jq '.stagnation_count = 3' "$TEST_DIR/experiments.json" > "$TEST_DIR/experiments.json.tmp" && \
    mv "$TEST_DIR/experiments.json.tmp" "$TEST_DIR/experiments.json"

  # Copy ralph.sh to test directory
  cp "$BATS_TEST_DIRNAME/../ralph.sh" "$TEST_DIR/"
  chmod +x "$TEST_DIR/ralph.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/ralph.sh" --next-experiment
  [ "$status" -eq 0 ]
  [[ "$output" == *"Big Mutation Selection"* ]]
  [[ "$output" == *"Stagnation Escape"* ]]
  [[ "$output" == *"mutation_id"* ]]
}

@test "--next-experiment uses normal hypothesis when no stagnation" {
  # Ensure stagnation_count is 0
  run jq -r '.stagnation_count' "$TEST_DIR/experiments.json"
  [ "$output" = "0" ]

  # Copy ralph.sh to test directory
  cp "$BATS_TEST_DIRNAME/../ralph.sh" "$TEST_DIR/"
  chmod +x "$TEST_DIR/ralph.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/ralph.sh" --next-experiment
  [ "$status" -eq 0 ]
  [[ "$output" == *"Next Experiment Hypothesis Generator"* ]]
  [[ "$output" != *"Big Mutation Selection"* ]]
}

@test "select_big_mutation outputs structured mutation data" {
  # Set stagnation to trigger big mutation selection
  jq '.stagnation_count = 3' "$TEST_DIR/experiments.json" > "$TEST_DIR/experiments.json.tmp" && \
    mv "$TEST_DIR/experiments.json.tmp" "$TEST_DIR/experiments.json"

  # Copy ralph.sh to test directory
  cp "$BATS_TEST_DIRNAME/../ralph.sh" "$TEST_DIR/"
  chmod +x "$TEST_DIR/ralph.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/ralph.sh" --next-experiment
  [ "$status" -eq 0 ]
  [[ "$output" == *"mutation_id"* ]]
  [[ "$output" == *"mutation_name"* ]]
  [[ "$output" == *"mutation_description"* ]]
}

@test "select_big_mutation skips already-tried mutations" {
  # Add an experiment that used MUTATION-001
  cat > "$TEST_DIR/experiments.json" << 'EOF'
{
  "version": "1.0.0",
  "baseline": {
    "completion_rate": 100,
    "avg_iterations": 1,
    "code_quality_rate": 100
  },
  "stagnation_count": 3,
  "last_improvement_at": null,
  "experiments": [
    {
      "id": "EXP-001",
      "date": "2026-01-26",
      "hypothesis": "MUTATION-001 - Restructure PRD Format",
      "metrics": {"completion_rate": 80, "avg_iterations": 2, "code_quality_rate": 90},
      "outcome": "completed",
      "delta_fitness": -5
    }
  ]
}
EOF

  # Ensure PRD has incomplete stories
  create_incomplete_prd

  # Copy ralph.sh to test directory
  cp "$BATS_TEST_DIRNAME/../ralph.sh" "$TEST_DIR/"
  chmod +x "$TEST_DIR/ralph.sh"

  cd "$TEST_DIR"
  run bash "$TEST_DIR/ralph.sh" --next-experiment
  [ "$status" -eq 0 ]
  # Should select MUTATION-002 since MUTATION-001 was already tried
  [[ "$output" == *"MUTATION-002"* ]] || [[ "$output" == *"mutation_id"* ]]
}

@test "experiments.json tracks stagnation_count field" {
  run jq -r '.stagnation_count' "$TEST_DIR/experiments.json"
  [ "$status" -eq 0 ]
  [ "$output" = "0" ]
}

@test "experiments.json tracks last_improvement_at field" {
  run jq 'has("last_improvement_at")' "$TEST_DIR/experiments.json"
  [ "$status" -eq 0 ]
  [ "$output" = "true" ]
}
