"""Tests for Chapter 4 Git workflow toolkit."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from branch_validator import validate_branch_name
from change_inventory import inventory_paths
from commit_validator import validate_commit_message


def test_valid_commit():
    result = validate_commit_message("feat(chapter-004): add commit validator")
    assert result.ok
    assert result.errors == ()


def test_invalid_commit_type():
    result = validate_commit_message("feature: add something")
    assert not result.ok


def test_vague_subject_rejected():
    result = validate_commit_message("fix: fix")
    assert not result.ok


def test_body_requires_blank_line():
    result = validate_commit_message("feat(tools): add timeout\nBody without blank line")
    assert not result.ok
    assert any("blank line" in e for e in result.errors)


def test_valid_branches():
    assert validate_branch_name("main").ok
    assert validate_branch_name("feat/git-toolkit").ok
    assert validate_branch_name("fix/http-timeout").ok
    assert validate_branch_name("docs/chapter-004").ok


def test_invalid_branch():
    result = validate_branch_name("RandomBranch")
    assert not result.ok


def test_inventory_groups_areas_and_chapters():
    inv = inventory_paths(
        [
            "book/chapter-004.md",
            "code/chapter-004/main.py",
            "BOOK_MANIFEST.md",
            "README.md",
        ]
    )
    assert "book" in inv.areas
    assert "code" in inv.areas
    assert "source_of_truth" in inv.areas
    assert "004" in inv.chapters
    assert "README.md" in inv.other


def test_inventory_summary_not_empty():
    inv = inventory_paths(["code/chapter-001/main.py"])
    lines = inv.summary_lines()
    assert any("chapter:001" in line for line in lines)
