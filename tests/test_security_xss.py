import pytest
from qakeapi.security.xss import XSSProtection, XSSMiddleware
from qakeapi.core.requests import Request
from qakeapi.core.responses import Response

@pytest.fixture
def xss_protection():
    return XSSProtection()

@pytest.fixture
def xss_middleware():
    return XSSMiddleware()

def test_clean_html():
    """Test HTML cleaning functionality."""
    value = '<script>alert("xss")</script>'
    cleaned = XSSProtection.clean_html(value)
    assert cleaned == '&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;'

def test_clean_javascript():
    """Test JavaScript cleaning functionality."""
    test_cases = [
        ('onclick="alert(1)"', 'data-removed=""'),
        ('<script>bad()</script>', ''),
        ('javascript:alert(1)', 'removed:alert(1)'),
        ('expression(alert(1))', 'removed()'),
        ('<object>bad</object>', ''),
        ('<embed src="bad.swf">', ''),
        ('<applet code="bad.class">', ''),
    ]
    
    for input_value, expected_part in test_cases:
        cleaned = XSSProtection.clean_javascript(input_value.lower())
        assert expected_part in cleaned, f"Failed for input: {input_value}"

def test_sanitize_dict():
    """Test dictionary sanitization."""
    data = {
        'safe': 'text',
        'unsafe': '<script>alert(1)</script>',
        'nested': {
            'unsafe': 'javascript:alert(1)'
        }
    }
    cleaned = XSSProtection.sanitize_dict(data)
    assert '<script>' not in cleaned['unsafe'].lower()
    assert 'removed:' in cleaned['nested']['unsafe'].lower()

@pytest.mark.asyncio
async def test_xss_middleware_request(xss_middleware):
    """Test XSS middleware request processing."""
    request = Request({
        'type': 'http',
        'method': 'POST',
        'scheme': 'http',
        'path': '/',
        'query_string': b'unsafe=<script>alert(1)</script>',
        'headers': [],
        'client': ('127.0.0.1', 8000),
    })
    request.json = {'unsafe': '<script>alert(1)</script>'}
    
    await xss_middleware.process_request(request)
    assert '<script>' not in request.json['unsafe'].lower()
    assert '<script>' not in request.query_params['unsafe'].lower()

@pytest.mark.asyncio
async def test_xss_middleware_response(xss_middleware):
    """Test XSS middleware response processing."""
    response = Response(content={'unsafe': '<script>alert(1)</script>'})
    processed = await xss_middleware.process_response(response)
    assert '<script>' not in processed.content['unsafe'].lower()

def test_complex_xss_patterns():
    """Test against various XSS patterns."""
    patterns = [
        ('<img src="x" onerror="alert(1)">', 'data-removed'),
        ('<svg><script>alert(1)</script></svg>', '&lt;svg&gt;&lt;/svg&gt;'),
        ('javascript:alert(1)', 'removed:'),
        ('<a href="javascript:alert(1)">click me</a>', 'removed:'),
        ('<script src="http://evil.com/hack.js"></script>', ''),
    ]
    
    for input_value, expected_part in patterns:
        cleaned = XSSProtection.sanitize_value(input_value)
        assert expected_part in cleaned.lower(), f"Failed for input: {input_value}\nGot: {cleaned}" 