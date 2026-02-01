# CLAUDE.md - Project Context for Claude Code

## What This Project Is

A tool to extract Granola meeting transcripts from local Mac storage and organize them into readable markdown files by year/month.

## Project Structure

```
granola-extractor/
├── extract_granola_transcripts.py   # Main standalone script
├── skills/                          # Claude Code skill
│   └── extract-transcripts/
│       ├── SKILL.md                 # Skill instructions
│       └── scripts/
│           └── extract_transcripts.py
├── tests/
│   └── test_extract_transcripts.py  # 85 unit tests
├── pyproject.toml                   # Project config (pytest, ruff)
└── .github/workflows/tests.yml      # CI pipeline
```

## Key Files

- **`extract_granola_transcripts.py`** - The main script. Reads from `~/Library/Application Support/Granola/cache-v3.json`
- **`skills/extract-transcripts/SKILL.md`** - Instructions for Claude Code skill usage
- **`tests/test_extract_transcripts.py`** - Comprehensive unit tests (85 tests, 72% coverage)

## Development

### Setup
```bash
uv sync --dev
```

### Run Tests
```bash
uv run pytest
```

### Lint & Format
```bash
uv run ruff check .
uv run ruff format .
```

### CI
GitHub Actions runs on push to main and PRs:
- Python 3.8, 3.10, 3.12 matrix
- Ruff lint + format check
- Pytest with coverage

## Code Style

- Use ruff for linting and formatting
- Follow existing patterns in the codebase
- Add defensive error handling for external data (JSON parsing, file I/O)
- Keep the script dependency-free (stdlib only)

## Speaker Labels

Granola records two audio sources:
- `source: "microphone"` → labeled as **ME**
- `source: "system_audio"` → labeled as **OTHERS**

Granola cannot distinguish individual remote speakers.

---

## IMPORTANT: Bug Fix Workflow

**When a bug is reported, do NOT start by trying to fix it.**

Instead, follow this process:

1. **Write a test first** - Create a failing test that reproduces the bug
2. **Verify the test fails** - Run it to confirm it captures the bug
3. **Then fix the bug** - Use subagents to implement the fix
4. **Prove it with a passing test** - The previously failing test should now pass

This ensures:
- The bug is clearly understood before attempting a fix
- The fix actually solves the problem
- Regression protection for the future
