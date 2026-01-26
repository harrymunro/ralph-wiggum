#!/bin/bash
# Mock implementations for testing ralph.sh

# Create a mock claude command that returns COMPLETE signal
create_mock_claude_complete() {
  cat > "$TEST_DIR/bin/claude" << 'EOF'
#!/bin/bash
echo "Processing CLAUDE.md..."
echo "<promise>COMPLETE</promise>"
exit 0
EOF
  chmod +x "$TEST_DIR/bin/claude"
}

# Create a mock claude command that returns normal output (no COMPLETE)
create_mock_claude_continue() {
  local output="${1:-Working on story US-001...}"
  cat > "$TEST_DIR/bin/claude" << EOF
#!/bin/bash
echo "$output"
exit 0
EOF
  chmod +x "$TEST_DIR/bin/claude"
}

# Create a mock claude command that exits with error
create_mock_claude_error() {
  local error_msg="${1:-Error: Something went wrong}"
  local exit_code="${2:-1}"
  cat > "$TEST_DIR/bin/claude" << EOF
#!/bin/bash
echo "$error_msg" >&2
exit $exit_code
EOF
  chmod +x "$TEST_DIR/bin/claude"
}

# Create a mock claude that tracks how many times it was called
create_mock_claude_counter() {
  cat > "$TEST_DIR/bin/claude" << 'EOF'
#!/bin/bash
COUNTER_FILE="${SCRIPT_DIR:-/tmp}/.claude-call-count"
COUNT=0
if [ -f "$COUNTER_FILE" ]; then
  COUNT=$(cat "$COUNTER_FILE")
fi
COUNT=$((COUNT + 1))
echo "$COUNT" > "$COUNTER_FILE"
echo "Claude call #$COUNT"
exit 0
EOF
  chmod +x "$TEST_DIR/bin/claude"
  echo "0" > "$TEST_DIR/.claude-call-count"
}

# Get the claude call count
get_claude_call_count() {
  cat "$TEST_DIR/.claude-call-count" 2>/dev/null || echo "0"
}

# Create a mock claude that returns COMPLETE after N calls
create_mock_claude_complete_after() {
  local n="$1"
  cat > "$TEST_DIR/bin/claude" << EOF
#!/bin/bash
COUNTER_FILE="\${SCRIPT_DIR:-/tmp}/.claude-call-count"
COUNT=0
if [ -f "\$COUNTER_FILE" ]; then
  COUNT=\$(cat "\$COUNTER_FILE")
fi
COUNT=\$((COUNT + 1))
echo "\$COUNT" > "\$COUNTER_FILE"

if [ "\$COUNT" -ge "$n" ]; then
  echo "<promise>COMPLETE</promise>"
else
  echo "Working on iteration \$COUNT..."
fi
exit 0
EOF
  chmod +x "$TEST_DIR/bin/claude"
  echo "0" > "$TEST_DIR/.claude-call-count"
}

# Create a mock claude that updates PRD to mark story as passing
create_mock_claude_pass_story() {
  local story_id="$1"
  cat > "$TEST_DIR/bin/claude" << EOF
#!/bin/bash
# Update PRD to mark story as passing
if [ -f "\$SCRIPT_DIR/prd.json" ]; then
  jq --arg id "$story_id" '
    .userStories = [.userStories[] | if .id == \$id then .passes = true else . end]
  ' "\$SCRIPT_DIR/prd.json" > "\$SCRIPT_DIR/prd.json.tmp" && mv "\$SCRIPT_DIR/prd.json.tmp" "\$SCRIPT_DIR/prd.json"
fi
echo "Completed story $story_id"
exit 0
EOF
  chmod +x "$TEST_DIR/bin/claude"
}
