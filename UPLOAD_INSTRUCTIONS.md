# PyPI Upload Instructions

## Connection Issues

When attempting to upload, a connection error occurred. This may be related to:
- Unstable internet connection
- Firewall or antivirus
- Issues on PyPI side

## Solutions

### Option 1: Run Script Later

Use the ready script `upload_to_pypi.ps1`:

```powershell
.\upload_to_pypi.ps1
```

### Option 2: Manual Upload

```powershell
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "YOUR_PYPI_TOKEN_HERE"
py -m twine upload dist/*
```

### Option 3: Use GitHub Actions (Recommended)

1. Create a release on GitHub (tag v1.1.2 already created)
2. Workflow `.github/workflows/publish.yml` will automatically upload the package to PyPI
3. Make sure the repository has the secret `PYPI_API_TOKEN` with your token

### Option 4: Check Network Settings

1. Temporarily disable firewall/antivirus
2. Check if proxy server is blocking the connection
3. Try from another computer/network

## PyPI Token

Token is saved in `upload_to_pypi.ps1` script. If the token expires, create a new one at https://pypi.org/manage/account/

## Ready Files

Packages ready for upload:
- `dist/qakeapi-1.1.2-py3-none-any.whl` (199 KB)
- `dist/qakeapi-1.1.2.tar.gz` (163 KB)
