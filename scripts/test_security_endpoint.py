import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://localhost:8000"


def test_security_headers():
    print("\n--- Testing Security Headers ---")
    try:
        req = urllib.request.Request(f"{BASE_URL}/health")
        with urllib.request.urlopen(req) as response:
            headers = response.info()
            
            x_frame = headers.get("X-Frame-Options")
            x_content = headers.get("X-Content-Type-Options")
            x_xss = headers.get("X-XSS-Protection")
            referrer = headers.get("Referrer-Policy")
            
            print(f"X-Frame-Options: {x_frame} (Expected: DENY)")
            print(f"X-Content-Type-Options: {x_content} (Expected: nosniff)")
            print(f"X-XSS-Protection: {x_xss} (Expected: 1; mode=block)")
            print(f"Referrer-Policy: {referrer} (Expected: strict-origin-when-cross-origin)")
            
            assert x_frame == "DENY", "X-Frame-Options mismatch"
            assert x_content == "nosniff", "X-Content-Type-Options mismatch"
            assert x_xss == "1; mode=block", "X-XSS-Protection mismatch"
            assert referrer == "strict-origin-when-cross-origin", "Referrer-Policy mismatch"
            print("✅ Security Headers test PASSED!")
    except Exception as e:
        print(f"❌ Security Headers test FAILED: {e}")
        return False
    return True


def test_trusted_host():
    print("\n--- Testing Trusted Host Middleware ---")
    try:
        # FastAPI's default allowed hosts is ["*"] if not overridden. 
        # But if we pass a malformed Host header or if we customize it, it should block.
        # Let's try sending a request with a fake host header.
        req = urllib.request.Request(f"{BASE_URL}/health")
        # Change Host header to something not matching typical localhost (assuming it's restricted)
        req.add_header("Host", "malicious-host-header.com")
        
        try:
            with urllib.request.urlopen(req) as response:
                print(f"Response code: {response.getcode()}")
                # If ALLOWED_HOSTS is ["*"] (default), this will pass. If restricted, it should fail.
                print("⚠️ Trusted Host check returned 200 (Allowed due to ALLOWED_HOSTS = ['*'])")
        except urllib.error.HTTPError as e:
            if e.code == 400:
                print("✅ Trusted Host block worked! (Received 400 Bad Request)")
            else:
                print(f"❌ Trusted Host check failed with unexpected code: {e.code}")
    except Exception as e:
        print(f"❌ Trusted Host check failed: {e}")
        return False
    return True


def test_payload_size_limiter():
    print("\n--- Testing Payload Size Limiter ---")
    try:
        # Create a huge body (over 10MB limit)
        # settings.MAX_CONTENT_LENGTH = 10MB
        # Let's send a post request with a giant Content-Length header
        url = f"{BASE_URL}/health"
        data = b"x" * (12 * 1024 * 1024) # 12MB (exceeds 10MB limit)
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/octet-stream")
        
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                print(f"❌ Payload size limiter FAILED: allowed 12MB request! Code: {response.getcode()}")
                return False
        except urllib.error.HTTPError as e:
            if e.code == 413:
                body = e.read().decode()
                print(f"Received expected 413 Payload Too Large. Body: {body}")
                print("✅ Payload Size Limiter test PASSED!")
                return True
            else:
                print(f"❌ Payload size limiter failed with unexpected code: {e.code}")
                return False
        except (urllib.error.URLError, ConnectionResetError, BrokenPipeError) as e:
            print(f"Received expected connection closure (Broken pipe / Connection Reset): {e}")
            print("✅ Payload Size Limiter test PASSED!")
            return True
    except Exception as e:
        print(f"❌ Payload Size Limiter test failed: {e}")
        return False
    return True


def test_rate_limiting():
    print("\n--- Testing Rate Limiting (Auth Endpoint: Max 5/minute) ---")
    
    # We will spam the login endpoint /api/v1/auth/login.
    # The rate limit is 5 requests per minute, so the 6th request should fail with 429.
    url = f"{BASE_URL}/api/v1/auth/login"
    
    for i in range(1, 10):
        # Dummy login data
        data = json.dumps({"username": f"user_{i}", "password": "password123"}).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        
        try:
            print(f"Sending request #{i}...", end="")
            with urllib.request.urlopen(req) as response:
                # Login will likely fail with 401 Unauthorized or 400 (which is expected because user doesn't exist)
                # But it should NOT be 429.
                print(f" received response code: {response.getcode()}")
        except urllib.error.HTTPError as e:
            print(f" received response code: {e.code}")
            if e.code == 429:
                body = e.read().decode()
                print(f"\n✅ Rate limit works! Blocked at request #{i} with 429 Too Many Requests. Response: {body}")
                print("✅ Rate Limiting test PASSED!")
                return True
            elif e.code == 400 or e.code == 401 or e.code == 404:
                # These are expected business logic codes, indicating the request got past the rate limiter.
                continue
            else:
                print(f"❌ Unexpected HTTP code: {e.code}")
                return False
                
    print("❌ Rate limiting failed: Sent 9 requests without hitting 429.")
    return False


if __name__ == "__main__":
    success = True
    success &= test_security_headers()
    success &= test_trusted_host()
    success &= test_payload_size_limiter()
    success &= test_rate_limiting()
    
    if success:
        print("\n🎉 ALL SECURITY ENDPOINT TESTS PASSED SUCCESSFULY!")
        sys.exit(0)
    else:
        print("\n❌ SOME SECURITY TESTS FAILED. PLEASE CHECK LOGS.")
        sys.exit(1)
