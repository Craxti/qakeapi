# PyPI Publishing Setup

## Adding PyPI API Token to GitHub Secrets

To enable automatic publishing to PyPI when creating releases, you need to add your PyPI API token to GitHub Secrets.

### Steps:

1. Go to your repository on GitHub: `https://github.com/Craxti/qakeapi`

2. Click on **Settings** (в настройках репозитория)

3. In the left sidebar, click on **Secrets and variables** → **Actions**

4. Click **New repository secret**

5. Fill in:
   - **Name**: `PYPI_API_TOKEN`
   - **Secret**: `4e2a1d57-1554-438e-8d8d-9a8a48a822b9` (your PyPI token)

6. Click **Add secret**

### How it works:

- The workflow (`.github/workflows/release.yml`) will automatically:
  - Build the package when you create a GitHub Release
  - Publish to PyPI using the token from secrets
  - You can also trigger it manually via "Actions" → "Release" → "Run workflow"

### Testing:

After adding the secret, you can test by:
1. Creating a new GitHub Release (tagged version like `v1.2.0`)
2. Or manually running the workflow from Actions tab

The package will be published to PyPI automatically!

