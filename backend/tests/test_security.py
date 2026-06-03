import unittest
from utils.security import is_safe_url, sanitize_html

class TestSecurity(unittest.TestCase):

    def test_ssrf_prevention(self):
        # Should block
        self.assertFalse(is_safe_url("http://localhost:8080")[0])
        self.assertFalse(is_safe_url("http://127.0.0.1/admin")[0])
        self.assertFalse(is_safe_url("http://0.0.0.0/test")[0])
        self.assertFalse(is_safe_url("http://169.254.169.254/latest/meta-data/")[0])
        self.assertFalse(is_safe_url("file:///etc/passwd")[0])
        self.assertFalse(is_safe_url("ftp://server.com/file")[0])
        
        # Should pass
        self.assertTrue(is_safe_url("https://google.com")[0])
        self.assertTrue(is_safe_url("http://wikipedia.org/wiki/Test")[0])

    def test_html_sanitization(self):
        malicious = '<script>alert(1)</script><p>Safe text</p><img src="test.jpg" onload="bad()">'
        clean = sanitize_html(malicious)
        self.assertNotIn('<script>', clean)
        self.assertNotIn('alert(1)', clean)
        self.assertNotIn('onload', clean)
        self.assertIn('Safe text', clean)

    def test_html_sanitization_fallback_bypasses(self):
        # Simulate fallback behavior by bypassing bleach if needed, or just testing the sanitizer works
        # This test ensures the new regex stripping logic stops obfuscated pseudo-protocols
        payloads = [
            '<a href="java\tscript:alert(1)">Click</a>',
            '<a href=" jav a script:alert(1)">Click</a>',
            '<a href="javascript&#x3a;alert(1)">Click</a>', # HTML entities might be decoded by bs4
            '<a href="&#106;&#97;&#118;&#97;&#115;&#99;&#114;&#105;&#112;&#116;&#58;alert(1)">Click</a>'
        ]
        import sys
        # Temporarily mock bleach missing to force fallback
        original_modules = sys.modules.copy()
        if 'bleach' in sys.modules:
            sys.modules['bleach'] = None
        
        try:
            for payload in payloads:
                clean = sanitize_html(payload)
                self.assertNotIn('alert(1)', clean, f"Payload bypassed fallback: {payload}")
        finally:
            sys.modules.clear()
            sys.modules.update(original_modules)

if __name__ == '__main__':
    unittest.main()
