"""Fuzz tests for org2tc using Hypothesis."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

SCRIPT = str(Path(__file__).parent.parent / "org2tc")

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@st.composite
def valid_timestamp(draw):
    year = draw(st.integers(2020, 2025))
    month = draw(st.integers(1, 12))
    day = draw(st.integers(1, 28))
    hour = draw(st.integers(0, 23))
    minute = draw(st.integers(0, 59))
    day_name = draw(st.sampled_from(DAYS))
    return f"{year}-{month:02d}-{day:02d} {day_name} {hour:02d}:{minute:02d}"


@st.composite
def org_content(draw):
    lines = []
    header_billcode = draw(st.booleans())
    if header_billcode:
        bc = draw(st.from_regex(r"[A-Za-z]{3,10}", fullmatch=True))
        lines.append(f"#+PROPERTY: BILLCODE {bc}")
        lines.append("")

    num_headings = draw(st.integers(0, 15))
    for _ in range(num_headings):
        depth = draw(st.integers(1, 5))
        stars = "*" * depth
        keyword = draw(st.sampled_from(["", "TODO ", "DONE "]))
        title = draw(st.from_regex(r"[A-Za-z][A-Za-z0-9 ]{0,20}", fullmatch=True))
        lines.append(f"{stars} {keyword}{title}")

        if draw(st.booleans()):
            lines.append("  :PROPERTIES:")
            if draw(st.booleans()):
                bc = draw(st.from_regex(r"[A-Za-z]{3,10}", fullmatch=True))
                lines.append(f"  :BILLCODE: {bc}")
            if draw(st.booleans()):
                tc = draw(st.from_regex(r"[A-Za-z]{3,10}", fullmatch=True))
                lines.append(f"  :TASKCODE: {tc}")
            lines.append("  :END:")

        num_clocks = draw(st.integers(0, 3))
        for _ in range(num_clocks):
            ts1 = draw(valid_timestamp())
            if draw(st.booleans()):
                ts2 = draw(valid_timestamp())
                lines.append(f"  CLOCK: [{ts1}]--[{ts2}] =>  1:00")
            else:
                lines.append(f"  CLOCK: [{ts1}]")

    return "\n".join(lines)


@given(content=org_content())
@settings(max_examples=200, deadline=10000)
def test_no_crash_on_generated_org(content):
    """org2tc should not crash on valid org-like content."""
    fd, path = tempfile.mkstemp(suffix=".org")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        result = subprocess.run(
            [sys.executable, SCRIPT, path],
            capture_output=True,
            text=True,
            env={**os.environ, "LC_ALL": "C"},
            check=False,
        )
        assert result.returncode == 0, f"Crashed on input:\n{content}\n\nStderr:\n{result.stderr}"
    finally:
        os.unlink(path)


@given(content=st.text(min_size=0, max_size=500))
@settings(max_examples=100, deadline=10000)
def test_no_crash_on_random_text(content):
    """org2tc should not crash on arbitrary text input."""
    fd, path = tempfile.mkstemp(suffix=".org")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        result = subprocess.run(
            [sys.executable, SCRIPT, path],
            capture_output=True,
            text=True,
            env={**os.environ, "LC_ALL": "C"},
            check=False,
        )
        assert result.returncode == 0, f"Crashed on input:\n{content!r}\n\nStderr:\n{result.stderr}"
    finally:
        os.unlink(path)
