#!/usr/bin/env python3
"""
Test client for Realistic Hindi Neural TTS Microservice.
Verifies health, Swara Neural Hindi & Hinglish audio, GET streaming, base64 synthesis, and voice catalog.
"""

import sys
import os
import argparse
import base64
import json
import urllib.request
import urllib.error


def make_http_request(url: str, method: str = "GET", data: dict = None, headers: dict = None, timeout: float = 30.0):
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
    print(f" Testing Realistic Hindi Neural TTS API: {base_url}")
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
        print("    [PASS] Health check successful.")
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
        star_voices = [v['name'] for v in voices if v.get('is_star')]
        print(f"    Star Hindi Voices: {star_voices}")
        assert len(voices) > 0, "Voice list should not be empty"
        print("    [PASS] Voices catalog retrieved successfully.")
    except Exception as e:
        print(f"    [FAIL] Voices catalog failed: {e}")
        return False

    # 3. POST /tts (Swara Neural Hindi Speech - MP3)
    print("\n[3] Testing POST /tts (Swara Neural Hindi Audio)...")
    hindi_text = "नमस्ते! आपका स्वागत है। आपका ऑर्डर सफलतापूर्वक कन्फर्म हो गया है।"
    try:
        status, headers, content = make_http_request(
            f"{base_url}/tts",
            method="POST",
            data={"text": hindi_text, "voice": "hi-IN-SwaraNeural"},
            headers=auth_headers,
        )
        print(f"    Status: {status}")
        print(f"    Content-Type: {headers.get('content-type')}")
        print(f"    Audio Size: {len(content)} bytes")
        assert status == 200, f"Expected 200, got {status}"
        assert len(content) > 1000, "Audio content too small"

        output_file = "test_swara_hindi_api.mp3"
        with open(output_file, "wb") as f:
            f.write(content)
        print(f"    [PASS] Saved realistic Hindi test audio to '{output_file}' ({len(content)} bytes).")
    except Exception as e:
        print(f"    [FAIL] /tts request failed: {e}")
        return False

    # 4. POST /tts (Hinglish with Madhur Male Voice)
    print("\n[4] Testing POST /tts (Madhur Neural Hinglish Audio)...")
    hinglish_text = "Namaste! Hamare customer support team aapko WhatsApp par jald connect karegi."
    try:
        status, headers, content = make_http_request(
            f"{base_url}/tts",
            method="POST",
            data={"text": hinglish_text, "voice": "hi-IN-MadhurNeural"},
            headers=auth_headers,
        )
        print(f"    Status: {status}")
        print(f"    Audio Size: {len(content)} bytes")
        assert status == 200, f"Expected 200, got {status}"
        assert len(content) > 1000, "Audio content too small"
        print("    [PASS] Hinglish speech generation with Madhur successful.")
    except Exception as e:
        print(f"    [FAIL] Hinglish request failed: {e}")
        return False

    # 5. GET /tts (Direct URL Streaming)
    print("\n[5] Testing GET /tts (Direct URL Streaming for WhatsApp / Web)...")
    try:
        encoded_q = urllib.parse.quote("Hello from Qloudflow WhatsApp Manager!")
        status, headers, content = make_http_request(f"{base_url}/tts?text={encoded_q}")
        print(f"    Status: {status}")
        print(f"    Content-Type: {headers.get('content-type')}")
        print(f"    Audio Size: {len(content)} bytes")
        assert status == 200, f"Expected 200, got {status}"
        print("    [PASS] GET /tts streaming successful.")
    except Exception as e:
        print(f"    [FAIL] GET /tts failed: {e}")
        return False

    # 6. POST /tts/base64 (JSON Base64 Audio)
    print("\n[6] Testing POST /tts/base64 (JSON Base64 Audio)...")
    try:
        status, headers, content = make_http_request(
            f"{base_url}/tts/base64",
            method="POST",
            data={"text": "Aapka transaction successful raha.", "voice": "hi-IN-SwaraNeural"},
            headers=auth_headers,
        )
        print(f"    Status: {status}")
        assert status == 200, f"Expected 200, got {status}"
        data = json.loads(content.decode("utf-8"))
        assert "audio_base64" in data, "Missing audio_base64 field in response"
        raw_audio = base64.b64decode(data["audio_base64"])
        print(f"    Decoded Audio Size: {len(raw_audio)} bytes")
        print(f"    Voice Returned: {data.get('voice')}")
        print("    [PASS] /tts/base64 request successful.")
    except Exception as e:
        print(f"    [FAIL] /tts/base64 request failed: {e}")
        return False

    # 7. Error Case: Empty Text
    print("\n[7] Testing POST /tts with empty text (Validation Test)...")
    try:
        status, headers, content = make_http_request(
            f"{base_url}/tts",
            method="POST",
            data={"text": "   "},
            headers=auth_headers,
        )
        print(f"    Status: {status} (Expected 400)")
        assert status == 400, f"Expected 400, got {status}"
        print("    [PASS] Correctly rejected empty text.")
    except Exception as e:
        print(f"    [FAIL] Validation test failed: {e}")

    print("\n==================================================")
    print(" ALL TESTS COMPLETED SUCCESSFULLY!")
    print("==================================================")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Realistic Hindi Neural TTS API endpoints.")
    parser.add_argument("--url", default="http://localhost:8000", help="Base API URL (e.g., http://localhost:8000)")
    parser.add_argument("--key", default="", help="Optional API key")
    args = parser.parse_args()

    test_api(args.url.rstrip("/"), args.key)

