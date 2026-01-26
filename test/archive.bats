#!/usr/bin/env bats
# Tests for ralph.sh branch archive functionality

load 'test_helper/common'
load 'test_helper/mocks'

setup() {
  setup_test_environment
  create_mock_claude_complete
}

teardown() {
  teardown_test_environment
}

# Create an archive test script that isolates just the archive logic
create_archive_test_script() {
  cat > "$TEST_DIR/archive_test.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$TEST_DIR"
PRD_FILE="$SCRIPT_DIR/prd.json"
PROGRESS_FILE="$SCRIPT_DIR/progress.txt"
ARCHIVE_DIR="$SCRIPT_DIR/archive"
LAST_BRANCH_FILE="$SCRIPT_DIR/.last-branch"

# Archive previous run if branch changed
if [ -f "$PRD_FILE" ] && [ -f "$LAST_BRANCH_FILE" ]; then
  CURRENT_BRANCH=$(jq -r '.branchName // empty' "$PRD_FILE" 2>/dev/null || echo "")
  LAST_BRANCH=$(cat "$LAST_BRANCH_FILE" 2>/dev/null || echo "")

  if [ -n "$CURRENT_BRANCH" ] && [ -n "$LAST_BRANCH" ] && [ "$CURRENT_BRANCH" != "$LAST_BRANCH" ]; then
    # Archive the previous run
    DATE=$(date +%Y-%m-%d)
    # Strip "ralph/" prefix from branch name for folder
    FOLDER_NAME=$(echo "$LAST_BRANCH" | sed 's|^ralph/||')
    ARCHIVE_FOLDER="$ARCHIVE_DIR/$DATE-$FOLDER_NAME"

    echo "Archiving previous run: $LAST_BRANCH"
    mkdir -p "$ARCHIVE_FOLDER"
    [ -f "$PRD_FILE" ] && cp "$PRD_FILE" "$ARCHIVE_FOLDER/"
    [ -f "$PROGRESS_FILE" ] && cp "$PROGRESS_FILE" "$ARCHIVE_FOLDER/"
    echo "Archived to: $ARCHIVE_FOLDER"

    # Reset progress file for new run
    echo "# Ralph Progress Log" > "$PROGRESS_FILE"
    echo "Started: $(date)" >> "$PROGRESS_FILE"
    echo "---" >> "$PROGRESS_FILE"
    echo "Progress file reset."
  else
    echo "No archive needed - same branch or missing data"
  fi
else
  echo "No archive needed - missing prd.json or .last-branch"
fi
EOF
  chmod +x "$TEST_DIR/archive_test.sh"
}

@test "Archives when branch changes" {
  create_archive_test_script

  # Set up previous branch state
  echo "ralph/old-feature" > "$TEST_DIR/.last-branch"
  cp "$BATS_TEST_DIRNAME/fixtures/prd_branch_change.json" "$TEST_DIR/prd.json"
  echo "Previous progress content" > "$TEST_DIR/progress.txt"

  export TEST_DIR
  run bash "$TEST_DIR/archive_test.sh"

  [ "$status" -eq 0 ]
  [[ "$output" == *"Archiving previous run"* ]]

  # Check archive directory was created
  archive_dirs=$(ls -d "$TEST_DIR/archive/"*-old-feature 2>/dev/null || echo "")
  [ -n "$archive_dirs" ]
}

@test "No archive when branch is the same" {
  create_archive_test_script

  # Same branch in both places
  echo "ralph/test-feature" > "$TEST_DIR/.last-branch"
  cp "$BATS_TEST_DIRNAME/fixtures/prd_incomplete.json" "$TEST_DIR/prd.json"
  echo "Progress content" > "$TEST_DIR/progress.txt"

  export TEST_DIR
  run bash "$TEST_DIR/archive_test.sh"

  [ "$status" -eq 0 ]
  [[ "$output" == *"No archive needed"* ]]

  # No archive directory should exist
  [ ! -d "$TEST_DIR/archive" ] || [ -z "$(ls -A "$TEST_DIR/archive" 2>/dev/null)" ]
}

@test "Strips ralph/ prefix from folder name" {
  create_archive_test_script

  echo "ralph/feature-with-prefix" > "$TEST_DIR/.last-branch"
  cp "$BATS_TEST_DIRNAME/fixtures/prd_branch_change.json" "$TEST_DIR/prd.json"
  echo "Progress content" > "$TEST_DIR/progress.txt"

  export TEST_DIR
  run bash "$TEST_DIR/archive_test.sh"

  [ "$status" -eq 0 ]

  # Check that folder name doesn't contain "ralph/"
  archive_folder=$(ls -d "$TEST_DIR/archive/"* 2>/dev/null | head -1)
  [[ "$archive_folder" == *"feature-with-prefix"* ]]
  [[ "$archive_folder" != *"ralph/"* ]]
}

@test "Resets progress.txt after archive" {
  create_archive_test_script

  echo "ralph/old-feature" > "$TEST_DIR/.last-branch"
  cp "$BATS_TEST_DIRNAME/fixtures/prd_branch_change.json" "$TEST_DIR/prd.json"
  echo "Old progress that should be archived" > "$TEST_DIR/progress.txt"

  export TEST_DIR
  run bash "$TEST_DIR/archive_test.sh"

  [ "$status" -eq 0 ]
  [[ "$output" == *"Progress file reset"* ]]

  # Check progress file was reset
  progress_content=$(cat "$TEST_DIR/progress.txt")
  [[ "$progress_content" == *"# Ralph Progress Log"* ]]
  [[ "$progress_content" == *"Started:"* ]]
  [[ "$progress_content" != *"Old progress that should be archived"* ]]
}

@test "Archive contains both prd.json and progress.txt" {
  create_archive_test_script

  echo "ralph/old-feature" > "$TEST_DIR/.last-branch"
  cp "$BATS_TEST_DIRNAME/fixtures/prd_branch_change.json" "$TEST_DIR/prd.json"
  echo "Progress to archive" > "$TEST_DIR/progress.txt"

  export TEST_DIR
  run bash "$TEST_DIR/archive_test.sh"

  [ "$status" -eq 0 ]

  archive_folder=$(ls -d "$TEST_DIR/archive/"* 2>/dev/null | head -1)
  [ -f "$archive_folder/prd.json" ]
  [ -f "$archive_folder/progress.txt" ]
}
