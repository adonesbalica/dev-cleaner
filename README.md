# dev-cleaner

A lightweight, cross-platform CLI tool to clean unnecessary directories from development projects.

`dev-cleaner` helps developers keep their workspaces clean by automatically detecting projects and removing generated or dependency directories such as `node_modules`, `.next`, `dist`, and more.

## Features

- **Cross-platform support:** Run on Windows and Linux.
- **Configurable cleanup:** Choose which directories should be removed.
- **Workspace scanning:** Automatically detects project directories inside a configured workspace.
- **Multiple environments:** Supports native Windows and Linux filesystems, including WSL.
- **YAML configuration:** Customize cleanup targets and workspace settings.
- **Extensible architecture:** Platform-specific operations are separated from the core cleanup logic.

## Supported Environments

| Environment | Support |
|---|---|
| Windows | Native filesystem cleanup |
| Linux | Native filesystem cleanup |
| WSL | Linux filesystem cleanup through WSL integration |

## Requirements

- Python 3.10 or higher.
- PyYAML.
- WSL and Ubuntu (only when using WSL integration).

## Installation

Clone the repository:

```bash
git clone https://github.com/adonesbalica/dev-cleaner
cd dev-cleaner
```

Create and activate a virtual environment:

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Configuration

Configure the `config.yaml` file:

```yaml
name: dev-cleaner
version: 1.0.0

config:
  target_folders:
    - node_modules
    - .next
    - dist

  workspace_path: "/home/user/workspace"
```

The `workspace_path` should point to the workspace you want to scan, using the path format of the environment where the application is running.

## Usage

Run the application:

```bash
python main.py
```

The application scans the configured workspace, identifies project directories, and removes the configured target directories when found.

## Project Structure

```text
dev-cleaner/
├── .venv/
├── config.yaml
├── main.py
├── requirements.txt
└── README.md
```

## Safety

Directory removal is permanent. Always verify your workspace path and configured target directories before running the cleanup.

## License

This project is licensed under the MIT License.