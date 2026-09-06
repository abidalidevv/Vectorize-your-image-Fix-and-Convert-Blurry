import os
import sys
import time
import urllib.request

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

dest = os.path.expanduser("~/.cache/lama/lama_fp32.onnx")
os.makedirs(os.path.dirname(dest), exist_ok=True)
url = "https://huggingface.co/Carve/LaMa-ONNX/resolve/main/lama_fp32.onnx"

print(f"Downloading LaMa model from {url} to {dest}...")
for attempt in range(1, 6):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(dest, "wb") as f:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            t0 = time.time()
            while True:
                chunk = resp.read(2 * 1024 * 1024)  # 2MB chunks
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if downloaded % (20 * 1024 * 1024) < 2 * 1024 * 1024:
                    mb = round(downloaded / (1024 * 1024), 1)
                    tot_mb = round(total / (1024 * 1024), 1)
                    pct = int(downloaded / total * 100) if total else 0
                    print(f"LaMa progress: {mb}MB / {tot_mb}MB ({pct}%)")
        size_mb = round(os.path.getsize(dest) / (1024 * 1024), 1)
        print(f"[SUCCESS] LaMa downloaded cleanly! Total size: {size_mb} MB")
        break
    except Exception as e:
        print(f"Attempt {attempt} failed: {e}. Retrying in 3s...")
        time.sleep(3)
