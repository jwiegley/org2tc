# CLAUDE.md - org2tc

Single-file Python script (`org2tc`, no .py extension) that converts Emacs org-mode CLOCK entries into Ledger timeclock format. Only uses Python stdlib.

## Build & Run

```bash
./org2tc myfile.org                          # direct execution
python3 org2tc myfile.org                    # explicit python3
./org2tc -s "2024-01-01 00:00:00" -e "2024-02-01 00:00:00" -b MyProject file.org
nix build                                    # build package
nix develop                                  # enter dev shell
nix flake check                              # run all checks (format, lint, tests, coverage, fuzz)
LC_ALL=C python3 -m pytest tests/ -x -v     # run tests directly
ruff check org2tc tests/ scripts/            # lint
ruff format org2tc tests/ scripts/           # format
```

## Architecture

Single-pass, line-by-line parser using module-level globals (acknowledged in a `# XXX` comment). The key pattern is **flush-on-next-heading**: when a new heading is encountered, `add_events()` commits the *previous* heading's accumulated clocks to the global `events` list.

### Global state and lifetimes

| Variable   | Lifetime     | Purpose |
|------------|-------------|---------|
| `events`   | All files   | Accumulated `(clock_in, clock_out, keyword, display_string)` tuples |
| `title`    | Per heading | Colon-joined ancestor path like `"Project:Sub:Task"` |
| `keyword`  | Per heading | `"TODO"`, `"DONE"`, or `None` |
| `clocks`   | Per heading | Pending `(clock_in, clock_out, billcode, taskcode)` tuples |
| `acct`     | Per file    | Ledger account string; initialized to `"<None>"` (truthy string, not Python None) |
| `billcode` | Per file    | Current billcode; from `#+PROPERTY: BILLCODE` header, `-b` arg, or `<Unknown>` |
| `taskcode` | Per file    | Current taskcode; starts as `None`, reset to `"Misc"` when BILLCODE is set |
| `headings` | Per file    | 9-slot array tracking heading text at each depth |

### Critical design patterns

- **BILLCODE/TASKCODE retroactive patching**: Properties appearing AFTER CLOCK entries in the same heading retroactively patch all pending clocks. The patching loops (lines 165-168, 173-176) iterate `clocks` and replace the billcode/taskcode.
- **`acct` is sticky**: Once set to `"billcode:taskcode"`, persists for all subsequent headings in the file. Not reset between headings.
- **Two heading regexes**: Line 109 stores raw text in `headings[depth]`. Line 113 triggers `add_events()`, extracts keyword, strips tags/links, and builds the colon-joined title path.

## Output format

```
i YYYY-MM-DD HH:MM:SS BILLCODE:TASKCODE  Parent:Child:Heading
o YYYY-MM-DD HH:MM:SS
```

- `i` = clock in, `o` = clock out (non-DONE), `O` = clock out (DONE task)
- Running/open clocks produce `i` with no matching `o`/`O`
- Seconds always `:00` (org timestamps lack seconds)

## Known bugs

1. **`--end` without `--start` crashes** (line 156): `clock_in < range_start` where `range_start` is `None` → `TypeError`
2. **`--start` without `--end` crashes** (line 158): `clock_in < range_end` where `range_end` is `None` → `TypeError`
3. **Running clock with `--start` crashes** (line 156): `clock_out > range_start` where `clock_out` is `None` → `TypeError`
4. **`--regex` always excludes top-level headings**: `prefix` is `None` for `*`-level headings, so the condition on line 140 is always `False`
5. **`--regex` only matches parent path**, never the current heading's own text
6. **Heading depth > 8** causes `IndexError` (`headings = [None] * 9`)
7. **BILLCODE containing `:` skips `acct` update** (line 61 condition); old `acct` leaks through
8. **Locale-dependent**: `parse_org_time` uses `%a` (abbreviated day name), so org files must match the system locale's language

## Org-mode features supported

Headings (1-8 stars), TODO/DONE keywords, `[#A/B/C]` priorities (stripped), trailing `:tags:` (stripped), leading `[[links]]` (stripped), CLOCK entries with optional end time, `:BILLCODE:`/`:TASKCODE:` properties, `#+PROPERTY: BILLCODE` file header, multiple org files.

**Not supported**: custom TODO keywords (WAITING, etc.), inherited properties, `#+PROPERTY: TASKCODE`, effort estimates, scheduled/deadline timestamps, `#+INCLUDE`, heading depth > 8.
