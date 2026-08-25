#!/usr/bin/env python3
"""
Test client for Meta MMS-TTS Hindi Microservice.
Verifies health, facebook/mms-tts-hin WAV audio generation, GET streaming, base64 synthesis, and voice catalog.
"""

import sys
import os
import argparse
import base64
import json
import urllib.request
import urllib.error


def make_http_request(url: str, method: str = "GET", data: dict = None, headers: dict = None, timeout: float = 60.0):
    """Helper to perform HTTP requests using Python standard library (urllib)."""
    headers = headers.copy() if headers else {}
    body_bytes = None
    if data is not None:
        body_bytes = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            response_headers = {k.lower(): v for k, v in response.headers.items()}
            content = response.read()
            return status_code, response_headers, content
    except urllib.error.HTTPError as e:
        status_code = e.code
        response_headers = {k.lower(): v for k, v in e.headers.items()}
        content = e.read()
        return status_code, response_headers, content
    except Exception as e:
        raise e


def test_api(base_url: str, api_key: str = ""):
    print(f"==================================================")
    print(f" Testing Meta MMS-TTS Hindi API: {base_url}")
    print(f" Auth Header: {'Bearer ' + api_key if api_key else 'None'}")
    print(f"==================================================")

    auth_headers = {}
    if api_key:
        auth_headers["Authorization"] = f"Bearer {api_key}"

    # 1. Health Check
    print("\n[1] Testing GET /health...")
    try:
        status, headers, content = make_http_request(f"{base_url}/health")
        text = content.decode("utf-8", errors="replace")
        print(f"    Status: {status}")
        print(f"    Response: {text}")
        assert status == 200, f"Expected 200, got {status}"
        data = json.loads(text)
        assert data.get("engine") == "mms-tts-hin", "Expected engine mms-tts-hin"
        print("    [PASS] Health check successful. Meta MMS Hindi engine active.")
    except Exception as e:
        print(f"    [FAIL] Health check failed: {e}")
        return False

    # 2. Voices Catalog
    print("\n[2] Testing GET /voices...")
    try:
        status, headers, content = make_http_request(f"{base_url}/voices")
        assert status == 200, f"Expected 200, got {status}"
        voices = json.loads(content.decode("utf-8"))
        print(f"    Total Available Voices: {len(voices)}")
        print(f"    Models: {[v['id'] for v in voices]}")
        assert len(voices) > 0, "Voice list should not be empty"
        print("    [PASS] Voices catalog retrieved successfully.")
    except Exception as e:
        print(f"    [FAIL] Voices catalog failed: {e}")
        return False

    # 3. POST /tts (Meta MMS Hindi Speech - WAV)
    print("\n[3] Testing POST /tts (Meta MMS Hindi Audio - 'नमस्ते, आप कैसे हैं?')...")
    hindi_text = "नमस्ते, आप कैसे हैं?"
    try:
        status, headers, content = make_http_request(
            f"{base_url}/tts",
            method="POST",
            data={"text": hindi_text, "voice": "facebook/mms-tts-hin", "format": "wav"},
            headers=auth_headers,
        )
        print(f"    Status: {status}")
        print(f"    Content-Type: {headers.get('content-type')}")
        print(f"    Audio Size: {len(content)} bytes")
        assert status == 200, f"Expected 200, got {status}"
        assert len(content) > 1000, "Audio content too small"

        output_file = "test_mms_hindi_api.wav"
        with open(output_file, "wb") as f:
            f.write(content)
        print(f"    [PASS] Saved Meta MMS Hindi test audio to '{output_file}' ({len(content)} bytes).")
    except Exception as e:
        print(f"    [FAIL] /tts request failed: {e}")
        return False

    # 4. GET /tts (Streaming Audio for HTML5 / Web Audio)
    print("\n[4] Testing GET /tts (Streaming Endpoint)...")
    try:
        query_text = urllib.parse.quote("नमस्ते! आपका स्वागत है।")
        status, headers, content = make_http_request(
            f"{base_url}/tts?text={query_text}&format=wav",
            method="GET",
            headers=auth_headers,
        )
        print(f"    Status: {status}")
        print(f"    Content-Type: {headers.get('content-type')}")
        print(f"    Audio Size: {len(content)} bytes")
        assert status == 200, f"Expected 200, got {status}"
        assert len(content) > 1000, "Streaming audio content too small"
        print("    [PASS] Direct GET streaming endpoint verified.")
    except Exception as e:
        print(f"    [FAIL] GET /tts streaming failed: {e}")
        return False

    # 5. POST /tts/base64
    print("\n[5] Testing POST /tts/base64...")
    try:
        status, headers, content = make_http_request(
            f"{base_url}/tts/base64",
            method="POST",
            data={"text": "क्लाउडसॉफ्ट सॉल्यूशंस में आपका स्वागत है।"},
            headers=auth_headers,
        )
        print(f"    Status: {status}")
        assert status == 200, f"Expected 200, got {status}"
        resp_json = json.loads(content.decode("utf-8"))
        assert "audio_base64" in resp_json, "Response missing audio_base64 key"
        decoded = base64.b64decode(resp_json["audio_base64"])
        print(f"    Decoded Audio Size: {len(decoded)} bytes")
        assert len(decoded) > 1000, "Decoded base64 audio too small"
        print("    [PASS] POST /tts/base64 verified.")
    except Exception as e:
        print(f"    [FAIL] POST /tts/base64 failed: {e}")
        return False

    print("\n==================================================")
    print(" ALL TESTS PASSED! Meta MMS-TTS Hindi is Production Ready.")
    print("==================================================")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test client for Meta MMS-TTS Hindi Microservice")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Base URL of the TTS API (default: http://127.0.0.1:8000)")
    parser.add_argument("--api-key", default="", help="Optional API key for Bearer auth")
    args = parser.parse_args()

    success = test_api(args.url, args.api_key)
    sys.exit(0 if success else 1)
