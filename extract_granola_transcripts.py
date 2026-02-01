#!/usr/bin/env python3
"""
Granola Transcript Extractor
============================

Extracts meeting transcripts from Granola and organizes them by year/month.

Usage:
    python3 extract_transcripts.py [output_folder]                    # Extract all
    python3 extract_transcripts.py [output_folder] --date 2026-01-29  # Specific date
    python3 extract_transcripts.py [output_folder] --month 2026-01    # Specific month
    python3 extract_transcripts.py [output_folder] --search "standup" # Search by title
    python3 extract_transcripts.py --list                             # List all meetings
    python3 extract_transcripts.py --list --month 2026-01             # List for month

Requirements:
- macOS with Granola app installed
- Python 3.8+ (no external dependencies)
"""

import json
import os
import re
import sys
import argparse
from datetime import datetime
from pathlib import Path


GRANOLA_CACHE = os.path.expanduser(
    "~/Library/Application Support/Granola/cache-v3.json"
)

MONTHS = [
    "",
    "01-January",
    "02-February",
    "03-March",
    "04-April",
    "05-May",
    "06-June",
    "07-July",
    "08-August",
    "09-September",
    "10-October",
    "11-November",
    "12-December",
]


def load_granola_data():
    """Load and parse Granola's cache file."""
    if not os.path.exists(GRANOLA_CACHE):
        print(f"ERROR: Granola cache not found at {GRANOLA_CACHE}")
        print(
            "\nMake sure you have Granola installed and have recorded at least one meeting."
        )
        sys.exit(1)

    try:
        with open(GRANOLA_CACHE, "r", encoding="utf-8") as f:
            data = json.load(f)

        cache = data.get("cache", "")
        if not cache or not isinstance(cache, str):
            print("ERROR: Invalid or empty cache data in Granola file")
            sys.exit(1)

        inner = json.loads(cache)
        state = inner.get("state", {})

        return {
            "documents": state.get("documents", {}),
            "transcripts": state.get("transcripts", {}),
        }
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse Granola cache file: {e}")
        sys.exit(1)
    except OSError as e:
        print(f"ERROR: Could not read Granola cache file: {e}")
        sys.exit(1)


def parse_timestamp(ts):
    """Parse ISO timestamp to datetime."""
    if not ts:
        return None
    try:
        ts = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError, AttributeError):
        return None


def sanitize_filename(name):
    """Convert a string to a safe filename."""
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", "-", name.strip())
    name = re.sub(r"-+", "-", name)
    if len(name) > 100:
        name = name[:100]
    return name or "Untitled"


def get_transcript_text(segments):
    """Convert transcript segments to readable text with speaker labels."""
    lines = []
    for seg in segments:
        source = seg.get("source", "unknown")
        text = seg.get("text", "").strip()

        if not text:
            continue

        speaker = "ME" if source == "microphone" else "OTHERS"
        lines.append(f"**{speaker}:** {text}")

    return "\n\n".join(lines)


def detect_split_meetings(documents, transcripts):
    """Detect meetings that were split into multiple documents."""
    splits = {}
    meetings = []

    for doc_id, doc in documents.items():
        if not isinstance(doc, dict):
            continue

        trans = transcripts.get(doc_id, [])
        if not trans or not isinstance(trans, list):
            continue

        # Verify first and last elements are dicts
        if not isinstance(trans[0], dict) or not isinstance(trans[-1], dict):
            continue

        title = doc.get("title", "") or ""
        first_ts = trans[0].get("start_timestamp", "")
        last_ts = trans[-1].get("end_timestamp", "")

        start = parse_timestamp(first_ts)
        end = parse_timestamp(last_ts)

        if start and end:
            meetings.append(
                {
                    "doc_id": doc_id,
                    "title": title,
                    "start": start,
                    "end": end,
                    "is_untitled": not title or title.strip() == "",
                }
            )

    meetings.sort(key=lambda x: x["start"])

    for i, mtg in enumerate(meetings):
        if mtg["is_untitled"]:
            for j in range(i - 1, -1, -1):
                prev = meetings[j]
                gap = (mtg["start"] - prev["end"]).total_seconds()
                if 0 <= gap <= 120:
                    main_id = prev["doc_id"]
                    if main_id not in splits:
                        splits[main_id] = []
                    splits[main_id].append(mtg["doc_id"])
                    break
                elif gap > 120:
                    break

    return splits


def extract_all_meetings(documents, transcripts):
    """Extract all meetings with their transcripts."""
    meetings = []
    splits = detect_split_meetings(documents, transcripts)
    processed_as_continuation = set()

    for continuations in splits.values():
        for cont_id in continuations:
            processed_as_continuation.add(cont_id)

    for doc_id, doc in documents.items():
        if not isinstance(doc, dict):
            continue

        if doc_id in processed_as_continuation:
            continue

        trans = transcripts.get(doc_id, [])
        title = doc.get("title", "") or "[Untitled Meeting]"

        continuation_ids = splits.get(doc_id, [])
        for cont_id in continuation_ids:
            cont_trans = transcripts.get(cont_id, [])
            trans = trans + cont_trans

        if not trans or not isinstance(trans, list):
            continue

        # Verify first and last elements are dicts
        if not isinstance(trans[0], dict) or not isinstance(trans[-1], dict):
            continue

        first_ts = trans[0].get("start_timestamp", "")
        last_ts = trans[-1].get("end_timestamp", "")
        start = parse_timestamp(first_ts)
        end = parse_timestamp(last_ts)
        duration = (end - start).total_seconds() / 60 if start and end else 0

        attendees = []
        gcal = doc.get("google_calendar_event", {})
        if gcal:
            for att in gcal.get("attendees", []):
                if isinstance(att, dict) and att.get("email") and not att.get("self"):
                    name = att.get("displayName", att["email"].split("@")[0])
                    attendees.append(name)

        notes = doc.get("notes_plain", "") or doc.get("overview", "") or ""

        meetings.append(
            {
                "doc_id": doc_id,
                "title": title,
                "start": start,
                "end": end,
                "duration_minutes": round(duration, 1),
                "attendees": attendees,
                "transcript": get_transcript_text(trans),
                "notes": notes,
                "was_merged": len(continuation_ids) > 0,
            }
        )

    meetings.sort(key=lambda x: x["start"] if x["start"] else datetime.min)
    return meetings


def filter_meetings(meetings, date_filter=None, month_filter=None, search_filter=None):
    """Filter meetings by date, month, or search term."""
    filtered = meetings

    if date_filter:
        filtered = [
            m
            for m in filtered
            if m["start"] and m["start"].strftime("%Y-%m-%d") == date_filter
        ]

    if month_filter:
        filtered = [
            m
            for m in filtered
            if m["start"] and m["start"].strftime("%Y-%m") == month_filter
        ]

    if search_filter:
        search_lower = search_filter.lower()
        filtered = [m for m in filtered if search_lower in m["title"].lower()]

    return filtered


def list_meetings(meetings):
    """Print a list of meetings."""
    if not meetings:
        print("No meetings found matching your criteria.")
        return

    print(f"\nFound {len(meetings)} meeting(s):\n")
    print("-" * 80)

    for i, m in enumerate(meetings, 1):
        date_str = (
            m["start"].strftime("%Y-%m-%d %I:%M %p") if m["start"] else "Unknown date"
        )
        duration = f"{m['duration_minutes']}min" if m["duration_minutes"] else ""
        print(f"{i:3}. [{date_str}] {m['title'][:50]} ({duration})")

    print("-" * 80)
    print("\nTo extract specific meeting(s), use --date, --month, or --search options.")


def format_meeting_markdown(meeting):
    """Format a meeting as a markdown document."""
    lines = []

    lines.append(f"# {meeting['title']}")
    lines.append("")

    if meeting["start"]:
        lines.append(f"**Date:** {meeting['start'].strftime('%A, %B %d, %Y')}")
        lines.append(
            f"**Time:** {meeting['start'].strftime('%I:%M %p')} - {meeting['end'].strftime('%I:%M %p') if meeting['end'] else 'Unknown'}"
        )
    lines.append(f"**Duration:** {meeting['duration_minutes']} minutes")

    if meeting["attendees"]:
        lines.append(f"**Attendees:** {', '.join(meeting['attendees'])}")

    if meeting["was_merged"]:
        lines.append("**Note:** This transcript was merged from multiple segments")

    lines.append("")
    lines.append("---")
    lines.append("")

    if meeting["notes"]:
        lines.append("## Notes")
        lines.append("")
        lines.append(meeting["notes"])
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Transcript")
    lines.append("")
    lines.append(
        "> **Speaker Labels:** `ME` = your microphone | `OTHERS` = all remote participants (Granola doesn't distinguish individual remote speakers)"
    )
    lines.append("")
    lines.append(meeting["transcript"])

    return "\n".join(lines)


def save_meetings(meetings, output_folder):
    """Save meetings to organized folder structure."""
    output_path = Path(output_folder).expanduser()
    output_path.mkdir(parents=True, exist_ok=True)

    saved_count = 0
    skipped_count = 0

    for meeting in meetings:
        if not meeting["start"]:
            skipped_count += 1
            continue

        year = meeting["start"].strftime("%Y")
        month_num = meeting["start"].month
        month_folder = MONTHS[month_num]

        folder = output_path / year / month_folder
        folder.mkdir(parents=True, exist_ok=True)

        date_str = meeting["start"].strftime("%Y-%m-%d")
        title_safe = sanitize_filename(meeting["title"])
        filename = f"{date_str}_{title_safe}.md"

        filepath = folder / filename
        counter = 1
        while filepath.exists():
            filename = f"{date_str}_{title_safe}_{counter}.md"
            filepath = folder / filename
            counter += 1

        content = format_meeting_markdown(meeting)
        filepath.write_text(content, encoding="utf-8")
        saved_count += 1

        print(f"  Saved: {year}/{month_folder}/{filename}")

    return saved_count, skipped_count


def main():
    parser = argparse.ArgumentParser(
        description="Extract Granola meeting transcripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Extract all to default location
  %(prog)s ~/Desktop/meetings                 # Extract all to custom folder
  %(prog)s ~/Desktop/meetings --date 2026-01-29   # Extract specific date
  %(prog)s ~/Desktop/meetings --month 2026-01     # Extract specific month
  %(prog)s ~/Desktop/meetings --search "standup"  # Search by title
  %(prog)s --list                             # List all meetings
  %(prog)s --list --month 2026-01             # List meetings for a month
        """,
    )
    parser.add_argument(
        "output_folder",
        nargs="?",
        default="~/Documents/GranolaTranscripts",
        help="Output folder (default: ~/Documents/GranolaTranscripts)",
    )
    parser.add_argument(
        "--date", help="Extract only meetings from this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--month", help="Extract only meetings from this month (YYYY-MM)"
    )
    parser.add_argument("--search", help="Search meetings by title (case-insensitive)")
    parser.add_argument(
        "--list", action="store_true", help="List meetings instead of extracting"
    )

    args = parser.parse_args()

    # Load data
    data = load_granola_data()
    documents = data["documents"]
    transcripts = data["transcripts"]

    # Extract all meetings
    meetings = extract_all_meetings(documents, transcripts)

    if not meetings:
        print("No meetings with transcripts found!")
        return

    # Apply filters
    meetings = filter_meetings(
        meetings,
        date_filter=args.date,
        month_filter=args.month,
        search_filter=args.search,
    )

    # List mode
    if args.list:
        list_meetings(meetings)
        return

    # Extract mode
    if not meetings:
        print("No meetings found matching your criteria.")
        if args.date:
            print(f"  Date filter: {args.date}")
        if args.month:
            print(f"  Month filter: {args.month}")
        if args.search:
            print(f"  Search filter: {args.search}")
        return

    print("=" * 60)
    print("Granola Transcript Extractor")
    print("=" * 60)
    print()

    output_folder = os.path.expanduser(args.output_folder)
    print(f"Output folder: {output_folder}")

    if args.date:
        print(f"Filter: Date = {args.date}")
    if args.month:
        print(f"Filter: Month = {args.month}")
    if args.search:
        print(f"Filter: Title contains '{args.search}'")

    print(f"Meetings to extract: {len(meetings)}")
    print()

    # Show date range
    dates = [m["start"] for m in meetings if m["start"]]
    if dates:
        earliest = min(dates)
        latest = max(dates)
        if earliest.date() == latest.date():
            print(f"Date: {earliest.strftime('%Y-%m-%d')}")
        else:
            print(
                f"Date range: {earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}"
            )
        print()

    print("Saving transcripts...")
    saved, skipped = save_meetings(meetings, output_folder)

    print()
    print("=" * 60)
    print(f"Done! Saved {saved} meeting transcript(s)")
    if skipped:
        print(f"Skipped {skipped} meeting(s) (no valid date)")
    print(f"Location: {output_folder}")
    print("=" * 60)


if __name__ == "__main__":
    main()
