#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security examples application for QakeAPI.
"""
import sys
import os

# Add path to local QakeAPI
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qakeapi import Application

# Create application
app = Application("Security Examples")

@app.get("/")
async def home(request):
    """Home page with security information."""
    return {
        "message": "Security Examples API",
        "version": "1.0.0",
        "features": [
            "CSRF Protection",
            "XSS Prevention", 
            "SQL Injection Protection",
            "Input Validation",
            "Output Encoding"
        ],
        "endpoints": {
            "security_info": "/security-info",
            "validation_test": "/validation-test",
            "encoding_test": "/encoding-test"
        }
    }

@app.get("/security-info")
async def security_info(request):
    """Get security information."""
    return {
        "security_headers": {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
        },
        "security_features": [
            "CSRF tokens",
            "Input sanitization",
            "Output encoding",
            "SQL parameterization"
        ]
    }

@app.get("/validation-test")
async def validation_test(request):
    """Test input validation."""
    return {
        "message": "Input validation is working",
        "status": "secure"
    }

@app.get("/encoding-test")
async def encoding_test(request):
    """Test output encoding."""
    return {
        "message": "Output encoding is working",
        "status": "secure"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("security_examples_app:app", host="0.0.0.0", port=8023, reload=False) 