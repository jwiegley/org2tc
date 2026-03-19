#!/usr/bin/env python3
"""Performance benchmark for org2tc."""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPT = str(Path(__file__).parent.parent / "org2tc")
BASELINE_FILE = Path(__file__).parent.parent / ".perf_baseline.json"

NUM_HEADINGS = 500
NUM_CLOCKS_PER_HEADING = 3
NUM_RUNS = 5


def generate_org_file(path):
    """Generate a large org file for benchmarking."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    with open(path, "w") as f:
        f.write("#+PROPERTY: BILLCODE BenchProject\n\n")
        for i in range(NUM_HEADINGS):
            depth = (i % 3) + 1
            stars = "*" * depth
            keyword = "TODO" if i % 2 == 0 else "DONE"
            f.write(f"{stars} {keyword} Task {i}\n")
            f.write("  :PROPERTIES:\n")
            f.write(f"  :BILLCODE: Project{i % 10}\n")
            f.write(f"  :TASKCODE: Task{i % 5}\n")
            f.write("  :END:\n")
            for j in range(NUM_CLOCKS_PER_HEADING):
                hour = 9 + j * 2
                idx = i * NUM_CLOCKS_PER_HEADING + j
                day = idx % 28 + 1
                month = (idx // 28) % 12 + 1
                day_name = days[idx % 7]
                f.write(
                    f"  CLOCK: [2024-{month:02d}-{day:02d} {day_name} "
                    f"{hour:02d}:00]--[2024-{month:02d}-{day:02d} {day_name} "
                    f"{hour + 1:02d}:00] =>  1:00\n"
                )


def run_benchmark():
    """Run the benchmark and return median time in seconds."""
    with tempfile.NamedTemporaryFile(suffix=".org", mode="w", delete=False) as f:
        generate_org_file(f.name)
        org_file = f.name

    times = []
    for _ in range(NUM_RUNS):
        start = time.perf_counter()
        result = subprocess.run(
            [sys.executable, SCRIPT, org_file],
            capture_output=True,
            text=True,
            env={**os.environ, "LC_ALL": "C"},
            check=False,
        )
        elapsed = time.perf_counter() - start
        if result.returncode != 0:
            print(f"Error: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        times.append(elapsed)

    Path(org_file).unlink()
    times.sort()
    return times[len(times) // 2]


def main():
    median = run_benchmark()
    print(
        f"Benchmark: {median:.4f}s (median of {NUM_RUNS} runs, "
        f"{NUM_HEADINGS} headings, {NUM_CLOCKS_PER_HEADING} clocks each)"
    )

    if "--save-baseline" in sys.argv:
        BASELINE_FILE.write_text(json.dumps({"median_seconds": median}))
        print(f"Baseline saved to {BASELINE_FILE}")
    elif "--check" in sys.argv:
        if not BASELINE_FILE.exists():
            print("No baseline found. Saving current run as baseline.")
            BASELINE_FILE.write_text(json.dumps({"median_seconds": median}))
            print(f"Baseline saved: {median:.4f}s")
            return
        baseline = json.loads(BASELINE_FILE.read_text())
        baseline_time = baseline["median_seconds"]
        regression = (median - baseline_time) / baseline_time * 100
        print(f"Baseline: {baseline_time:.4f}s")
        print(f"Change: {regression:+.1f}%")
        if regression > 10.0:
            print(f"FAIL: Performance regression of {regression:.1f}% exceeds 10% threshold")
            sys.exit(1)
        print("PASS: Performance within acceptable range")
    else:
        print("\nRun with --save-baseline to save, --check to compare against baseline")


if __name__ == "__main__":
    main()
