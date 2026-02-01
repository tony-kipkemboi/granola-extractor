# Granola Transcript Extractor

Extract and organize your Granola meeting transcripts into folders by year and month.

## When to Use

Use this skill when the user wants to:
- Extract their Granola meeting transcripts
- Export Granola meetings to files
- Get a specific meeting transcript
- Extract meetings from a specific date or month
- Search for meetings by title
- List their available meetings
- Says things like "extract my Granola", "get yesterday's meeting", "find the standup transcript"

## How to Use

**Step 1: Check if Granola data exists**

```bash
if [ -f ~/Library/Application\ Support/Granola/cache-v3.json ]; then
    echo "GRANOLA_FOUND=true"
else
    echo "GRANOLA_FOUND=false"
fi
```

If not found, tell the user: "Granola data not found. Make sure you have Granola installed and have recorded at least one meeting."

**Step 2: Determine what the user wants**

Based on their request, choose the appropriate action:

| User Request | Action |
|--------------|--------|
| "Extract all my transcripts" | Extract all meetings |
| "Get yesterday's meeting" / "meeting from Jan 29" | Extract specific date |
| "Get January meetings" | Extract specific month |
| "Find the standup transcript" | Search by title |
| "What meetings do I have?" / "List my meetings" | List meetings |

**Step 3: For extraction - Ask where to save**

Use `AskUserQuestion` tool:
```
Question: "Where should I save your Granola transcripts?"
Header: "Save Location"
Options:
1. Label: "Documents folder (Recommended)", Description: "Saves to ~/Documents/GranolaTranscripts"
2. Label: "Desktop", Description: "Saves to ~/Desktop/GranolaTranscripts"
3. Label: "Custom location", Description: "Specify your own folder path"
```

**Step 4: Run the appropriate command**

```bash
SKILL_DIR="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/skills/granola-extractor}"
SCRIPT="$SKILL_DIR/skills/extract-transcripts/scripts/extract_transcripts.py"

# List all meetings:
python3 "$SCRIPT" --list

# List meetings for a specific month:
python3 "$SCRIPT" --list --month 2026-01

# Search meetings by title:
python3 "$SCRIPT" --list --search "standup"

# Extract ALL meetings:
python3 "$SCRIPT" ~/Documents/GranolaTranscripts

# Extract specific DATE (e.g., Jan 29, 2026):
python3 "$SCRIPT" ~/Documents/GranolaTranscripts --date 2026-01-29

# Extract specific MONTH:
python3 "$SCRIPT" ~/Documents/GranolaTranscripts --month 2026-01

# Extract meetings matching a SEARCH term:
python3 "$SCRIPT" ~/Documents/GranolaTranscripts --search "standup"
```

**Step 5: Summarize results**

Tell the user:
- How many meetings were extracted/found
- Date range covered
- Where files were saved (if extracting)
- Explain speaker labels: "**ME** = your voice, **OTHERS** = all remote participants combined"

## Output Structure

```
GranolaTranscripts/
├── 2025/
│   ├── 01-January/
│   │   └── 2025-01-15_Team-Standup.md
│   └── 02-February/
└── 2026/
    └── 01-January/
```

## Speaker Labels

Always explain to users:
- **ME** = What they said (their microphone)
- **OTHERS** = All remote participants combined (Granola can't identify individual speakers)

## Examples

**User:** "Extract all my Granola transcripts"
→ Ask where to save, then run without filters

**User:** "Get my meeting from yesterday"
→ Calculate yesterday's date, run with `--date YYYY-MM-DD`

**User:** "Extract January meetings"
→ Ask where to save, run with `--month 2026-01`

**User:** "Find the product review meeting"
→ Run with `--list --search "product review"` first to show matches, then extract

**User:** "What meetings do I have recorded?"
→ Run with `--list` to show all available meetings

**User:** "List my meetings from last week"
→ Run with `--list` and filter by relevant dates
