# Contributing

## Quick Start

```bash
git clone https://github.com/harrymunro/ralph-wiggum.git
cd ralph-wiggum/flowchart
npm install
npm run dev
```

## Making Changes

- Pick a story from `prd.json` or open an issue
- Keep changes small and focused
- Update docs if you discover reusable patterns

## Quality Gates (Required)

All changes must pass these checks before committing:

```bash
npm run build    # typecheck
npm run lint     # code style
npm test         # tests
```

## Commit Format

```
feat: US-XXX - Short description
```

Examples:
- `feat: US-001 - Add user authentication`
- `fix: US-002 - Resolve login redirect bug`

## Questions?

Open an issue on GitHub.
