# org2tc

I've been using org-mode's clocking system to track my time for years, and I
needed a way to get that data into Ledger for proper time reporting. org2tc is
the bridge -- it reads CLOCK entries from org files and outputs timeclock format
that Ledger reads directly.

## Usage

```bash
org2tc work.org
```

It prints timeclock entries to stdout. Pipe it to Ledger for querying:

```bash
org2tc work.org | ledger -f - balance
```

### Options

```
-s, --start TIME     Only entries from this date (format: YYYY-MM-DD HH:MM:SS)
-e, --end TIME       Only entries up to this date
-r, --regex REGEX    Only entries whose heading path matches
-o, --output FILE    Write to file instead of stdout
-b, --billcode CODE  Default billcode
```

### BILLCODE and TASKCODE

org2tc reads `:BILLCODE:` and `:TASKCODE:` properties from heading drawers to
build Ledger account paths:

```org
* TODO Implement feature
  :PROPERTIES:
  :BILLCODE: ClientProject
  :TASKCODE: Development
  :END:
  CLOCK: [2024-01-15 Mon 09:00]--[2024-01-15 Mon 12:00] =>  3:00
```

This produces:

```
i 2024-01-15 09:00:00 ClientProject:Development  Implement feature
o 2024-01-15 12:00:00
```

You can also set a default billcode in the org file header:

```org
#+PROPERTY: BILLCODE ClientProject
```

### Output format

Standard timeclock format: `i` for clock-in, `o` for clock-out, `O` for final
clock-out on headings marked DONE. See the
[Ledger documentation](http://ledger-cli.org/2.6/ledger.html#Using-timeclock-to-record-billable-time)
for details.

## Building

```bash
nix build        # build the package
nix develop      # enter dev shell with all tools
nix flake check  # run all checks (format, lint, tests, coverage, fuzz)
```

### Pre-commit hooks

The repo uses [lefthook](https://github.com/evilmartians/lefthook) for
pre-commit checks. After entering the dev shell:

```bash
lefthook install
```

### Performance baseline

The first time the pre-commit performance check runs, it saves a baseline
automatically. To manually reset the baseline:

```bash
python3 scripts/benchmark.py --save-baseline
```

## License

BSD 3-Clause. See [LICENSE.md](LICENSE.md).
