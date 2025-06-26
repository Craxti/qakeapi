"""Security headers module."""
from typing import Dict, List, Optional

class SecurityHeaders:
    """Security headers implementation."""
    
    @staticmethod
    def get_default_headers() -> Dict[str, str]:
        """Get default security headers."""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'Cache-Control': 'no-store, max-age=0'
        }
    
    @staticmethod
    def customize_csp(
        default_src: Optional[List[str]] = None,
        script_src: Optional[List[str]] = None,
        style_src: Optional[List[str]] = None,
        img_src: Optional[List[str]] = None,
        font_src: Optional[List[str]] = None,
        connect_src: Optional[List[str]] = None
    ) -> str:
        """Customize Content Security Policy."""
        policies = []
        
        def add_policy(name: str, sources: Optional[List[str]]):
            if sources is not None:
                policies.append(f"{name} {' '.join(sources)}")
        
        add_policy("default-src", default_src or ["'self'"])
        add_policy("script-src", script_src or ["'self'"])
        add_policy("style-src", style_src or ["'self'"])
        add_policy("img-src", img_src or ["'self'", "data:"])
        add_policy("font-src", font_src or ["'self'"])
        add_policy("connect-src", connect_src or ["'self'"])
        
        return "; ".join(policies)
    
    @classmethod
    def get_custom_headers(
        cls,
        hsts_max_age: int = 31536000,
        frame_options: str = 'DENY',
        permissions: Optional[Dict[str, str]] = None,
        csp_custom: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, str]:
        """Get customized security headers."""
        headers = cls.get_default_headers()
        
        # Customize HSTS
        headers['Strict-Transport-Security'] = f'max-age={hsts_max_age}; includeSubDomains'
        
        # Customize Frame Options
        if frame_options in ['DENY', 'SAMEORIGIN']:
            headers['X-Frame-Options'] = frame_options
        
        # Customize Permissions Policy
        if permissions:
            policies = []
            for feature, value in permissions.items():
                policies.append(f"{feature}={value}")
            headers['Permissions-Policy'] = ', '.join(policies)
        
        # Customize CSP
        if csp_custom:
            headers['Content-Security-Policy'] = cls.customize_csp(**csp_custom)
        
        return headers 