# Granola Transcript Extractor

Extract your Granola meeting transcripts with one simple command.

---

## What This Tool Does

This tool reads the meeting transcripts that the **Granola app has already saved on your Mac**. When you record meetings with Granola, it automatically stores the transcripts in a local folder on your computer. This tool simply finds those files and exports them to readable markdown format.

**This is NOT a cloud service.** There's no login, no API, no internet connection needed. The tool just reads files that already exist on your Mac.

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

## Security & Privacy

**Your data never leaves your Mac.** Here's exactly what this tool does (and doesn't do):

**What it reads:**
- Only local files from `~/Library/Application Support/Granola/` on your computer
- These are files that the Granola app already created when you recorded meetings

**What it does NOT do:**
- No cloud connections or network requests
- No API keys required
- No data sent to any server
- No tracking or analytics
- No access to anything except your local Granola files

**Why you can trust it:**
- The code is completely open source - you can read every line
- It's a simple Python script that just reads local files and writes markdown
- No dependencies on external services
- Your meeting transcripts stay 100% on your machine

---

*Questions? Ping Tony on Slack.*
