#!/usr/bin/env python3
"""
VectorForge AI — Pro Models Pre-Download Helper Script

This script pre-downloads the heavier Pro-tier AI model weights offline to prevent
blocking live HTTP requests:
1. BiRefNet Ultra (~972MB): High-fidelity background removal with hair & edge matting.
2. Real-ESRGAN Ultra (~4.8MB): AI Super-resolution upscaling (realesr-general-x4v3 ONNX).

Usage:
    python scripts/download_pro_models.py            # Download both models
    python scripts/download_pro_models.py --birefnet # Download BiRefNet only
    python scripts/download_pro_models.py --realesrgan # Download Real-ESRGAN only
"""
import sys
import time
import argparse
from pathlib import Path
import urllib.request
import requests


def download_realesrgan():
    url = "https://huggingface.co/Heliosoph/realesrgan-onnx/resolve/main/realesr-general-x4v3.onnx"
    target_dir = Path.home() / ".cache" / "realesrgan"
    target_file = target_dir / "realesr-general-x4v3.onnx"

    print("=======================================================")
    print("1. Real-ESRGAN Ultra Model (realesr-general-x4v3.onnx)")
    print("=======================================================")

    if target_file.exists() and target_file.stat().st_size > 1_000_000:
        print(f"[OK] Real-ESRGAN model is already cached at:\n  {target_file} ({target_file.stat().st_size / 1e6:.1f} MB)\n")
        return True

    print(f"Downloading Real-ESRGAN weights (~4.8MB) to:\n  {target_file} ...")
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, str(target_file))
        print(f"[OK] Real-ESRGAN model successfully downloaded! ({target_file.stat().st_size / 1e6:.1f} MB)\n")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to download Real-ESRGAN weights: {e}\n")
        return False


def _download_file_resumable(url: str, target_file: Path, expected_size: int = 0, max_retries: int = 15) -> bool:
    """Download a large file with automatic HTTP Range resume and retry support."""
    target_dir = target_file.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    part_file = target_file.with_name(f"{target_file.name}.part")

    chunk_size = 1024 * 1024  # 1 MB chunks

    for attempt in range(1, max_retries + 1):
        try:
            downloaded = part_file.stat().st_size if part_file.exists() else 0

            headers = {}
            if downloaded > 0:
                headers["Range"] = f"bytes={downloaded}-"
                print(f"[Attempt {attempt}] Resuming download from {downloaded / 1e6:.1f} MB...")
            else:
                print(f"[Attempt {attempt}] Starting fresh download...")

            with requests.get(url, headers=headers, stream=True, timeout=(20, 60), allow_redirects=True) as resp:
                if resp.status_code not in (200, 206):
                    print(f"Server returned HTTP {resp.status_code}. Retrying in 5s...")
                    time.sleep(5)
                    continue

                total_size = expected_size
                content_range = resp.headers.get("Content-Range")
                if content_range:
                    # Format: bytes start-end/total
                    try:
                        total_size = int(content_range.split("/")[-1])
                    except Exception:
                        pass
                elif resp.headers.get("Content-Length"):
                    total_size = downloaded + int(resp.headers.get("Content-Length"))

                mode = "ab" if (resp.status_code == 206 and downloaded > 0) else "wb"
                if mode == "wb":
                    downloaded = 0

                last_print = downloaded
                with open(part_file, mode) as f:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            # Print progress every ~50 MB
                            if downloaded - last_print >= 50 * 1024 * 1024 or (total_size and downloaded >= total_size):
                                if total_size:
                                    pct = (downloaded / total_size) * 100
                                    print(f"  Progress: {downloaded / 1e6:.1f} / {total_size / 1e6:.1f} MB ({pct:.1f}%)")
                                else:
                                    print(f"  Progress: {downloaded / 1e6:.1f} MB")
                                last_print = downloaded

            if total_size and downloaded < total_size:
                print(f"Partial stream ended ({downloaded}/{total_size} bytes). Reconnecting...")
                time.sleep(2)
                continue

            # Complete! Rename part file to final file
            if target_file.exists():
                target_file.unlink()
            part_file.rename(target_file)
            print(f"[OK] Download finished: {target_file.stat().st_size / 1e6:.1f} MB")
            return True

        except (requests.RequestException, IOError) as e:
            print(f"[Attempt {attempt}] Connection issue: {e}. Retrying in 3s...")
            time.sleep(3)

    return False


def download_birefnet():
    print("=======================================================")
    print("2. BiRefNet Ultra Model (birefnet-general.onnx)")
    print("=======================================================")

    target_dir = Path.home() / ".rembg" / "models" / "birefnet-general"
    target_file = target_dir / "birefnet-general.onnx"
    legacy_file = Path.home() / ".u2net" / "birefnet-general.onnx"

    for p in [target_file, legacy_file]:
        if p.exists() and p.stat().st_size > 500_000_000:
            print(f"[OK] BiRefNet model is already cached at:\n  {p} ({p.stat().st_size / 1e6:.1f} MB)\n")
            return True

    birefnet_url = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-epoch_244.onnx"
    print(f"Downloading BiRefNet Ultra weights (~972MB) to:\n  {target_file}")
    print("Automatic resume and retry is enabled for network stability.")

    ok = _download_file_resumable(birefnet_url, target_file, expected_size=972666916)
    if not ok:
        print("[ERROR] Could not complete BiRefNet download after multiple retries.\n")
        return False

    print("Verifying BiRefNet model with rembg session loader...")
    try:
        from rembg import new_session
        session = new_session("birefnet-general")
        print("[OK] BiRefNet Ultra model session loaded successfully!\n")
        return True
    except Exception as e:
        print(f"[WARNING] Model downloaded, but rembg session validation gave: {e}\n")
        return True


def download_isnet():
    print("=======================================================")
    print("3. ISNet Fast Tier Model (isnet-general-use.onnx)")
    print("=======================================================")

    target_dir = Path.home() / ".rembg" / "models" / "isnet-general-use"
    target_file = target_dir / "isnet-general-use.onnx"
    legacy_file = Path.home() / ".u2net" / "isnet-general-use.onnx"

    for p in [target_file, legacy_file]:
        if p.exists() and p.stat().st_size > 100_000_000:
            print(f"[OK] ISNet model is already cached at:\n  {p} ({p.stat().st_size / 1e6:.1f} MB)\n")
            return True

    isnet_url = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-general-use.onnx"
    print(f"Downloading ISNet Fast weights (~178.6MB) to:\n  {target_file}")

    ok = _download_file_resumable(isnet_url, target_file, expected_size=178648008)
    if not ok:
        print("[ERROR] Could not complete ISNet download after multiple retries.\n")
        return False

    # Clean up any stale tmp files left from previous interrupted downloads
    if target_dir.exists():
        for tmp_file in target_dir.glob("tmp*"):
            try:
                tmp_file.unlink()
            except Exception:
                pass

    print("Verifying ISNet model with rembg session loader...")
    try:
        from rembg import new_session
        session = new_session("isnet-general-use")
        print("[OK] ISNet model session loaded successfully!\n")
        return True
    except Exception as e:
        print(f"[WARNING] Model downloaded, but session validation gave: {e}\n")
        return True


def download_realesrgan_plus():
    print("=======================================================")
    print("4. Real-ESRGAN Ultra (RealESRGAN_x4plus.onnx, ~67MB)")
    print("=======================================================")

    target_dir = Path.home() / ".cache" / "realesrgan"
    target_file = target_dir / "RealESRGAN_x4plus.onnx"

    if target_file.exists() and target_file.stat().st_size > 60_000_000:
        print(f"[OK] RealESRGAN_x4plus model is already cached at:\n  {target_file} ({target_file.stat().st_size / 1e6:.1f} MB)\n")
        return True

    url = "https://huggingface.co/anakhiu/realesrgan-onnx/resolve/main/realesrgan_x4plus.onnx"
    print(f"Downloading RealESRGAN_x4plus Ultra weights (~67MB) to:\n  {target_file}")

    # If partial un-parted file exists, rename to part to resume
    part_file = target_file.with_name(f"{target_file.name}.part")
    if target_file.exists() and target_file.stat().st_size < 60_000_000 and not part_file.exists():
        target_file.rename(part_file)

    ok = _download_file_resumable(url, target_file, expected_size=67051616)
    if not ok:
        print("[ERROR] Could not complete RealESRGAN_x4plus download after multiple retries.\n")
        return False

    print("Verifying RealESRGAN_x4plus model with ONNX Runtime...")
    try:
        import onnxruntime as ort
        sess = ort.InferenceSession(str(target_file), providers=['CPUExecutionProvider'])
        print(f"[OK] RealESRGAN_x4plus Ultra model session loaded successfully! ({target_file.stat().st_size / 1e6:.1f} MB)\n")
        return True
    except Exception as e:
        print(f"[WARNING] Model downloaded, but ONNX session validation gave: {e}\n")
        return True


def main():
    parser = argparse.ArgumentParser(description="Pre-download VectorForge AI models.")
    parser.add_argument("--birefnet", action="store_true", help="Download BiRefNet Ultra model (~972MB)")
    parser.add_argument("--realesrgan", action="store_true", help="Download Real-ESRGAN Fast model (realesr-general-x4v3, ~4.8MB)")
    parser.add_argument("--realesrgan-plus", action="store_true", help="Download RealESRGAN_x4plus Ultra model (~67MB)")
    parser.add_argument("--isnet", action="store_true", help="Download ISNet Fast model (~178.6MB)")
    parser.add_argument("--all", action="store_true", help="Download all models")
    args = parser.parse_args()

    download_all = args.all or not (args.birefnet or args.realesrgan or args.realesrgan_plus or args.isnet)

    success = True
    if download_all or args.realesrgan:
        if not download_realesrgan():
            success = False

    if download_all or args.realesrgan_plus:
        if not download_realesrgan_plus():
            success = False

    if download_all or args.birefnet:
        if not download_birefnet():
            success = False

    if download_all or args.isnet:
        if not download_isnet():
            success = False

    if success:
        print("All requested models are ready for offline inference.")
    else:
        print("Some downloads were skipped or failed. Offline graceful fallbacks will remain active during live requests.")


if __name__ == "__main__":
    main()


