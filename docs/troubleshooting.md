# Troubleshooting

## Common issues

### Dependencies fail to install

- **Symptom:** `uv sync` exits with a resolver error.
- **Cause:** Python version mismatch or stale lock file.
- **Fix:** Verify `python --version` meets the minimum requirement, then run `uv lock --upgrade` and retry.

### Tests fail on a clean checkout

- **Symptom:** `uv run pytest` reports import errors or missing fixtures.
- **Cause:** Dependencies not installed or virtual environment not activated.
- **Fix:** Run `uv sync` to install all dependencies, then retry.

### Docs build produces warnings

- **Symptom:** Documentation build emits broken-link or missing-page warnings.
- **Cause:** New pages not added to navigation config, or stale cross-references.
- **Fix:** Run `check_docs_links` to identify broken references and update navigation.

## Diagnostics

Collect the following information before reporting an issue:

```bash
# System and runtime info
python --version
uv --version
git --version

# Project state
git log --oneline -5
uv run pytest --co -q  # list collected tests without running
```

Include the output of these commands in your bug report to help maintainers reproduce the issue.

## Getting help

- **GitHub Issues** — Search [existing issues](../../issues) before opening a new one. Use issue templates when available.
- **GitHub Discussions** — Ask questions and share ideas in [Discussions](../../discussions).
- **Pull requests** — If you have a fix, open a PR and reference the related issue.
- See the [Contributing guide](./contributing.md) for detailed contribution instructions.
