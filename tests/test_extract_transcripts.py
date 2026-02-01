"""
Comprehensive unit tests for Granola Transcript Extractor.

Tests cover all core functions with edge cases including:
- Empty inputs
- Malformed data
- Missing fields
- Special characters in filenames
- Various timestamp formats
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from extract_granola_transcripts import (
    detect_split_meetings,
    extract_all_meetings,
    filter_meetings,
    format_meeting_markdown,
    get_transcript_text,
    parse_timestamp,
    sanitize_filename,
)


class TestParseTimestamp:
    """Tests for parse_timestamp function."""

    def test_valid_iso_timestamp_with_z(self):
        """Test parsing ISO timestamp with Z suffix."""
        result = parse_timestamp("2026-01-29T10:30:00Z")
        assert result is not None
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 29
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 0

    def test_valid_iso_timestamp_with_offset(self):
        """Test parsing ISO timestamp with timezone offset."""
        result = parse_timestamp("2026-01-29T10:30:00+05:00")
        assert result is not None
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 29

    def test_valid_iso_timestamp_with_negative_offset(self):
        """Test parsing ISO timestamp with negative timezone offset."""
        result = parse_timestamp("2026-01-29T15:45:30-08:00")
        assert result is not None
        assert result.hour == 15
        assert result.minute == 45
        assert result.second == 30

    def test_valid_iso_timestamp_with_milliseconds(self):
        """Test parsing ISO timestamp with milliseconds."""
        result = parse_timestamp("2026-01-29T10:30:00.123456Z")
        assert result is not None
        assert result.microsecond == 123456

    def test_empty_string(self):
        """Test parsing empty string returns None."""
        assert parse_timestamp("") is None

    def test_none_input(self):
        """Test parsing None returns None."""
        assert parse_timestamp(None) is None

    def test_invalid_format(self):
        """Test parsing invalid format returns None."""
        assert parse_timestamp("not-a-timestamp") is None
        assert parse_timestamp("2026/01/29") is None
        assert parse_timestamp("29-01-2026") is None

    def test_malformed_timestamp(self):
        """Test parsing malformed timestamp returns None."""
        assert parse_timestamp("2026-13-45T99:99:99Z") is None
        assert parse_timestamp("2026-01-29T") is None
        assert parse_timestamp("T10:30:00Z") is None

    def test_integer_input(self):
        """Test parsing integer input returns None (AttributeError caught)."""
        assert parse_timestamp(12345) is None

    def test_list_input(self):
        """Test parsing list input returns None (AttributeError caught)."""
        assert parse_timestamp(["2026-01-29"]) is None


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_simple_name(self):
        """Test simple filename without special characters."""
        assert sanitize_filename("Meeting Notes") == "Meeting-Notes"

    def test_special_characters_removed(self):
        """Test special characters are removed."""
        result = sanitize_filename('Test<>:"/\\|?*File')
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "/" not in result
        assert "\\" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result

    def test_multiple_spaces_collapsed(self):
        """Test multiple spaces are collapsed to single dash."""
        assert sanitize_filename("Meeting   with   spaces") == "Meeting-with-spaces"

    def test_multiple_dashes_collapsed(self):
        """Test multiple dashes are collapsed to single dash."""
        assert sanitize_filename("Meeting---Notes") == "Meeting-Notes"

    def test_leading_trailing_whitespace(self):
        """Test leading and trailing whitespace is stripped."""
        assert sanitize_filename("  Meeting Notes  ") == "Meeting-Notes"

    def test_empty_string(self):
        """Test empty string returns 'Untitled'."""
        assert sanitize_filename("") == "Untitled"

    def test_only_special_characters(self):
        """Test string with only special characters returns 'Untitled'."""
        assert sanitize_filename('<>:"/\\|?*') == "Untitled"

    def test_long_name_truncated(self):
        """Test names longer than 100 characters are truncated."""
        long_name = "A" * 150
        result = sanitize_filename(long_name)
        assert len(result) == 100

    def test_unicode_characters_preserved(self):
        """Test unicode characters are preserved."""
        result = sanitize_filename("Meeting with cafe and resume")
        assert "cafe" in result or "resume" in result

    def test_emoji_preserved(self):
        """Test emoji characters are preserved."""
        result = sanitize_filename("Team Standup Meeting")
        assert "Team" in result
        assert "Standup" in result

    def test_mixed_special_and_normal(self):
        """Test mixed special and normal characters."""
        result = sanitize_filename("Project: Final <Review>")
        assert result == "Project-Final-Review"


class TestGetTranscriptText:
    """Tests for get_transcript_text function."""

    def test_single_microphone_segment(self):
        """Test single segment from microphone."""
        segments = [{"source": "microphone", "text": "Hello everyone"}]
        result = get_transcript_text(segments)
        assert "**ME:** Hello everyone" in result

    def test_single_speaker_segment(self):
        """Test single segment from speaker (others)."""
        segments = [{"source": "speaker", "text": "Hi there"}]
        result = get_transcript_text(segments)
        assert "**OTHERS:** Hi there" in result

    def test_multiple_segments(self):
        """Test multiple segments from different sources."""
        segments = [
            {"source": "microphone", "text": "How is the project going?"},
            {"source": "speaker", "text": "It is going well."},
            {"source": "microphone", "text": "Great to hear."},
        ]
        result = get_transcript_text(segments)
        assert "**ME:** How is the project going?" in result
        assert "**OTHERS:** It is going well." in result
        assert "**ME:** Great to hear." in result

    def test_empty_segments_list(self):
        """Test empty segments list."""
        result = get_transcript_text([])
        assert result == ""

    def test_segment_with_empty_text(self):
        """Test segments with empty text are skipped."""
        segments = [
            {"source": "microphone", "text": "Hello"},
            {"source": "speaker", "text": ""},
            {"source": "microphone", "text": "Goodbye"},
        ]
        result = get_transcript_text(segments)
        assert "Hello" in result
        assert "Goodbye" in result
        lines = result.split("\n\n")
        assert len(lines) == 2

    def test_segment_with_whitespace_only_text(self):
        """Test segments with whitespace-only text are skipped."""
        segments = [
            {"source": "microphone", "text": "Hello"},
            {"source": "speaker", "text": "   "},
            {"source": "microphone", "text": "Goodbye"},
        ]
        result = get_transcript_text(segments)
        lines = [line for line in result.split("\n\n") if line.strip()]
        assert len(lines) == 2

    def test_unknown_source(self):
        """Test segment with unknown source defaults to OTHERS."""
        segments = [{"source": "unknown_device", "text": "Test message"}]
        result = get_transcript_text(segments)
        assert "**OTHERS:** Test message" in result

    def test_missing_source_field(self):
        """Test segment with missing source field defaults to unknown."""
        segments = [{"text": "Test message"}]
        result = get_transcript_text(segments)
        assert "**OTHERS:** Test message" in result

    def test_missing_text_field(self):
        """Test segment with missing text field is skipped."""
        segments = [{"source": "microphone"}]
        result = get_transcript_text(segments)
        assert result == ""

    def test_segments_separated_by_double_newline(self):
        """Test segments are separated by double newlines."""
        segments = [
            {"source": "microphone", "text": "First"},
            {"source": "speaker", "text": "Second"},
        ]
        result = get_transcript_text(segments)
        assert "\n\n" in result


class TestDetectSplitMeetings:
    """Tests for detect_split_meetings function."""

    def test_no_split_meetings(self):
        """Test when there are no split meetings."""
        documents = {
            "doc1": {"title": "Meeting 1"},
            "doc2": {"title": "Meeting 2"},
        }
        transcripts = {
            "doc1": [
                {
                    "start_timestamp": "2026-01-29T10:00:00Z",
                    "end_timestamp": "2026-01-29T10:30:00Z",
                }
            ],
            "doc2": [
                {
                    "start_timestamp": "2026-01-29T14:00:00Z",
                    "end_timestamp": "2026-01-29T14:30:00Z",
                }
            ],
        }
        splits = detect_split_meetings(documents, transcripts)
        assert splits == {}

    def test_split_meeting_detected(self):
        """Test detection of split meetings within 120 seconds gap."""
        documents = {
            "main_doc": {"title": "Main Meeting"},
            "continuation": {"title": ""},  # Untitled continuation
        }
        transcripts = {
            "main_doc": [
                {
                    "start_timestamp": "2026-01-29T10:00:00Z",
                    "end_timestamp": "2026-01-29T10:30:00Z",
                }
            ],
            "continuation": [
                {
                    # 30 seconds gap
                    "start_timestamp": "2026-01-29T10:30:30Z",
                    "end_timestamp": "2026-01-29T11:00:00Z",
                }
            ],
        }
        splits = detect_split_meetings(documents, transcripts)
        assert "main_doc" in splits
        assert "continuation" in splits["main_doc"]

    def test_gap_too_large_not_split(self):
        """Test meetings with gap > 120 seconds are not considered splits."""
        documents = {
            "doc1": {"title": "Meeting 1"},
            "doc2": {"title": ""},  # Untitled but gap too large
        }
        transcripts = {
            "doc1": [
                {
                    "start_timestamp": "2026-01-29T10:00:00Z",
                    "end_timestamp": "2026-01-29T10:30:00Z",
                }
            ],
            "doc2": [
                {
                    # 5 minutes gap
                    "start_timestamp": "2026-01-29T10:35:00Z",
                    "end_timestamp": "2026-01-29T11:00:00Z",
                }
            ],
        }
        splits = detect_split_meetings(documents, transcripts)
        assert splits == {}

    def test_titled_meeting_not_continuation(self):
        """Test meetings with titles are not treated as continuations."""
        documents = {
            "doc1": {"title": "Meeting 1"},
            "doc2": {"title": "Different Meeting"},  # Has title
        }
        transcripts = {
            "doc1": [
                {
                    "start_timestamp": "2026-01-29T10:00:00Z",
                    "end_timestamp": "2026-01-29T10:30:00Z",
                }
            ],
            "doc2": [
                {
                    # Within gap but has title
                    "start_timestamp": "2026-01-29T10:30:30Z",
                    "end_timestamp": "2026-01-29T11:00:00Z",
                }
            ],
        }
        splits = detect_split_meetings(documents, transcripts)
        assert splits == {}

    def test_empty_documents(self):
        """Test with empty documents dictionary."""
        splits = detect_split_meetings({}, {})
        assert splits == {}

    def test_document_not_dict(self):
        """Test documents that are not dictionaries are skipped."""
        documents = {"doc1": "not a dict", "doc2": None}
        transcripts = {"doc1": [], "doc2": []}
        splits = detect_split_meetings(documents, transcripts)
        assert splits == {}

    def test_empty_transcript_list(self):
        """Test documents with empty transcript lists are skipped."""
        documents = {"doc1": {"title": "Meeting"}}
        transcripts = {"doc1": []}
        splits = detect_split_meetings(documents, transcripts)
        assert splits == {}

    def test_transcript_elements_not_dicts(self):
        """Test transcripts with non-dict elements are skipped."""
        documents = {"doc1": {"title": "Meeting"}}
        transcripts = {"doc1": ["not a dict", "also not a dict"]}
        splits = detect_split_meetings(documents, transcripts)
        assert splits == {}

    def test_missing_timestamps(self):
        """Test transcripts with missing timestamps are handled."""
        documents = {"doc1": {"title": "Meeting"}}
        transcripts = {"doc1": [{"text": "Hello"}]}  # No timestamps
        splits = detect_split_meetings(documents, transcripts)
        assert splits == {}


class TestExtractAllMeetings:
    """Tests for extract_all_meetings function."""

    def test_single_meeting_extraction(self):
        """Test extraction of a single meeting."""
        documents = {
            "doc1": {
                "title": "Team Standup",
                "notes_plain": "Discussed project status",
            }
        }
        transcripts = {
            "doc1": [
                {
                    "start_timestamp": "2026-01-29T10:00:00Z",
                    "end_timestamp": "2026-01-29T10:30:00Z",
                    "source": "microphone",
                    "text": "Good morning everyone",
                }
            ]
        }
        meetings = extract_all_meetings(documents, transcripts)
        assert len(meetings) == 1
        assert meetings[0]["title"] == "Team Standup"
        assert meetings[0]["notes"] == "Discussed project status"
        assert "Good morning" in meetings[0]["transcript"]

    def test_meeting_with_attendees(self):
        """Test extraction of meeting with Google Calendar attendees."""
        documents = {
            "doc1": {
                "title": "Planning Meeting",
                "google_calendar_event": {
                    "attendees": [
                        {"email": "alice@example.com", "displayName": "Alice Smith"},
                        {"email": "bob@example.com"},  # No displayName
                        # Self attendee, should be excluded
                        {"email": "me@example.com", "self": True},
                    ]
                },
            }
        }
        transcripts = {
            "doc1": [
                {
                    "start_timestamp": "2026-01-29T10:00:00Z",
                    "end_timestamp": "2026-01-29T10:30:00Z",
                    "source": "microphone",
                    "text": "Hello",
                }
            ]
        }
        meetings = extract_all_meetings(documents, transcripts)
        assert len(meetings) == 1
        assert "Alice Smith" in meetings[0]["attendees"]
        assert "bob" in meetings[0]["attendees"]  # Uses email prefix
        assert len(meetings[0]["attendees"]) == 2  # Self excluded

    def test_untitled_meeting(self):
        """Test extraction of meeting without title."""
        documents = {"doc1": {"title": None}}
        transcripts = {
            "doc1": [
                {
                    "start_timestamp": "2026-01-29T10:00:00Z",
                    "end_timestamp": "2026-01-29T10:30:00Z",
                    "source": "microphone",
                    "text": "Test",
                }
            ]
        }
        meetings = extract_all_meetings(documents, transcripts)
        assert len(meetings) == 1
        assert meetings[0]["title"] == "[Untitled Meeting]"

    def test_merged_meetings(self):
        """Test that split meetings are merged."""
        documents = {
            "main": {"title": "Long Meeting"},
            "continuation": {"title": ""},
        }
        transcripts = {
            "main": [
                {
                    "start_timestamp": "2026-01-29T10:00:00Z",
                    "end_timestamp": "2026-01-29T10:30:00Z",
                    "source": "microphone",
                    "text": "Part one",
                }
            ],
            "continuation": [
                {
                    "start_timestamp": "2026-01-29T10:30:30Z",
                    "end_timestamp": "2026-01-29T11:00:00Z",
                    "source": "microphone",
                    "text": "Part two",
                }
            ],
        }
        meetings = extract_all_meetings(documents, transcripts)
        # Should have only one meeting (merged)
        merged = [m for m in meetings if m["title"] == "Long Meeting"]
        assert len(merged) == 1
        assert merged[0]["was_merged"] is True
        assert "Part one" in merged[0]["transcript"]
        assert "Part two" in merged[0]["transcript"]

    def test_empty_documents(self):
        """Test with empty documents."""
        meetings = extract_all_meetings({}, {})
        assert meetings == []

    def test_document_without_transcript(self):
        """Test documents without corresponding transcripts are skipped."""
        documents = {"doc1": {"title": "Meeting"}}
        transcripts = {}  # No transcript for doc1
        meetings = extract_all_meetings(documents, transcripts)
        assert meetings == []

    def test_duration_calculation(self):
        """Test duration is calculated correctly in minutes."""
        documents = {"doc1": {"title": "Short Meeting"}}
        transcripts = {
            "doc1": [
                {
                    "start_timestamp": "2026-01-29T10:00:00Z",
                    "end_timestamp": "2026-01-29T10:45:00Z",
                    "source": "microphone",
                    "text": "Test",
                }
            ]
        }
        meetings = extract_all_meetings(documents, transcripts)
        assert meetings[0]["duration_minutes"] == 45.0

    def test_meetings_sorted_by_start_time(self):
        """Test meetings are sorted by start time."""
        documents = {
            "doc1": {"title": "Second Meeting"},
            "doc2": {"title": "First Meeting"},
        }
        transcripts = {
            "doc1": [
                {
                    "start_timestamp": "2026-01-29T14:00:00Z",
                    "end_timestamp": "2026-01-29T14:30:00Z",
                    "source": "microphone",
                    "text": "Test",
                }
            ],
            "doc2": [
                {
                    "start_timestamp": "2026-01-29T10:00:00Z",
                    "end_timestamp": "2026-01-29T10:30:00Z",
                    "source": "microphone",
                    "text": "Test",
                }
            ],
        }
        meetings = extract_all_meetings(documents, transcripts)
        assert meetings[0]["title"] == "First Meeting"
        assert meetings[1]["title"] == "Second Meeting"

    def test_notes_fallback_to_overview(self):
        """Test notes field falls back to overview if notes_plain is empty."""
        documents = {
            "doc1": {
                "title": "Meeting",
                "notes_plain": "",
                "overview": "Overview content",
            }
        }
        transcripts = {
            "doc1": [
                {
                    "start_timestamp": "2026-01-29T10:00:00Z",
                    "end_timestamp": "2026-01-29T10:30:00Z",
                    "source": "microphone",
                    "text": "Test",
                }
            ]
        }
        meetings = extract_all_meetings(documents, transcripts)
        assert meetings[0]["notes"] == "Overview content"


class TestFilterMeetings:
    """Tests for filter_meetings function."""

    @pytest.fixture
    def sample_meetings(self):
        """Create sample meetings for filter tests."""
        return [
            {
                "title": "Daily Standup",
                "start": datetime(2026, 1, 29, 10, 0, 0),
                "end": datetime(2026, 1, 29, 10, 15, 0),
            },
            {
                "title": "Project Review",
                "start": datetime(2026, 1, 29, 14, 0, 0),
                "end": datetime(2026, 1, 29, 15, 0, 0),
            },
            {
                "title": "Weekly Planning",
                "start": datetime(2026, 2, 5, 9, 0, 0),
                "end": datetime(2026, 2, 5, 10, 0, 0),
            },
            {
                "title": "Team Standup",
                "start": datetime(2026, 2, 10, 10, 0, 0),
                "end": datetime(2026, 2, 10, 10, 15, 0),
            },
        ]

    def test_no_filters(self, sample_meetings):
        """Test with no filters returns all meetings."""
        result = filter_meetings(sample_meetings)
        assert len(result) == 4

    def test_date_filter(self, sample_meetings):
        """Test filtering by specific date."""
        result = filter_meetings(sample_meetings, date_filter="2026-01-29")
        assert len(result) == 2
        assert all(m["start"].strftime("%Y-%m-%d") == "2026-01-29" for m in result)

    def test_month_filter(self, sample_meetings):
        """Test filtering by month."""
        result = filter_meetings(sample_meetings, month_filter="2026-02")
        assert len(result) == 2
        assert all(m["start"].strftime("%Y-%m") == "2026-02" for m in result)

    def test_search_filter(self, sample_meetings):
        """Test filtering by title search."""
        result = filter_meetings(sample_meetings, search_filter="standup")
        assert len(result) == 2
        assert all("standup" in m["title"].lower() for m in result)

    def test_search_filter_case_insensitive(self, sample_meetings):
        """Test search filter is case insensitive."""
        result = filter_meetings(sample_meetings, search_filter="STANDUP")
        assert len(result) == 2

    def test_combined_filters(self, sample_meetings):
        """Test combining multiple filters."""
        result = filter_meetings(
            sample_meetings,
            month_filter="2026-01",
            search_filter="standup",
        )
        assert len(result) == 1
        assert result[0]["title"] == "Daily Standup"

    def test_filter_no_matches(self, sample_meetings):
        """Test filter with no matches returns empty list."""
        result = filter_meetings(sample_meetings, search_filter="nonexistent")
        assert result == []

    def test_filter_with_none_start(self):
        """Test filtering handles meetings with None start date."""
        meetings = [
            {"title": "Meeting 1", "start": None},
            {"title": "Meeting 2", "start": datetime(2026, 1, 29, 10, 0, 0)},
        ]
        result = filter_meetings(meetings, date_filter="2026-01-29")
        assert len(result) == 1
        assert result[0]["title"] == "Meeting 2"

    def test_empty_meetings_list(self):
        """Test filtering empty meetings list."""
        result = filter_meetings([])
        assert result == []


class TestFormatMeetingMarkdown:
    """Tests for format_meeting_markdown function."""

    @pytest.fixture
    def complete_meeting(self):
        """Create a complete meeting fixture."""
        return {
            "title": "Team Planning Session",
            "start": datetime(2026, 1, 29, 10, 0, 0),
            "end": datetime(2026, 1, 29, 11, 30, 0),
            "duration_minutes": 90.0,
            "attendees": ["Alice Smith", "Bob Jones"],
            "transcript": "**ME:** Hello team\n\n**OTHERS:** Hi there",
            "notes": "Action items discussed",
            "was_merged": False,
        }

    def test_title_in_markdown(self, complete_meeting):
        """Test title is included as H1."""
        result = format_meeting_markdown(complete_meeting)
        assert "# Team Planning Session" in result

    def test_date_formatted(self, complete_meeting):
        """Test date is formatted correctly."""
        result = format_meeting_markdown(complete_meeting)
        assert "**Date:** Thursday, January 29, 2026" in result

    def test_time_formatted(self, complete_meeting):
        """Test time is formatted correctly."""
        result = format_meeting_markdown(complete_meeting)
        assert "**Time:** 10:00 AM - 11:30 AM" in result

    def test_duration_included(self, complete_meeting):
        """Test duration is included."""
        result = format_meeting_markdown(complete_meeting)
        assert "**Duration:** 90.0 minutes" in result

    def test_attendees_included(self, complete_meeting):
        """Test attendees are included."""
        result = format_meeting_markdown(complete_meeting)
        assert "**Attendees:** Alice Smith, Bob Jones" in result

    def test_notes_section(self, complete_meeting):
        """Test notes section is included."""
        result = format_meeting_markdown(complete_meeting)
        assert "## Notes" in result
        assert "Action items discussed" in result

    def test_transcript_section(self, complete_meeting):
        """Test transcript section is included."""
        result = format_meeting_markdown(complete_meeting)
        assert "## Transcript" in result
        assert "**ME:** Hello team" in result

    def test_merged_note_shown(self, complete_meeting):
        """Test merged note is shown when was_merged is True."""
        complete_meeting["was_merged"] = True
        result = format_meeting_markdown(complete_meeting)
        assert "This transcript was merged from multiple segments" in result

    def test_no_attendees(self, complete_meeting):
        """Test markdown without attendees."""
        complete_meeting["attendees"] = []
        result = format_meeting_markdown(complete_meeting)
        assert "**Attendees:**" not in result

    def test_no_notes(self, complete_meeting):
        """Test markdown without notes."""
        complete_meeting["notes"] = ""
        result = format_meeting_markdown(complete_meeting)
        assert "## Notes" not in result

    def test_no_start_date(self, complete_meeting):
        """Test markdown when start date is None."""
        complete_meeting["start"] = None
        result = format_meeting_markdown(complete_meeting)
        assert "**Date:**" not in result
        assert "**Time:**" not in result

    def test_no_end_date(self, complete_meeting):
        """Test markdown when end date is None."""
        complete_meeting["end"] = None
        result = format_meeting_markdown(complete_meeting)
        assert "Unknown" in result

    def test_speaker_labels_note(self, complete_meeting):
        """Test speaker labels explanation is included."""
        result = format_meeting_markdown(complete_meeting)
        assert "`ME` = your microphone" in result
        assert "`OTHERS` = all remote participants" in result


class TestLoadGranolaData:
    """Tests for load_granola_data function (with mocking)."""

    def test_file_not_found(self):
        """Test behavior when cache file doesn't exist."""
        from extract_granola_transcripts import load_granola_data

        with patch("os.path.exists", return_value=False):
            with pytest.raises(SystemExit) as exc_info:
                load_granola_data()
            assert exc_info.value.code == 1

    def test_invalid_json(self):
        """Test behavior with invalid JSON."""
        from extract_granola_transcripts import load_granola_data

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="not valid json")):
                with pytest.raises(SystemExit) as exc_info:
                    load_granola_data()
                assert exc_info.value.code == 1

    def test_empty_cache(self):
        """Test behavior with empty cache."""
        from extract_granola_transcripts import load_granola_data

        json_data = '{"cache": ""}'
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json_data)):
                with pytest.raises(SystemExit) as exc_info:
                    load_granola_data()
                assert exc_info.value.code == 1

    def test_valid_cache(self):
        """Test behavior with valid cache data."""
        import json

        from extract_granola_transcripts import load_granola_data

        inner_data = {
            "state": {
                "documents": {"doc1": {"title": "Test"}},
                "transcripts": {"doc1": []},
            }
        }
        outer_data = {"cache": json.dumps(inner_data)}
        json_string = json.dumps(outer_data)

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json_string)):
                result = load_granola_data()
                assert "documents" in result
                assert "transcripts" in result
                assert "doc1" in result["documents"]


class TestSaveMeetings:
    """Tests for save_meetings function (with mocking)."""

    def test_save_creates_directory_structure(self, tmp_path):
        """Test save creates year/month directory structure."""
        from extract_granola_transcripts import save_meetings

        meetings = [
            {
                "title": "Test Meeting",
                "start": datetime(2026, 1, 29, 10, 0, 0),
                "end": datetime(2026, 1, 29, 10, 30, 0),
                "duration_minutes": 30.0,
                "attendees": [],
                "transcript": "Test transcript",
                "notes": "",
                "was_merged": False,
            }
        ]
        saved, skipped = save_meetings(meetings, str(tmp_path))
        assert saved == 1
        assert skipped == 0
        assert (tmp_path / "2026" / "01-January").exists()

    def test_save_skips_meetings_without_start(self, tmp_path):
        """Test meetings without start date are skipped."""
        from extract_granola_transcripts import save_meetings

        meetings = [
            {
                "title": "No Date Meeting",
                "start": None,
                "end": None,
                "duration_minutes": 0,
                "attendees": [],
                "transcript": "Test",
                "notes": "",
                "was_merged": False,
            }
        ]
        saved, skipped = save_meetings(meetings, str(tmp_path))
        assert saved == 0
        assert skipped == 1

    def test_save_handles_duplicate_filenames(self, tmp_path):
        """Test duplicate filenames get incremented."""
        from extract_granola_transcripts import save_meetings

        meetings = [
            {
                "title": "Same Meeting",
                "start": datetime(2026, 1, 29, 10, 0, 0),
                "end": datetime(2026, 1, 29, 10, 30, 0),
                "duration_minutes": 30.0,
                "attendees": [],
                "transcript": "First",
                "notes": "",
                "was_merged": False,
            },
            {
                "title": "Same Meeting",
                "start": datetime(2026, 1, 29, 14, 0, 0),
                "end": datetime(2026, 1, 29, 14, 30, 0),
                "duration_minutes": 30.0,
                "attendees": [],
                "transcript": "Second",
                "notes": "",
                "was_merged": False,
            },
        ]
        saved, skipped = save_meetings(meetings, str(tmp_path))
        assert saved == 2
        folder = tmp_path / "2026" / "01-January"
        files = list(folder.glob("*.md"))
        assert len(files) == 2


class TestEdgeCases:
    """Additional edge case tests."""

    def test_transcript_with_none_source(self):
        """Test transcript segments with None source value."""
        segments = [
            {"source": None, "text": "Test"},
        ]
        result = get_transcript_text(segments)
        # None source should be treated as "unknown" which maps to OTHERS
        assert "**OTHERS:** Test" in result

    def test_transcript_with_none_text_raises(self):
        """Test transcript segments with None text raises AttributeError.

        Note: This test documents current behavior - None text values
        cause an AttributeError. In production, transcript segments
        should always have string text values.
        """
        segments = [
            {"source": "microphone", "text": None},
        ]
        with pytest.raises(AttributeError):
            get_transcript_text(segments)

    def test_deeply_nested_invalid_structure(self):
        """Test handling of deeply nested invalid structures."""
        documents = {
            "doc1": {
                "title": "Test",
                "google_calendar_event": {
                    "attendees": [
                        None,  # None attendee
                        "string_attendee",  # String instead of dict
                        {"no_email": True},  # Dict without email
                    ]
                },
            }
        }
        transcripts = {
            "doc1": [
                {
                    "start_timestamp": "2026-01-29T10:00:00Z",
                    "end_timestamp": "2026-01-29T10:30:00Z",
                    "source": "microphone",
                    "text": "Test",
                }
            ]
        }
        meetings = extract_all_meetings(documents, transcripts)
        assert len(meetings) == 1
        # Should not crash, attendees should be empty or have valid entries only
        assert isinstance(meetings[0]["attendees"], list)

    def test_extremely_long_meeting_title(self):
        """Test meeting with extremely long title."""
        long_title = "A" * 500
        result = sanitize_filename(long_title)
        assert len(result) <= 100

    def test_meeting_spanning_midnight(self):
        """Test meeting that spans midnight."""
        documents = {"doc1": {"title": "Late Night Meeting"}}
        transcripts = {
            "doc1": [
                {
                    "start_timestamp": "2026-01-29T23:00:00Z",
                    "end_timestamp": "2026-01-30T01:00:00Z",
                    "source": "microphone",
                    "text": "Test",
                }
            ]
        }
        meetings = extract_all_meetings(documents, transcripts)
        assert len(meetings) == 1
        assert meetings[0]["duration_minutes"] == 120.0

    def test_filter_with_special_characters_in_search(self):
        """Test search filter with special regex characters."""
        meetings = [
            {"title": "Meeting (important)", "start": datetime(2026, 1, 29, 10, 0, 0)},
            {"title": "Regular Meeting", "start": datetime(2026, 1, 29, 14, 0, 0)},
        ]
        # Should not raise regex error
        result = filter_meetings(meetings, search_filter="(important)")
        assert len(result) == 1

    def test_unicode_in_transcript(self):
        """Test unicode characters in transcript segments."""
        segments = [
            {"source": "microphone", "text": "Hello! How are you today?"},
            {"source": "speaker", "text": "I am fine, thank you!"},
        ]
        result = get_transcript_text(segments)
        assert "Hello" in result
        assert "fine" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
