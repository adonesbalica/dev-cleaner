# dev-cleaner

A lightweight, cross-platform CLI tool to clean unnecessary directories from development projects.

`dev-cleaner` helps developers keep their workspaces clean by automatically detecting projects and removing generated or dependency directories such as `node_modules`, `.next`, and `dist`.

## Table of contents

- [Features](#features)
- [Supported environments](#supported-environments)
- [Requirements](#requirements)
- [Installation](#installation)
- [Tutorial](#tutorial)
- [Usage](#usage)
- [Development](#development)
- [Project structure](#project-structure)
- [Architecture](#architecture)
- [Safety](#safety)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

- **Cross-platform:** runs natively on Windows, Linux, and inside WSL.
- **Automatic backend selection:** the right filesystem implementation is picked from the workspace path.
- **Windows → WSL support:** clean Linux filesystems from Windows without leaving the terminal.
- **Configurable targets:** defaults to `node_modules`, `.next`, and `dist`, and accepts custom targets.
- **Safe by default:** asks for confirmation, supports `--dry-run`, skips symlinks and junctions, and refuses to scan a filesystem root.
- **Per-operation reporting:** failures are reported per project instead of aborting the whole run.
- **Live progress:** a spinner and elapsed timer show that a long cleanup is still running.
- **Installable:** published on PyPI as `devcleaner-cli` and exposes the `dev-cleaner` command.
- **No dependencies:** the CLI uses only the Python standard library.

## Supported environments

| Where you run it | Workspace path | Backend |
|---|---|---|
| Windows | `C:\Users\me\workspace` | `native` (Windows filesystem) |
| Windows | `/home/me/workspace` | `wsl` (default distribution) |
| Windows | `//wsl.localhost/Ubuntu/home/me/workspace` | `wsl` (distribution taken from the path) |
| Linux | `/home/me/workspace` | `native` (Linux filesystem) |
| Inside WSL | `/home/me/workspace` or `/mnt/c/...` | `native` (Linux filesystem) |

The backend is detected automatically. Use `--backend` only to override the detection.

## Requirements

- Python 3.12 or higher.
- WSL 2 with a Linux distribution such as Ubuntu (only when cleaning a Linux filesystem from Windows).

No third-party packages are required.

## Installation

The package is published on PyPI as [`devcleaner-cli`](https://pypi.org/project/devcleaner-cli/) and installs the `dev-cleaner` command.

**pipx (recommended for CLI tools):**

```bash
pipx install devcleaner-cli
```

**uv:**

```bash
uv tool install devcleaner-cli
```

**pip:**

```bash
python -m pip install --user devcleaner-cli
```

On Windows, install pipx with `py -m pip install --user pipx` and run `py -m pipx ensurepath`, then reopen the terminal.

**From source:**

```bash
git clone https://github.com/adonesbalica/dev-cleaner.git
cd dev-cleaner
pipx install .
```

After installing, `dev-cleaner` works from any directory:

```bash
dev-cleaner --version
```

If the command is not found, reopen the terminal so the updated `PATH` is loaded, or run `python -m dev_cleaner`. The package has no runtime dependencies.

## Tutorial

This walkthrough creates a throwaway workspace, so nothing real is deleted. It takes about two minutes.

### 1. Create a practice workspace

**Windows (PowerShell):**

```powershell
$demo = Join-Path $env:TEMP "dev-cleaner-demo"
New-Item -ItemType Directory -Force "$demo\app-a\node_modules\react" | Out-Null
New-Item -ItemType Directory -Force "$demo\app-a\dist" | Out-Null
New-Item -ItemType Directory -Force "$demo\app-b\.next" | Out-Null
New-Item -ItemType Directory -Force "$demo\app-c\src" | Out-Null
```

**Linux or WSL:**

```bash
demo="$(mktemp -d)"
mkdir -p "$demo/app-a/node_modules/react" "$demo/app-a/dist"
mkdir -p "$demo/app-b/.next" "$demo/app-c/src"
```

You now have three projects: `app-a` and `app-b` contain generated directories, while `app-c` contains only source code.

### 2. Preview the cleanup with a dry run

**Windows:**

```powershell
dev-cleaner -w $demo -n
```

**Linux or WSL:**

```bash
dev-cleaner -w "$demo" -n
```

Expected output:

```text
dev-cleaner 1.0.0 | native | <workspace>

would remove app-a/node_modules
would remove app-a/dist
would remove app-b/.next

3 matched (3 projects) [dry run]
```

The first line shows the tool version, the selected backend, and the workspace you passed. Nothing has been deleted; the `[dry run]` marker confirms it. The order of the lines depends on the filesystem; the counts are what matter.

### 3. Run the cleanup for real

Drop `-n` and add `-y` to skip the confirmation prompt:

```bash
dev-cleaner -w "$demo" -y
```

Expected output:

```text
dev-cleaner 1.0.0 | native | <workspace>

removed      app-a/node_modules
removed      app-a/dist
removed      app-b/.next

3 removed (3 projects)
```

On a real terminal, a single-line spinner and timer appear while the directories are removed, so a slow cleanup never looks frozen:

```text
| cleaning app-a/node_modules (1/3) 0:04
```

The line is erased when the run finishes, and the summary appends the total time when it took at least one second (for example `3 removed (3 projects) in 0:04`). When the output is piped or redirected, the spinner is skipped and only the final lines are written, which keeps the output easy to parse.

Without `-y`, the tool asks first:

```text
Remove node_modules, .next, dist from every project? [y/N]
```

Press `y` and Enter to continue, or Enter to cancel. The default is always **No**.

### 4. Verify the result

**Windows:**

```powershell
Get-ChildItem -Directory -Recurse $demo | Select-Object -ExpandProperty FullName
```

**Linux or WSL:**

```bash
find "$demo" -type d
```

Only `app-a`, `app-b`, and `app-c` (plus `app-c/src`) should remain. The generated directories are gone.

### 5. Remove the practice workspace

**Windows:**

```powershell
Remove-Item $demo -Recurse -Force
```

**Linux or WSL:**

```bash
rm -rf "$demo"
```

### Tutorial: clean a WSL workspace from Windows

Use the Linux path of the workspace. The tool detects that it is not a Windows path and switches to the WSL backend automatically.

```powershell
# See which distributions are available
wsl -l -q

# Preview the cleanup
dev-cleaner -w /home/me/workspace -n

# Use a specific distribution if the default is not the right one
dev-cleaner -w /home/me/workspace -d Ubuntu -n

# Run it
dev-cleaner -w /home/me/workspace -y
```

The header shows which backend and distribution were selected:

```text
dev-cleaner 1.0.0 | wsl:Ubuntu | /home/me/workspace
```

You can also pass a Windows UNC path such as `//wsl.localhost/Ubuntu/home/me/workspace`; the distribution is read from the path.

### Tutorial: use custom targets

Passing `-t` **replaces** the default target list, so list every directory you want to remove:

```bash
dev-cleaner -w /home/me/workspace -t node_modules -t .venv -t target -n
```

This removes only `node_modules`, `.venv`, and `target`; it does not also remove `.next` or `dist`.

### Tutorial: use it in a script

Use `-y` so the command never waits for input, and check the exit code:

**Bash:**

```bash
dev-cleaner -w /home/me/workspace -y
if [ $? -ne 0 ]; then
    echo "cleanup failed" >&2
fi
```

**PowerShell:**

```powershell
dev-cleaner -w C:/Users/me/workspace -y
if ($LASTEXITCODE -ne 0) {
    Write-Error "cleanup failed"
}
```

## Usage

```bash
dev-cleaner -w <workspace> [options]
```

### Options

| Option | Description |
|---|---|
| `-w`, `--workspace` | Workspace directory to scan. Required. |
| `-t`, `--target` | Directory to remove. Repeatable; replaces the defaults. Defaults to `node_modules`, `.next`, `dist`. |
| `-b`, `--backend` | Force `native` or `wsl`. Auto-detected by default. |
| `-d`, `--distribution` | WSL distribution to use. Defaults to the WSL default distribution, or `Ubuntu`. |
| `-n`, `--dry-run` | Show what would be removed without deleting anything. |
| `-y`, `--yes` | Do not ask for confirmation. |
| `--version` | Show the version and exit. |

### Progress indicator

While scanning or deleting, the CLI shows one animated line with the directory being removed and an elapsed timer:

```text
/ cleaning app-a/node_modules (2/7) 0:12
```

- The spinner uses plain ASCII frames (`|`, `/`, `-`, `\`), so it works in any terminal.
- The status updates before **each directory** is removed, so the name changes even when a single project takes a long time.
- The timer uses `m:ss`, switching to `h:mm:ss` after one hour.
- The line is cleared before the per-directory results are printed.
- The summary appends `in m:ss` when the run took at least one second.
- The spinner is **TTY-only**. Piped or redirected output never contains the animation, so logs and scripts stay clean.

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Success, including "nothing to remove" and a cancelled prompt. |
| `1` | Error: invalid workspace, invalid target, failed removal, or WSL unavailable. |
| `2` | Invalid command-line arguments. |
| `130` | Interrupted with Ctrl+C. |

### How it works

1. Detects the backend from the workspace path (unless `--backend` is given).
2. Maps the workspace to a scan path and, for WSL, to the equivalent Linux path.
3. Lists the direct children of the workspace as projects.
4. Checks each project for the configured target directories.
5. Removes matching directories using the selected backend, reporting every operation.

Only direct children of the workspace are treated as projects, and only direct children of each project are removed. Symlinked projects and targets, as well as Windows directory junctions, are skipped.

## Development

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/adonesbalica/dev-cleaner.git
cd dev-cleaner
python -m venv .venv
```

Activate it:

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**Linux / WSL:**

```bash
source .venv/bin/activate
```

Install the package in editable mode with the development tools:

```bash
python -m pip install -e ".[dev]"
```

Run the CLI without the console script:

```bash
python -m dev_cleaner --help
```

Run the checks and build the distribution:

```bash
ruff check src
ruff format --check src
python -m build
```

The build writes `dist/devcleaner_cli-<version>-py3-none-any.whl` and a source archive. See [RELEASING.md](https://github.com/adonesbalica/dev-cleaner/blob/main/RELEASING.md) for the publish steps.

## Project structure

```text
dev-cleaner/
├── src/
│   └── dev_cleaner/
│       ├── __init__.py
│       ├── __main__.py
│       ├── main.py
│       ├── core/
│       │   ├── __init__.py
│       │   └── cleaner.py
│       ├── cleaners/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── native.py
│       │   └── wsl.py
│       └── cli/
│           ├── __init__.py
│           ├── interface.py
│           └── parser.py
├── pyproject.toml
├── README.md
├── RELEASING.md
├── LICENSE
└── .gitignore
```

## Architecture

The project uses a strategy-based architecture to separate cleanup orchestration from filesystem operations.

- **`FileSystemCleaner`:** defines the contract for filesystem cleanup implementations.
- **`NativeCleaner`:** uses `shutil.rmtree` on the filesystem the application runs on (Windows or Linux), including retries for read-only files.
- **`WslCleaner`:** runs `wsl -d <distribution> -- rm -rf` to remove directories inside a Linux filesystem from Windows.
- **`Cleaner`:** handles workspace scanning, project detection, WSL path mapping, dry runs, and cleanup orchestration.
- **`main.py`:** detects the backend, resolves the workspace paths, and wires everything together.
- **`cli/`:** parses arguments, shows the TTY-only spinner and timer, and prints plain-text results, a summary, and the confirmation prompt. No third-party dependencies.

This design allows new filesystem cleanup implementations to be added without changing the core cleanup logic.

## Safety

Directory removal is permanent.

Before running the application, make sure that:

- The workspace path is correct.
- The target directories are the ones you intend to remove.
- The selected backend matches your environment.

Use `--dry-run` first to review what will be removed. Symlinked projects and targets are skipped, and the tool refuses to scan a filesystem root. Only direct children of the workspace are considered, so pointing `-w` at a folder that contains projects is safer than pointing it at a single project.

## Troubleshooting

| Problem | Cause and fix |
|---|---|
| `Error: Workspace not found: ...` | The path is wrong, or the WSL distribution is not running. Check the path and run `wsl -l -q` to see available distributions. |
| `Error: The wsl backend requires Windows with WSL installed.` | You forced `-b wsl` on Linux. Remove `-b wsl`; Linux paths already work with the native backend. |
| `Error: Refusing to scan a filesystem root: ...` | Pass the folder that contains your projects, not `/`, `C:\`, or a WSL distribution root. |
| `Error: Invalid target directory: ...` | Targets must be a single directory name. Do not use paths such as `src/dist` or `..`. |
| `failed ... [WinError 32]` or `Permission denied` | A file is open or read-only. Close editors, dev servers, and terminals using the directory, then retry. |
| Nothing is removed | Only direct children of the workspace are scanned. Point `-w` at the folder containing your project folders. |
| Paths with spaces do not work | Quote the path: `-w "C:/Users/me/My Projects"`. |
| Colors look wrong or appear as escape codes | Set `NO_COLOR=1`, or use a terminal with ANSI support. |
| No spinner or timer appears | The spinner is TTY-only. It is hidden when output is piped or redirected, and when `TERM=dumb`. Run the tool directly in a terminal to see it. |
| `dev-cleaner` is not recognized | Install it with `pipx install devcleaner-cli` or `uv tool install devcleaner-cli`, then reopen the terminal so `PATH` is updated. You can always run `python -m dev_cleaner` instead. |

## License

This project is licensed under the MIT License.
