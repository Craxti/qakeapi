# Security Policy

## Supported Versions

We provide security updates for the following versions of QakeAPI:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability in QakeAPI, please follow these steps:

### 1. **Do NOT** open a public GitHub issue

Security vulnerabilities should be reported privately to protect users until a fix is available.

### 2. Email the security team

Send an email to **security@qakeapi.dev** with the following information:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if any)
- Your contact information

### 3. Response timeline

- **Initial response**: Within 48 hours
- **Status update**: Within 7 days
- **Fix timeline**: Depends on severity, typically 30-90 days

### 4. Disclosure policy

- We will acknowledge receipt of your report
- We will keep you informed of the progress
- We will credit you in the security advisory (if desired)
- We will coordinate public disclosure after a fix is available

## Security Best Practices

When using QakeAPI in production:

1. **Keep dependencies updated**: Regularly update QakeAPI and its dependencies
2. **Use HTTPS**: Always use HTTPS in production
3. **Secure secrets**: Never commit secrets to version control
4. **Rate limiting**: Enable rate limiting for public APIs
5. **Input validation**: Always validate and sanitize user input
6. **Authentication**: Use strong authentication mechanisms
7. **Error handling**: Don't expose sensitive information in error messages
8. **Security headers**: Configure appropriate security headers (CSP, HSTS, etc.)

## Known Security Considerations

### JWT Tokens

- Always use strong secret keys
- Set appropriate token expiration times
- Validate tokens on every request
- Use HTTPS to prevent token interception

### Password Hashing

- Use bcrypt with appropriate cost factor
- Never store plain text passwords
- Implement password strength requirements

### CORS

- Don't use `allow_origins=["*"]` in production
- Specify exact origins when possible
- Review CORS configuration regularly

### Rate Limiting

- Configure appropriate rate limits
- Use different limits for authenticated vs anonymous users
- Monitor for abuse patterns

## Security Updates

Security updates will be:

- Released as patch versions (e.g., 0.1.1, 0.1.2)
- Documented in CHANGELOG.md
- Announced via GitHub releases
- Tagged with security labels

## Security Audit

If you're conducting a security audit or penetration test:

1. Contact us at security@qakeapi.dev before starting
2. Provide details about scope and timeline
3. We can provide test credentials or environments if needed
4. Share findings through the same security reporting process

## Thank You

We appreciate your help in keeping QakeAPI secure! Responsible disclosure helps protect all users of the framework.

