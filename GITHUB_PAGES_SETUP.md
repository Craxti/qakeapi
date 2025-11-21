# GitHub Pages Setup for QakeAPI

## Automatic Publishing

GitHub Pages is configured for automatic documentation publishing on every push to the `main` branch.

## Manual Setup Required

1. Go to repository settings: `Settings` → `Pages`
2. In the "Source" section, select:
   - **Source**: `GitHub Actions`
3. Save settings

## Structure

- Documentation is built from the `docs/` folder using Sphinx
- Built documentation is published to the `gh-pages` branch automatically
- Documentation URL: `https://craxti.github.io/qakeapi/`

## Local Build

To build documentation locally:

```bash
cd docs
make html
```

Built documentation will be in `docs/_build/html/`

## Documentation Updates

Documentation is automatically updated when:
- Files in the `docs/` folder are changed
- Code in `qakeapi/` is changed
- `README.md` is changed
- Workflow is manually triggered via `workflow_dispatch`

## Status Check

Check publishing status in `Actions` → `Documentation`
