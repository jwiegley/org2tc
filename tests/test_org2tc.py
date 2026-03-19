"""Integration tests for org2tc."""


class TestBasicClock:
    def test_single_todo_clock(self, run_org2tc):
        result = run_org2tc(
            "* TODO Task One\n  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n"
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2
        assert lines[0] == "i 2024-01-15 09:00:00 <None>  Task One"
        assert lines[1] == "o 2024-01-15 12:00:00"

    def test_done_clock_uses_capital_o(self, run_org2tc):
        result = run_org2tc(
            "* DONE Task One\n  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n"
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert lines[1] == "O 2024-01-15 12:00:00"

    def test_no_keyword_uses_lowercase_o(self, run_org2tc):
        result = run_org2tc(
            "* Task One\n  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n"
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert lines[1] == "o 2024-01-15 12:00:00"

    def test_running_clock_no_end(self, run_org2tc):
        result = run_org2tc("* TODO Task One\n  CLOCK: [2024-01-15 Mon 09:00]\n")
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 1
        assert lines[0].startswith("i 2024-01-15 09:00:00")

    def test_multiple_clocks_same_heading(self, run_org2tc):
        result = run_org2tc(
            "* TODO Task One\n"
            "  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n"
            "  CLOCK: [2024-01-15 Mon 13:00]--[2024-01-15 Mon 17:00] =>  4:00\n"
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 4

    def test_empty_file(self, run_org2tc):
        result = run_org2tc("")
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_no_clocks(self, run_org2tc):
        result = run_org2tc("* TODO Task One\n* TODO Task Two\n")
        assert result.returncode == 0
        assert result.stdout.strip() == ""


class TestHeadingHierarchy:
    def test_nested_headings_colon_path(self, run_org2tc):
        result = run_org2tc(
            "* Projects\n"
            "** TODO Implement Feature\n"
            "   CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n"
        )
        assert result.returncode == 0
        assert "Projects:Implement Feature" in result.stdout

    def test_deep_nesting(self, run_org2tc):
        result = run_org2tc(
            "* Level1\n"
            "** Level2\n"
            "*** TODO Level3\n"
            "    CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n"
        )
        assert result.returncode == 0
        assert "Level1:Level2:Level3" in result.stdout

    def test_sibling_headings(self, run_org2tc):
        result = run_org2tc(
            "* Projects\n"
            "** TODO Task A\n"
            "   CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 10:00] =>  1:00\n"
            "** TODO Task B\n"
            "   CLOCK: [2024-01-15 Mon 11:00]--[2024-01-15 Mon 12:00] =>  1:00\n"
        )
        assert result.returncode == 0
        assert "Projects:Task A" in result.stdout
        assert "Projects:Task B" in result.stdout


class TestBillcodeTaskcode:
    def test_billcode_and_taskcode(self, run_org2tc):
        result = run_org2tc(
            "* TODO Task One\n"
            "  :PROPERTIES:\n"
            "  :BILLCODE: ProjectA\n"
            "  :TASKCODE: Development\n"
            "  :END:\n"
            "  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n"
        )
        assert result.returncode == 0
        assert "ProjectA:Development  Task One" in result.stdout

    def test_retroactive_billcode(self, run_org2tc):
        """BILLCODE after CLOCK in same heading should still apply."""
        result = run_org2tc(
            "* TODO Task One\n"
            "  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n"
            "  :PROPERTIES:\n"
            "  :BILLCODE: ProjectA\n"
            "  :TASKCODE: Development\n"
            "  :END:\n"
        )
        assert result.returncode == 0
        assert "ProjectA:Development  Task One" in result.stdout

    def test_file_level_billcode(self, run_org2tc):
        result = run_org2tc(
            "\n#+PROPERTY: BILLCODE DefaultProject\n"
            "* TODO Task One\n"
            "  :PROPERTIES:\n"
            "  :TASKCODE: Coding\n"
            "  :END:\n"
            "  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n"
        )
        assert result.returncode == 0
        assert "DefaultProject:Coding  Task One" in result.stdout

    def test_billcode_flag(self, run_org2tc):
        result = run_org2tc(
            "* TODO Task One\n"
            "  :PROPERTIES:\n"
            "  :TASKCODE: Coding\n"
            "  :END:\n"
            "  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n",
            args=["-b", "FlagProject"],
        )
        assert result.returncode == 0
        assert "FlagProject:Coding  Task One" in result.stdout

    def test_billcode_sticky_across_headings(self, run_org2tc):
        """BILLCODE persists to subsequent headings."""
        result = run_org2tc(
            "* TODO Task One\n"
            "  :PROPERTIES:\n"
            "  :BILLCODE: ProjectA\n"
            "  :TASKCODE: Dev\n"
            "  :END:\n"
            "  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 10:00] =>  1:00\n"
            "* TODO Task Two\n"
            "  CLOCK: [2024-01-15 Mon 11:00]--[2024-01-15 Mon 12:00] =>  1:00\n"
        )
        assert result.returncode == 0
        assert "ProjectA:Dev  Task One" in result.stdout
        assert "ProjectA:Dev  Task Two" in result.stdout


class TestHeadingParsing:
    def test_tag_stripping(self, run_org2tc):
        result = run_org2tc(
            "* TODO Task One  :work:urgent:\n"
            "  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n"
        )
        assert result.returncode == 0
        assert "Task One" in result.stdout
        assert ":work:" not in result.stdout

    def test_link_stripping(self, run_org2tc):
        result = run_org2tc(
            "* TODO [[http://example.com][Link]] Task One\n"
            "  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n"
        )
        assert result.returncode == 0
        assert "Task One" in result.stdout
        assert "http" not in result.stdout

    def test_priority_stripping(self, run_org2tc):
        result = run_org2tc(
            "* TODO [#A] Task One\n"
            "  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n"
        )
        assert result.returncode == 0
        assert "Task One" in result.stdout
        assert "[#A]" not in result.stdout


class TestTimeRange:
    def test_start_and_end_filter(self, run_org2tc):
        result = run_org2tc(
            "* TODO Task One\n"
            "  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n"
            "  CLOCK: [2024-02-15 Thu 09:00]--[2024-02-15 Thu 12:00] =>  3:00\n",
            args=["-s", "2024-02-01 00:00:00", "-e", "2024-03-01 00:00:00"],
        )
        assert result.returncode == 0
        assert "2024-02-15" in result.stdout
        assert "2024-01-15" not in result.stdout

    def test_start_and_end_both_set(self, run_org2tc):
        result = run_org2tc(
            "* TODO Task One\n  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n",
            args=["-s", "2024-01-01 00:00:00", "-e", "2024-02-01 00:00:00"],
        )
        assert result.returncode == 0
        assert "2024-01-15" in result.stdout


class TestOutputFormat:
    def test_sorted_output(self, run_org2tc):
        result = run_org2tc(
            "* TODO Task Late\n"
            "  CLOCK: [2024-01-20 Sat 09:00]--[2024-01-20 Sat 12:00] =>  3:00\n"
            "* TODO Task Early\n"
            "  CLOCK: [2024-01-10 Wed 09:00]--[2024-01-10 Wed 12:00] =>  3:00\n"
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert "2024-01-10" in lines[0]
        assert "2024-01-20" in lines[2]

    def test_output_file(self, run_org2tc, tmp_path):
        outfile = tmp_path / "output.tc"
        result = run_org2tc(
            "* TODO Task One\n  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n",
            args=["-o", str(outfile)],
        )
        assert result.returncode == 0
        assert outfile.read_text().strip() != ""

    def test_multiple_files(self, run_org2tc):
        result = run_org2tc(
            "* TODO Task A\n  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 10:00] =>  1:00\n",
            extra_files={
                "extra.org": (
                    "* TODO Task B\n"
                    "  CLOCK: [2024-01-15 Mon 11:00]--[2024-01-15 Mon 12:00] =>  1:00\n"
                )
            },
        )
        assert result.returncode == 0
        assert "Task A" in result.stdout
        assert "Task B" in result.stdout


class TestRegexFilter:
    def test_regex_matches_parent_path(self, run_org2tc):
        result = run_org2tc(
            "* Projects\n"
            "** TODO Matching Task\n"
            "   CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00\n"
            "* Other\n"
            "** TODO Non-matching Task\n"
            "   CLOCK: [2024-01-15 Mon 13:00]--[2024-01-15 Mon 14:00] =>  1:00\n",
            args=["-r", "Projects"],
        )
        assert result.returncode == 0
        assert "Matching Task" in result.stdout
        assert "Non-matching" not in result.stdout
