# dev-cleaner

A lightweight, cross-platform CLI tool to clean unnecessary directories from development projects.

`dev-cleaner` helps developers keep their workspaces clean by automatically detecting projects and removing generated or dependency directories such as `node_modules`, `.next`, `dist`, and more.

## Features

- **Cross-platform support:** Runs on Windows and Linux.
- **Configurable cleanup:** Choose which directories should be removed.
- **Workspace scanning:** Automatically detects project directories inside a configured workspace.
- **Multiple environments:** Supports native Windows and Linux filesystems, including WSL integration.
- **YAML configuration:** Customize cleanup targets, workspace paths, and cleanup backends.
- **Extensible architecture:** Separates core cleanup logic from filesystem-specific operations.
- **Backend selection:** Uses the appropriate cleanup implementation for each environment.

## Supported Environments

| Environment | Cleanup Backend | Description |
|---|---|---|
| Windows | `NativeCleaner` | Removes directories using the Windows filesystem. |
| Linux | `NativeCleaner` | Removes directories using the Linux filesystem. |
| Windows + WSL | `WslCleaner` | Uses WSL commands to remove directories inside a Linux filesystem. |

## Requirements

- Python 3.10 or higher.
- PyYAML.
- WSL 2 with a Linux distribution such as Ubuntu (only when using WSL integration).

## Installation

Clone the repository:

```bash
git clone https://github.com/adonesbalica/dev-cleaner.git
cd dev-cleaner
```

Create and activate a virtual environment.

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

Configure the `config.yaml` file according to your environment.

### Windows

For native Windows filesystem cleanup:

```yaml
name: dev-cleaner
version: 1.0.0

config:
  target_folders:
    - node_modules
    - .next
    - dist

  workspace_path: 'C:/Users/user/workspace'
  cleanup_backend: native
```

### Linux

For native Linux filesystem cleanup:

```yaml
name: dev-cleaner
version: 1.0.0

config:
  target_folders:
    - node_modules
    - .next
    - dist

  workspace_path: '/home/user/workspace'
  cleanup_backend: native
```

### Windows + WSL

When running the application on Windows and cleaning projects stored inside WSL, configure both the Windows-accessible workspace path and the corresponding Linux workspace path:

```yaml
name: dev-cleaner
version: 1.0.0

config:
  target_folders:
    - node_modules
    - .next
    - dist

  workspace_path: '//wsl.localhost/Ubuntu/home/user/workspace'
  cleanup_backend: wsl

  wsl:
    distribution: Ubuntu
    workspace_path: '/home/user/workspace'
```

**Configuration options:**

| Option | Description |
|---|---|
| `target_folders` | Directories to remove from each detected project. |
| `workspace_path` | Workspace path used to discover projects. |
| `cleanup_backend` | Filesystem implementation: `native` or `wsl`. |
| `wsl.distribution` | Name of the WSL distribution. |
| `wsl.workspace_path` | Linux workspace path used for WSL cleanup. |

The `workspace_path` must use the path format accessible to the application. When using WSL integration from Windows, `wsl.workspace_path` must point to the equivalent directory inside Linux.

## Usage

Run the application from the project root:

```bash
python -m src.main
```

The application:

1. Loads the configuration from `config.yaml`.
2. Selects the appropriate cleanup backend.
3. Scans the configured workspace for project directories.
4. Checks each project for the configured target directories.
5. Removes matching directories using the selected backend.

## Project Structure

```text
dev-cleaner/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── cleaner.py
│   └── cleaners/
│       ├── __init__.py
│       ├── base.py
│       ├── native.py
│       └── wsl.py
├── config.yaml
├── requirements.txt
├── README.md
└── .gitignore
```

## Architecture

The project uses a strategy-based architecture to separate cleanup orchestration from filesystem operations.

- **`FileSystemCleaner`:** Defines the contract for filesystem cleanup implementations.
- **`NativeCleaner`:** Uses Python's `shutil` module to remove directories from native filesystems.
- **`WslCleaner`:** Uses `subprocess` to execute Linux removal commands through WSL.
- **`Cleaner`:** Handles workspace scanning, project detection, and cleanup orchestration.
- **`main.py`:** Loads configuration and initializes the appropriate cleanup backend.

This design allows new filesystem cleanup implementations to be added without changing the core cleanup logic.

## Safety

Directory removal is permanent.

Before running the application, make sure that:

- The configured workspace path is correct.
- The target directories are the ones you intend to remove.
- The selected cleanup backend matches your environment.
- The WSL distribution and Linux workspace path are configured correctly when using WSL integration.

Always verify the configured paths before executing a cleanup.

## License

This project is licensed under the MIT License.