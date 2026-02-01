# Granola Transcript Extractor

A Claude Code plugin that extracts and organizes your Granola meeting transcripts by year and month.

## Installation

### Option 1: Claude Code Plugin (Recommended for non-technical users)

1. Clone or download this repo
2. Copy the folder to `~/.claude/plugins/granola-extractor`
3. Restart Claude Code
4. Just ask: **"Extract my Granola transcripts"**

```bash
# Quick install
git clone https://github.com/your-org/granola-extractor.git
cp -r granola-extractor ~/.claude/plugins/
```

### Option 2: Standalone Script

Run the Python script directly:

```bash
python3 extract_granola_transcripts.py
```

## Usage

### With Claude Code (after installing plugin)

Just ask Claude naturally:

- **"Extract all my Granola transcripts"** - Exports everything
- **"Get yesterday's meeting"** - Extracts specific date
- **"Extract January meetings"** - Extracts specific month
- **"Find the standup transcript"** - Searches by title
- **"What meetings do I have?"** - Lists available meetings

### Standalone Script

```bash
# Extract all meetings
python3 extract_granola_transcripts.py

# Extract to custom folder
python3 extract_granola_transcripts.py ~/Desktop/meetings

# Extract specific date
python3 extract_granola_transcripts.py ~/Desktop/meetings --date 2026-01-29

# Extract specific month
python3 extract_granola_transcripts.py ~/Desktop/meetings --month 2026-01

# Search by title
python3 extract_granola_transcripts.py ~/Desktop/meetings --search "standup"

# List all meetings (don't extract)
python3 extract_granola_transcripts.py --list

# List meetings for a month
python3 extract_granola_transcripts.py --list --month 2026-01
```

## Output Structure

```
GranolaTranscripts/
├── 2025/
│   ├── 01-January/
│   │   ├── 2025-01-15_Team-Standup.md
│   │   └── 2025-01-16_1-on-1-with-Manager.md
│   └── 02-February/
│       └── ...
└── 2026/
    └── 01-January/
        └── ...
```

## Speaker Labels

Each transcript shows:
- **ME** = Your microphone (what you said)
- **OTHERS** = All remote participants combined

> **Note:** Granola captures your mic separately from call audio, but doesn't identify individual remote speakers. So if you're on a call with 3 people, all their voices appear as "OTHERS".

## Example Output

```markdown
# Weekly Team Standup

**Date:** Monday, January 27, 2025
**Time:** 10:00 AM - 10:30 AM
**Duration:** 28.5 minutes
**Attendees:** John Smith, Jane Doe, Bob Wilson

---

## Transcript

> **Speaker Labels:** `ME` = your microphone | `OTHERS` = all remote participants

**ME:** Good morning everyone, let's get started with our standup.

**OTHERS:** Morning! I'll go first. Yesterday I finished the API integration...

**ME:** Great work on that. Any blockers?

**OTHERS:** No blockers, but I could use a review on the PR when you get a chance.
```

## Requirements

- **macOS** (Granola is a Mac app)
- **Python 3.8+** (pre-installed on macOS)
- **Granola app** with at least one recorded meeting
- **No external dependencies**

## Troubleshooting

### "Granola cache not found"
Make sure Granola is installed and you've recorded at least one meeting.

### "No meetings found"
- Check the date/month format: `YYYY-MM-DD` for dates, `YYYY-MM` for months
- Try `--list` first to see available meetings

## Privacy

This tool only reads your **local** Granola data. Nothing is sent anywhere - your transcripts stay on your machine.

---

*Created by Guild Engineering Team*
