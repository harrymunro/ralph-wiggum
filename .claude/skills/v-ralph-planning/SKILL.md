---
name: v-ralph-planning
description: "Interactive spec refinement for V-Ralph that produces machine-verifiable specs. Use when planning new features for Ralph execution. Triggers on: v-ralph planning, create v-ralph spec, plan for ralph, verifiable spec."
---

# V-Ralph Planning Skill

Create machine-verifiable specifications for the V-Ralph autonomous execution system. This skill guides you through interactive refinement until every acceptance criterion is verifiable by automated checks.

---

## The Job

1. Receive feature description from user
2. Ask clarifying questions until ALL criteria are verifiable
3. Generate prd.yml with machine-verifiable acceptance criteria
4. Output valid prd.yml to the project directory

**Important:** Do NOT implement anything. This skill produces specifications only.

---

## Core Principle: Machine-Verifiable Criteria

Every acceptance criterion MUST have a corresponding verification method that a script can execute. V-Ralph uses a three-layer validation model where the semantic auditor checks if criteria are actually met - vague criteria cause audit failures.

### Verification Methods

| Verification Type | Command Example | When to Use |
|-------------------|-----------------|-------------|
| File exists | `test -f path/to/file` | New files created |
| Content contains | `grep -q "pattern" file` | Specific code/text added |
| Command succeeds | `python -m pytest tests/test_x.py` | Tests pass |
| Output matches | `python script.py \| grep "expected"` | Runtime behavior |
| Type check | `python -m py_compile module.py` | Python syntax valid |
| Lint passes | `npm run lint` | Code style compliance |

---

## Step 1: Gather Requirements

Ask clarifying questions with lettered options for quick responses:

```
1. What is the primary goal?
   A. [Option based on context]
   B. [Option based on context]
   C. [Option based on context]
   D. Other: [please specify]

2. What files should this feature modify?
   A. Existing files only: [list them]
   B. New files in existing directories
   C. New module/directory structure
   D. Mix of existing and new
```

**Keep asking until you can write a verification command for every criterion.**

---

## Step 2: Enforce Required Elements

Every story MUST include these mandatory elements:

### Files Whitelist (REQUIRED)

Every story must specify which files the agent may edit:

```yaml
files:
  - src/module/file.py
  - tests/test_module.py
  - README.md
```

**Why:** Prevents scope creep and unintended changes. The coder agent is forbidden from touching files outside this list.

### README Update Criterion (REQUIRED)

Every story must include documentation update as an acceptance criterion:

```yaml
acceptanceCriteria:
  - "README.md documents the new feature/change"
```

**Why:** Documentation stays in sync with implementation. Users can always understand what was built.

### Typecheck/Lint Criterion (REQUIRED)

Every story must include quality gate criteria:

```yaml
acceptanceCriteria:
  - "Typecheck passes: python -m py_compile module.py"
  # or for JS/TS projects:
  - "Lint passes: npm run lint"
  - "Tests pass: npm test"
```

---

## Step 3: Validate Criteria Are Verifiable

Before finalizing each criterion, ask yourself: **"How would a script verify this?"**

### Good vs Bad Acceptance Criteria

| Bad (Vague) | Good (Verifiable) | Verification Command |
|-------------|-------------------|----------------------|
| "Works correctly" | "Returns 200 status for valid input" | `curl -s -o /dev/null -w "%{http_code}" url \| grep 200` |
| "User can log in" | "Login endpoint returns JWT token on valid credentials" | `grep -q "def login" auth.py && grep -q "jwt" auth.py` |
| "Good error handling" | "Raises ValueError with message 'Invalid ID' for non-existent records" | `python -c "..." 2>&1 \| grep "Invalid ID"` |
| "Fast performance" | "Response time under 500ms for 100 concurrent requests" | Load test with specific threshold |
| "Clean code" | "No linting errors" | `npm run lint` exits 0 |
| "Proper testing" | "Unit tests in tests/test_feature.py cover all public functions" | `test -f tests/test_feature.py && pytest tests/test_feature.py` |
| "Handles edge cases" | "Returns empty list when no results match query" | `python -c "assert search('nonexistent') == []"` |
| "UI looks good" | "Button has class 'btn-primary' and text 'Submit'" | `grep -q 'class="btn-primary".*Submit' component.html` |

### Red Flags in Criteria

If you see these words, the criterion is probably not verifiable:

- "properly", "correctly", "appropriately"
- "good", "clean", "nice"
- "easy to", "simple to"
- "handles", "supports" (without specific cases)
- "works with", "integrates with" (without specific behavior)

**Rewrite to specify the exact observable behavior.**

---

## Step 4: Story Structure

Each story in prd.yml must follow this structure:

```yaml
- id: US-001
  title: Short descriptive title
  description: As a [user], I want [feature] so that [benefit]
  files:
    - path/to/file1.py
    - path/to/file2.py
    - README.md
  acceptanceCriteria:
    - "Specific verifiable criterion with test command"
    - "Another verifiable criterion"
    - "README.md documents this feature"
    - "Typecheck passes: python -m py_compile module.py"
  priority: 1
  passes: false
  notes: ""
```

### Story Sizing

Each story must be completable in ONE iteration (one context window). If a story requires more than 2-3 files or has more than 5-7 acceptance criteria, split it.

**Too big:** "Add user authentication system"
**Right size:** "Add password hashing utility function"

---

## Step 5: Output Format

Generate prd.yml (or prd.json) with this structure:

```yaml
project: "Project Name"
branchName: "ralph/feature-name"
description: "Brief description of the feature"
verificationCommands:
  typecheck: "python -m py_compile main.py"
  test: "python -m pytest tests/ -v"
userStories:
  - id: US-001
    title: "First story title"
    description: "As a developer, I need X so that Y"
    files:
      - file1.py
      - README.md
    acceptanceCriteria:
      - "Criterion 1 with verification method"
      - "README.md documents X"
      - "Typecheck passes"
    priority: 1
    passes: false
    notes: ""
```

---

## Interactive Refinement Loop

If a criterion cannot be made verifiable, iterate with the user:

```
I notice the criterion "handles errors gracefully" is not machine-verifiable.

What specific error scenarios should be handled?
A. Invalid input format - should return 400 status
B. Missing required fields - should return descriptive error message
C. Database connection failure - should retry 3 times before failing
D. All of the above
E. Other: [please specify]

Once you specify the scenarios, I can write verifiable criteria like:
- "Returns 400 status code when input JSON is malformed"
- "Error response includes field name for missing required fields"
- "Retries database connection up to 3 times with exponential backoff"
```

---

## Verification Checklist

Before outputting the final prd.yml, verify:

- [ ] **Every** story has a `files` whitelist
- [ ] **Every** story includes README.md in files list
- [ ] **Every** story has "README.md documents..." criterion
- [ ] **Every** story has typecheck/lint pass criterion
- [ ] **Every** criterion has a corresponding verification method (even if implicit)
- [ ] No criterion uses vague words (properly, correctly, handles, etc.)
- [ ] Stories are ordered by dependency (foundations first)
- [ ] Each story is small enough for one iteration

---

## Example Complete Workflow

**User:** "I want to add a caching layer to the API"

**Claude:**
```
I'll help you create a verifiable spec for the caching layer. A few questions:

1. What caching mechanism?
   A. In-memory (dict/lru_cache)
   B. Redis
   C. File-based
   D. Other

2. Which endpoints need caching?
   A. All GET endpoints
   B. Specific endpoints: [list them]
   C. Only expensive queries

3. Cache invalidation strategy?
   A. TTL-based (specify duration)
   B. Manual invalidation on writes
   C. Both
```

**User:** "1A, 2B - just /api/reports endpoint, 3A - 5 minute TTL"

**Claude generates:**
```yaml
project: "API Caching"
branchName: "ralph/api-caching"
description: "Add in-memory caching to /api/reports endpoint"
verificationCommands:
  typecheck: "python -m py_compile api/cache.py"
  test: "python -m pytest tests/ -v"
userStories:
  - id: US-001
    title: "Add cache utility module"
    description: "As a developer, I need a caching utility so I can cache API responses."
    files:
      - api/cache.py
      - tests/test_cache.py
      - README.md
    acceptanceCriteria:
      - "api/cache.py exists with Cache class"
      - "Cache.get(key) returns None for missing keys"
      - "Cache.set(key, value, ttl=300) stores value"
      - "Cache.get(key) returns stored value before TTL"
      - "Cache.get(key) returns None after TTL expires"
      - "tests/test_cache.py has tests for all Cache methods"
      - "README.md documents Cache class usage"
      - "Typecheck passes: python -m py_compile api/cache.py"
    priority: 1
    passes: false
    notes: ""

  - id: US-002
    title: "Apply cache to reports endpoint"
    description: "As a user, I want faster report loading through caching."
    files:
      - api/reports.py
      - tests/test_reports.py
      - README.md
    acceptanceCriteria:
      - "api/reports.py imports and uses Cache from api/cache"
      - "GET /api/reports checks cache before database query"
      - "Cache hit returns cached response (verified by mock)"
      - "Cache miss queries database and stores result"
      - "tests/test_reports.py verifies cache integration"
      - "README.md documents caching behavior"
      - "Typecheck passes: python -m py_compile api/reports.py"
    priority: 2
    passes: false
    notes: ""
```

Each criterion above can be verified:
- File existence: `test -f api/cache.py`
- Class exists: `grep -q "class Cache" api/cache.py`
- Method behavior: Unit tests verify
- README updated: `grep -q "Cache" README.md`
- Typecheck: `python -m py_compile api/cache.py`

---

## Remember

The V-Ralph semantic auditor will review implementations against these criteria. Vague criteria cause audit failures because the auditor cannot determine if they are satisfied. **Every criterion must be checkable by a machine.**
