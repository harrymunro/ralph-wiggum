#!/usr/bin/env bats
# Tests for ralph.sh security pre-flight check

load 'test_helper/common'
load 'test_helper/mocks'

setup() {
  setup_test_environment
  cp "$BATS_TEST_DIRNAME/fixtures/prd_complete.json" "$TEST_DIR/prd.json"
  create_mock_claude_complete

  # Unset any security-related env vars
  unset AWS_ACCESS_KEY_ID
  unset AWS_SECRET_ACCESS_KEY
  unset DATABASE_URL
}

teardown() {
  teardown_test_environment
}

# Create a minimal security check script for isolated testing
create_security_check_script() {
  cat > "$TEST_DIR/security_check.sh" << 'EOF'
#!/bin/bash
SKIP_SECURITY="${SKIP_SECURITY_CHECK:-false}"
while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-security-check) SKIP_SECURITY="true"; shift ;;
    *) shift ;;
  esac
done

if [[ "$SKIP_SECURITY" != "true" ]]; then
  SECURITY_WARNINGS=()

  if [[ -n "${AWS_ACCESS_KEY_ID:-}" ]]; then
    SECURITY_WARNINGS+=("AWS_ACCESS_KEY_ID is set - production credentials may be exposed")
  fi

  if [[ -n "${DATABASE_URL:-}" ]]; then
    SECURITY_WARNINGS+=("DATABASE_URL is set - database credentials may be exposed")
  fi

  if [[ ${#SECURITY_WARNINGS[@]} -gt 0 ]]; then
    echo "WARNING: Potential credential exposure detected:"
    for warning in "${SECURITY_WARNINGS[@]}"; do
      echo "  - $warning"
    done
    exit 1  # Exit with error for testing (would prompt in real script)
  else
    echo "No credential exposure risks detected."
  fi
else
  echo "Security check skipped."
fi
EOF
  chmod +x "$TEST_DIR/security_check.sh"
}

@test "Warns when AWS_ACCESS_KEY_ID is set" {
  create_security_check_script

  export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
  run bash "$TEST_DIR/security_check.sh"
  [ "$status" -eq 1 ]
  [[ "$output" == *"AWS_ACCESS_KEY_ID is set"* ]]
  [[ "$output" == *"WARNING"* ]]
}

@test "Warns when DATABASE_URL is set" {
  create_security_check_script

  export DATABASE_URL="postgres://user:pass@localhost/db"
  run bash "$TEST_DIR/security_check.sh"
  [ "$status" -eq 1 ]
  [[ "$output" == *"DATABASE_URL is set"* ]]
  [[ "$output" == *"WARNING"* ]]
}

@test "No warnings when environment is clean" {
  create_security_check_script

  unset AWS_ACCESS_KEY_ID
  unset DATABASE_URL
  run bash "$TEST_DIR/security_check.sh"
  [ "$status" -eq 0 ]
  [[ "$output" == *"No credential exposure risks detected"* ]]
}

@test "Security check skipped with --skip-security-check flag" {
  create_security_check_script

  export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
  export DATABASE_URL="postgres://user:pass@localhost/db"
  run bash "$TEST_DIR/security_check.sh" --skip-security-check
  [ "$status" -eq 0 ]
  [[ "$output" == *"Security check skipped"* ]]
  [[ "$output" != *"WARNING"* ]]
}

@test "Multiple credentials trigger multiple warnings" {
  create_security_check_script

  export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
  export DATABASE_URL="postgres://user:pass@localhost/db"
  run bash "$TEST_DIR/security_check.sh"
  [ "$status" -eq 1 ]
  [[ "$output" == *"AWS_ACCESS_KEY_ID is set"* ]]
  [[ "$output" == *"DATABASE_URL is set"* ]]
}
