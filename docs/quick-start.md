# Ralph Quick Start Guide

Get Ralph running in under 5 minutes.

## Prerequisites

Before starting, ensure you have:

- **Claude Code** - Install and authenticate:
  ```bash
  npm install -g @anthropic-ai/claude-code
  claude login
  ```
- **Python 3.8+** - Verify with `python3 --version`
- **Git** - Verify with `git --version`
- **jq** - Install with `brew install jq` (macOS) or `apt install jq` (Linux)

## Step 1: Set Up Your Project

```bash
# Create a new project directory
mkdir my-project && cd my-project

# Initialize git repository
git init
git commit --allow-empty -m "Initial commit"

# Create Ralph directory
mkdir -p scripts/ralph
```

## Step 2: Copy Ralph Files

```bash
# Copy ralph.sh and CLAUDE.md to your project
cp /path/to/ralph-wiggum/ralph.sh scripts/ralph/
cp /path/to/ralph-wiggum/CLAUDE.md scripts/ralph/
chmod +x scripts/ralph/ralph.sh
```

## Step 3: Create a PRD

Create `scripts/ralph/prd.json` with this minimal example:

```json
{
  "project": "My First Ralph Project",
  "branchName": "ralph/hello-world",
  "description": "A simple demo to verify Ralph is working",
  "verificationCommands": {
    "typecheck": "echo 'No typecheck configured'",
    "test": "echo 'No tests configured'"
  },
  "userStories": [
    {
      "id": "US-001",
      "title": "Create hello.txt",
      "description": "Create a simple text file to verify Ralph is running.",
      "acceptanceCriteria": [
        "File hello.txt exists in project root",
        "File contains the text 'Hello from Ralph!'"
      ],
      "priority": 1,
      "passes": false,
      "notes": ""
    },
    {
      "id": "US-002",
      "title": "Create goodbye.txt",
      "description": "Create a second file to show Ralph handles multiple stories.",
      "acceptanceCriteria": [
        "File goodbye.txt exists in project root",
        "File contains the text 'Goodbye from Ralph!'"
      ],
      "priority": 2,
      "passes": false,
      "notes": ""
    }
  ]
}
```

## Step 4: Create progress.txt

Create `scripts/ralph/progress.txt`:

```markdown
# Ralph Progress Log
Started: [Today's Date]

## Codebase Patterns
- This is a demo project
---
```

## Step 5: Run Ralph

```bash
# Navigate to Ralph directory
cd scripts/ralph

# Run Ralph (default 10 iterations)
./ralph.sh

# Or specify max iterations
./ralph.sh 5
```

## What to Expect

1. Ralph spawns a fresh Claude Code instance
2. Claude reads `prd.json` and picks the first story with `passes: false`
3. Claude implements the story and runs verification commands
4. If successful, Claude commits and marks the story as `passes: true`
5. Ralph loops until all stories pass or max iterations reached

## Verifying Success

After Ralph completes:

```bash
# Check story status
cat prd.json | jq '.userStories[] | {id, title, passes}'

# View what Ralph learned
cat progress.txt

# Review commits
git log --oneline
```

Expected output:
```json
{"id": "US-001", "title": "Create hello.txt", "passes": true}
{"id": "US-002", "title": "Create goodbye.txt", "passes": true}
```

---

## Troubleshooting

### Error: "Claude Code not found"

**Cause:** Claude Code CLI is not installed or not in PATH.

**Fix:**
```bash
npm install -g @anthropic-ai/claude-code
claude --version  # Should print version number
```

### Error: "prd.json not found"

**Cause:** PRD file is missing or in wrong location.

**Fix:**
```bash
# Verify file exists
ls scripts/ralph/prd.json

# Create if missing (see Step 3)
```

### Error: "Not a git repository"

**Cause:** Ralph requires a git repo to commit changes.

**Fix:**
```bash
git init
git commit --allow-empty -m "Initial commit"
```

### Story keeps failing after multiple iterations

**Cause:** Acceptance criteria may be unclear or too complex.

**Fix:** Review criteria for clarity, split large stories, check `progress.txt` for clues.

---

## Next Steps

1. **Add real verification commands** - Replace placeholders with actual build/test commands
2. **Set up quality gates** - Configure typecheck, lint, and test in your PRD
3. **Review security docs** - Read [SECURITY.md](SECURITY.md) before running on production code
4. **Keep stories small** - One context window per story for best results
