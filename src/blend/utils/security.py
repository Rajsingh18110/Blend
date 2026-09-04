import ipaddress
import socket
import urllib.parse
from typing import Optional

def is_safe_url(url: str, resolve_dns: bool = True) -> tuple[bool, Optional[str]]:
    """
    Validates a URL against SSRF and related vulnerabilities.
    Returns a tuple of (is_safe, resolved_ip).
    If resolve_dns=False, returns (is_safe, None).
    """
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return False, None

    if parsed.scheme not in ('http', 'https'):
        return False, None

    hostname = parsed.hostname
    if not hostname:
        return False, None

    # Block obvious local names
    if hostname.lower() in ('localhost', '127.0.0.1', '::1', '0.0.0.0'):
        return False, None
        
    if not resolve_dns:
        return True, None

    # Resolve IP and check if it's in a private/internal range
    try:
        # Use a timeout to prevent DNS rebinding attacks causing long stalls
        socket.setdefaulttimeout(3.0)
        ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip)
    except Exception:
        # If we can't resolve it, fail closed
        return False, None

    # Check for private, loopback, multicast, or cloud metadata ranges (169.254.x.x)
    if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_multicast or ip_obj.is_unspecified or ip_obj.is_reserved:
        return False, None
        
    # AWS / Cloud Metadata endpoint
    if str(ip_obj).startswith('169.254.'):
        return False, None

    return True, ip

def sanitize_html(html: str) -> str:
    """
    Hardened Ghost Mode HTML sanitization using bleach (if available) or strict BeautifulSoup cleanup.
    """
    if not html:
        return ""
        
    try:
        import bleach
        # Strict sanitization
        allowed_tags = bleach.sanitizer.ALLOWED_TAGS | {
            'p', 'div', 'span', 'br', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'strong', 'em', 'u', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'img', 'a', 'ul', 'ol', 'li', 'article', 'section', 'header', 'footer'
        }
        allowed_attrs = {
            '*': ['class', 'id', 'title'],
            'a': ['href', 'rel'],
            'img': ['src', 'alt', 'width', 'height']
        }
        return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=True)
    except ImportError:
        # Fallback to bs4 aggressive stripping
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup.find_all(['script', 'iframe', 'style', 'object', 'embed', 'applet', 'meta', 'link']):
                tag.decompose()
            for img in soup.find_all("img"):
                if img.get("width") == "1" or img.get("height") == "1":
                    img.decompose()
            # Strip dangerous attributes and pseudo-protocols
            for tag in soup.find_all(True):
                attrs_to_remove = []
                for attr in tag.attrs:
                    if attr.lower().startswith('on'): # inline JS
                        attrs_to_remove.append(attr)
                    elif attr.lower() in ('href', 'src'):
                        # Normalize control characters, tabs, newlines, and encoded whitespace
                        import re
                        raw_val = str(tag[attr]).lower()
                        # Remove all whitespace, control chars, and zero-width chars (ASCII 0-32, 127)
                        val = re.sub(r'[\x00-\x20\x7f]', '', raw_val)
                        
                        # Check against dangerous pseudo-protocols after normalization
                        if val.startswith(('javascript:', 'data:', 'vbscript:')):
                            attrs_to_remove.append(attr)
                            
                for attr in attrs_to_remove:
                    del tag[attr]
            return str(soup)
        except Exception:
            return ""
