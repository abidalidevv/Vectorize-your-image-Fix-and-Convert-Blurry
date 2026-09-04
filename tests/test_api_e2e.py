"""
End-to-End API Test for VectorForge AI
Tests full pipeline via HTTP API:
upload -> analyze -> preprocess -> quantize -> vectorize -> export (SVG & PNG)
"""
import json
import urllib.request
import urllib.parse
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
SAMPLE_PATH = Path("samples/test_logo.png").resolve()


def test_api():
    print("1. Testing /health...")
    req = urllib.request.urlopen(f"{BASE_URL}/health")
    health = json.loads(req.read())
    assert health["status"] == "ok"
    print("   Health OK:", health)

    print("\n2. Testing /api/upload...")
    boundary = "----WebKitFormBoundaryVectorForge7MA4YWxkTrZu0gW"
    filename = SAMPLE_PATH.name
    file_bytes = SAMPLE_PATH.read_bytes()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode("latin-1") + file_bytes + f"\r\n--{boundary}--\r\n".encode("latin-1")

    req = urllib.request.Request(
        f"{BASE_URL}/api/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    resp = urllib.request.urlopen(req)
    upload_res = json.loads(resp.read())
    session_id = upload_res["session_id"]
    print("   Upload OK. Session ID:", session_id)
    print("   Image info:", upload_res["width"], "x", upload_res["height"], upload_res["format"])

    print("\n3. Testing /api/analyze...")
    data = json.dumps({"session_id": session_id}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/analyze",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req)
    analyze_res = json.loads(resp.read())
    print("   Analyze OK. Mode:", analyze_res["recommended_mode"], "Confidence:", analyze_res["confidence"])

    print("\n4. Testing /api/quantize...")
    data = json.dumps({
        "session_id": session_id,
        "num_colors": 8,
        "method": "kmeans",
        "dither": False
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/quantize",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req)
    quantize_res = json.loads(resp.read())
    print("   Quantize OK. Palette colors:", len(quantize_res["palette"]))

    print("\n5. Testing /api/vectorize...")
    data = json.dumps({
        "session_id": session_id,
        "quality_preset": "balanced",
        "curve_fitting": "spline",
        "engine": "auto"
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/vectorize",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req)
    vectorize_res = json.loads(resp.read())
    print("   Vectorize OK. Engine used:", vectorize_res["engine_used"])
    stats = vectorize_res["stats"]
    print("   Paths:", stats["path_count"], "Colors:", stats["color_count"], "Raster:", stats["contains_raster"])
    assert stats["path_count"] > 0, "Must have vector paths"
    assert not stats["contains_raster"], "Must NOT contain embedded raster"

    print("\n6. Testing /api/export/svg...")
    data = json.dumps({
        "session_id": session_id,
        "optimize": True,
        "precision": 3
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/export/svg",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req)
    svg_bytes = resp.read()
    content_type = resp.headers.get("Content-Type", "")
    assert "svg" in content_type, f"Expected SVG content type, got {content_type}"
    assert b"<svg" in svg_bytes, "Expected <svg tag in exported SVG"
    print(f"   Export SVG OK! Size: {len(svg_bytes)} bytes, Content-Type: {content_type}")

    print("\n7. Testing /api/export/png...")
    data = json.dumps({
        "session_id": session_id,
        "scale": 2,
        "dpi": 96
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/export/png",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    resp = urllib.request.urlopen(req)
    png_bytes = resp.read()
    content_type = resp.headers.get("Content-Type", "")
    assert "png" in content_type, f"Expected PNG content type, got {content_type}"
    # Magic bytes for PNG: 89 50 4E 47
    assert png_bytes.startswith(b"\x89PNG"), "Expected PNG magic bytes"
    print(f"   Export PNG OK! Size: {len(png_bytes)} bytes, Content-Type: {content_type}")

    print("\n=== ALL E2E API TESTS PASSED! ===")


if __name__ == "__main__":
    test_api()
