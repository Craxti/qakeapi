# Manual PR Creation Instructions

## Quick Steps

### 1. Fork Repositories

Fork these repositories on GitHub:
- https://github.com/vinta/awesome-python (click Fork button)
- https://github.com/florimondmanca/awesome-asgi (click Fork button)

### 2. Add Your Forks and Push

```powershell
# Awesome Python
cd ../awesome-python
git remote add fork https://github.com/YOUR_USERNAME/awesome-python.git
git push fork add-qakeapi

# Awesome ASGI
cd ../awesome-asgi
git remote add fork https://github.com/YOUR_USERNAME/awesome-asgi.git
git push fork add-qakeapi
```

Replace `YOUR_USERNAME` with your GitHub username.

### 3. Create Pull Requests

After pushing, GitHub will show a banner to create PR. Or go to:

**Awesome Python:**
- https://github.com/vinta/awesome-python/compare/master...YOUR_USERNAME:awesome-python:add-qakeapi

**Awesome ASGI:**
- https://github.com/florimondmanca/awesome-asgi/compare/master...YOUR_USERNAME:awesome-asgi:add-qakeapi

### 4. PR Titles and Descriptions

**Awesome Python PR:**
- Title: `Add QakeAPI to Web Frameworks section`
- Description: See `AWESOME_LISTS_SETUP.md`

**Awesome ASGI PR:**
- Title: `Add QakeAPI to Application frameworks section`
- Description: See `AWESOME_LISTS_SETUP.md`

## Alternative: Use GitHub CLI

If you have GitHub CLI installed:

```powershell
.\create_awesome_prs.ps1
```

This script will automatically:
1. Fork repositories
2. Push branches
3. Create Pull Requests

