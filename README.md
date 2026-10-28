# win-cache-sweep

A lightweight, zero-dependency Windows disk scanner and cache cleaner built entirely in standard Python.

## Features

- **Targeted Audit**: Scans User TEMP, System TEMP, Crash Dumps, and Windows Update downloads.
- **Safety Ratings**: Classifies files into `SAFE` and `CAUTION` based on file staleness and system importance.
- **Dry-Run & Clean**: Preview exact space reclamation before performing file deletion.
- **JSON Export**: Output scan report in machine-readable JSON for scripting.

## Usage

Run directly via Python 3:

```bash
python -m wincachesweep
```

### Options

- `--stale-days N`: Set staleness threshold in days (default: 14).
- `--safe-only`: Limit scan/cleanup to strictly `SAFE` items.
- `--dry-run`: Simulate file deletion and report space savings.
- `--clean`: Execute actual cleanup of safe temp files.
- `--json`: Output report as JSON.

### Examples

Perform an audit and display top space consumers:
```bash
python -m wincachesweep
```

Simulate cleaning files older than 30 days:
```bash
python -m wincachesweep --stale-days 30 --dry-run
```

Clean safe files:
```bash
python -m wincachesweep --clean --safe-only
```

## Requirements

Python 3.8+ (Windows recommended for full directory detection).
