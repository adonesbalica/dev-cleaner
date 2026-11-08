# Releasing

The distribution name is `devcleaner` on PyPI, the import package is `dev_cleaner`, and the installed command is `dev-cleaner`.

## 1. Bump the version

Edit `src/dev_cleaner/__init__.py`:

```python
__version__ = "1.0.0"
```

`pyproject.toml` reads this value through `[tool.hatch.version]`, so it is the only place to change.

## 2. Verify locally

```bash
python -m pip install -e ".[dev]"
ruff check src
ruff format --check src
python -m build
```

Install the wheel in a clean virtual environment and run it from another directory:

```bash
python -m venv /tmp/devcleaner-check
/tmp/devcleaner-check/bin/pip install dist/devcleaner-*.whl
cd /tmp
/tmp/devcleaner-check/bin/dev-cleaner --version
```

On Windows, use `%TEMP%\devcleaner-check\Scripts\...` instead.

## 3. Test on TestPyPI (optional)

Create a token at <https://test.pypi.org/manage/account/token/> and run:

```bash
python -m twine upload --repository testpypi dist/*
python -m pip install --index-url https://test.pypi.org/simple/ --no-deps devcleaner
```

## 4. Publish with GitHub Actions (recommended)

`.github/workflows/release.yml` builds and publishes when a `v*` tag is pushed, using PyPI trusted publishing (OIDC), so no token is stored in the repository.

Configure the trusted publisher once at <https://pypi.org/manage/project/devcleaner/settings/publishing/>:

- Owner: `adonesbalica`
- Repository: `dev-cleaner`
- Workflow: `release.yml`
- Environment: `pypi`

Then push a tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## 5. Publish manually (alternative)

```bash
python -m twine upload dist/*
```

Use `__token__` as the username and a PyPI API token as the password. Create the token at <https://pypi.org/manage/account/token/>.
