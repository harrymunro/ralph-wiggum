#!/usr/bin/env bats
# Tests for ralph.sh argument parsing

load 'test_helper/common'
load 'test_helper/mocks'

setup() {
  setup_test_environment
  # Create a complete PRD so script doesn't wait for claude
  cp "$BATS_TEST_DIRNAME/fixtures/prd_complete.json" "$TEST_DIR/prd.json"
  create_mock_claude_complete
}

teardown() {
  teardown_test_environment
}

@test "MAX_ITERATIONS defaults to 10" {
  # Modify script to echo MAX_ITERATIONS and exit early
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
MAX_ITERATIONS=10
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-security-check) shift ;;
    *) if [[ "$1" =~ ^[0-9]+$ ]]; then MAX_ITERATIONS="$1"; fi; shift ;;
  esac
done
echo "MAX_ITERATIONS=$MAX_ITERATIONS"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  run bash "$TEST_DIR/ralph.sh"
  [ "$status" -eq 0 ]
  [[ "$output" == *"MAX_ITERATIONS=10"* ]]
}

@test "Numeric argument sets MAX_ITERATIONS" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
MAX_ITERATIONS=10
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-security-check) shift ;;
    *) if [[ "$1" =~ ^[0-9]+$ ]]; then MAX_ITERATIONS="$1"; fi; shift ;;
  esac
done
echo "MAX_ITERATIONS=$MAX_ITERATIONS"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  run bash "$TEST_DIR/ralph.sh" 25
  [ "$status" -eq 0 ]
  [[ "$output" == *"MAX_ITERATIONS=25"* ]]
}

@test "--skip-security-check sets SKIP_SECURITY to true" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
SKIP_SECURITY="${SKIP_SECURITY_CHECK:-false}"
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-security-check) SKIP_SECURITY="true"; shift ;;
    *) shift ;;
  esac
done
echo "SKIP_SECURITY=$SKIP_SECURITY"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  run bash "$TEST_DIR/ralph.sh" --skip-security-check
  [ "$status" -eq 0 ]
  [[ "$output" == *"SKIP_SECURITY=true"* ]]
}

@test "Non-numeric arguments are ignored for MAX_ITERATIONS" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
MAX_ITERATIONS=10
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-security-check) shift ;;
    *) if [[ "$1" =~ ^[0-9]+$ ]]; then MAX_ITERATIONS="$1"; fi; shift ;;
  esac
done
echo "MAX_ITERATIONS=$MAX_ITERATIONS"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  run bash "$TEST_DIR/ralph.sh" "notanumber"
  [ "$status" -eq 0 ]
  [[ "$output" == *"MAX_ITERATIONS=10"* ]]
}

@test "MAX_ATTEMPTS_PER_STORY uses environment variable" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
MAX_ATTEMPTS_PER_STORY="${MAX_ATTEMPTS_PER_STORY:-5}"
echo "MAX_ATTEMPTS_PER_STORY=$MAX_ATTEMPTS_PER_STORY"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  # Test default
  run bash "$TEST_DIR/ralph.sh"
  [[ "$output" == *"MAX_ATTEMPTS_PER_STORY=5"* ]]

  # Test with env var
  MAX_ATTEMPTS_PER_STORY=3 run bash "$TEST_DIR/ralph.sh"
  [[ "$output" == *"MAX_ATTEMPTS_PER_STORY=3"* ]]
}

@test "Multiple arguments can be combined" {
  cat > "$TEST_DIR/ralph.sh" << 'EOF'
#!/bin/bash
MAX_ITERATIONS=10
SKIP_SECURITY="${SKIP_SECURITY_CHECK:-false}"
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-security-check) SKIP_SECURITY="true"; shift ;;
    *) if [[ "$1" =~ ^[0-9]+$ ]]; then MAX_ITERATIONS="$1"; fi; shift ;;
  esac
done
echo "MAX_ITERATIONS=$MAX_ITERATIONS SKIP_SECURITY=$SKIP_SECURITY"
EOF
  chmod +x "$TEST_DIR/ralph.sh"

  run bash "$TEST_DIR/ralph.sh" 15 --skip-security-check
  [ "$status" -eq 0 ]
  [[ "$output" == *"MAX_ITERATIONS=15"* ]]
  [[ "$output" == *"SKIP_SECURITY=true"* ]]
}
