# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.2.x   | :white_check_mark: |
| 1.1.x   | :white_check_mark: |
| < 1.1   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in QakeAPI, please report it responsibly.

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead:

1. **Email** the maintainers with details of the vulnerability
2. Include steps to reproduce the issue
3. Describe the impact and potential exploit scenario
4. Allow reasonable time for a fix before public disclosure

We will acknowledge receipt of your report and work on a fix. We appreciate your help in keeping QakeAPI and its users safe.

## Security Best Practices for Deployment

When deploying QakeAPI applications to production:

- **Use HTTPS** — Always serve over TLS/SSL
- **Set secure headers** — Use appropriate security middleware
- **Validate input** — Leverage built-in validation; never trust user input
- **Limit request size** — Use `RequestSizeLimitMiddleware` to prevent DoS
- **Rate limiting** — Use `@rate_limit` on sensitive endpoints
- **Secrets** — Never commit API keys, tokens, or passwords to version control
- **Dependencies** — Keep uvicorn and other optional dependencies updated
- **CORS** — Configure `allow_origins` explicitly; avoid `["*"]` in production

## Dependency Security

QakeAPI core has **zero dependencies** — it uses only the Python standard library. This minimizes the attack surface.

For optional dependencies (uvicorn, pytest, etc.), keep them updated:

```bash
pip install --upgrade uvicorn
```
