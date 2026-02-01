# Granola Transcript Extractor

Extract your Granola meeting transcripts with one simple command.

---

## Quick Start (2 minutes)

### Step 1: Download

Open Terminal and paste:

```bash
git clone https://github.com/tony-kipkemboi/granola-extractor.git ~/.claude/skills/granola-extractor
```

### Step 2: Use it

Open Claude Code and just ask:

> "Extract my Granola transcripts"

That's it! Claude will ask where to save them and do the rest.

---

## What You Can Ask Claude

| What you want | What to say |
|---------------|-------------|
| Get all transcripts | "Extract my Granola transcripts" |
| Get yesterday's meeting | "Get my meeting from yesterday" |
| Get a specific month | "Extract my January meetings" |
| Find a specific meeting | "Find the standup transcript" |
| See what's available | "List my Granola meetings" |

---

## Where Your Transcripts Go

Files are organized by year and month:

```
GranolaTranscripts/
├── 2025/
│   ├── 01-January/
│   │   └── 2025-01-15_Team-Standup.md
│   └── 02-February/
└── 2026/
    └── 01-January/
```

---

## Understanding Speaker Labels

In each transcript you'll see:

- **ME** = What you said (your microphone)
- **OTHERS** = Everyone else on the call

> Note: Granola can't tell individual remote speakers apart, so all other voices show as "OTHERS".

---

## Troubleshooting

**"Granola data not found"**
→ Make sure Granola is installed and you've recorded at least one meeting.

**"No meetings found"**
→ Try "List my Granola meetings" first to see what's available.

---

## For Advanced Users

You can also run the script directly:

```bash
# List all meetings
python3 ~/.claude/skills/granola-extractor/extract_granola_transcripts.py --list

# Extract all to Documents folder
python3 ~/.claude/skills/granola-extractor/extract_granola_transcripts.py

# Extract specific date
python3 ~/.claude/skills/granola-extractor/extract_granola_transcripts.py --date 2026-01-29

# Extract specific month
python3 ~/.claude/skills/granola-extractor/extract_granola_transcripts.py --month 2026-01

# Search by title
python3 ~/.claude/skills/granola-extractor/extract_granola_transcripts.py --search "standup"
```

---

## Privacy

Everything stays on your computer. Nothing is sent anywhere.

---

*Questions? Ping Tony on Slack.*
