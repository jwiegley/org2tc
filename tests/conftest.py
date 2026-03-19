import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = str(Path(__file__).parent.parent / "org2tc")
PROJECT_ROOT = str(Path(__file__).parent.parent)


@pytest.fixture()
def run_org2tc(tmp_path):
    """Run org2tc on org content and return the subprocess result."""

    def _run(org_content, args=None, extra_files=None):
        org_file = tmp_path / "test.org"
        org_file.write_text(org_content)

        use_coverage = os.environ.get("ORG2TC_COVERAGE") == "1"
        if use_coverage:
            cmd = [
                sys.executable,
                "-m",
                "coverage",
                "run",
                "--append",
                f"--rcfile={Path(PROJECT_ROOT) / 'pyproject.toml'}",
                SCRIPT,
            ]
        else:
            cmd = [sys.executable, SCRIPT]

        if args:
            cmd.extend(args)

        cmd.append(str(org_file))

        if extra_files:
            for name, content in extra_files.items():
                f = tmp_path / name
                f.write_text(content)
                cmd.append(str(f))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env={**os.environ, "LC_ALL": "C"},
            check=False,
        )
        return result

    return _run
