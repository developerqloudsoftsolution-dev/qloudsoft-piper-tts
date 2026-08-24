#!/usr/bin/env python3
"""
Model download utility for Piper TTS.
Downloads .onnx and .onnx.json voice models from the official Hugging Face repository.
"""

import sys
import os
import argparse
import urllib.request
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("download_model")

HF_BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

# Pre-defined known voice paths for instant reliable resolution
KNOWN_VOICES = {
    # Lightweight Female Voices (Great for Voice Agents & Render Free Tier)
    "en_US-amy-low": "en/en_US/amy/low",
    "en_US-amy-medium": "en/en_US/amy/medium",
    "en_US-lessac-low": "en/en_US/lessac/low",
    "en_US-lessac-medium": "en/en_US/lessac/medium",
    "en_US-hfc_female-medium": "en/en_US/hfc_female/medium",
    "en_GB-jenny_dioco-medium": "en/en_GB/jenny_dioco/medium",
    "en_GB-alba-medium": "en/en_GB/alba/medium",
    # Male / General Voices
    "en_US-ryan-low": "en/en_US/ryan/low",
    "en_US-ryan-medium": "en/en_US/ryan/medium",
    "en_US-danny-low": "en/en_US/danny/low",
}


def resolve_voice_url_path(voice_name: str) -> str:
    """
    Resolves the relative Hugging Face repository path from a voice name.
    Example: 'en_US-amy-low' -> 'en/en_US/amy/low'
    """
    clean_name = voice_name.replace(".onnx", "").replace(".json", "")
    
    if clean_name in KNOWN_VOICES:
        return KNOWN_VOICES[clean_name]

    # Heuristic resolution for format: {lang_code}_{country}-{name}-{quality}
    # Example: en_US-kathleen-low -> lang=en, locale=en_US, name=kathleen, quality=low
    try:
        parts = clean_name.split("-")
        locale = parts[0]                  # e.g., 'en_US'
        lang = locale.split("_")[0]        # e.g., 'en'
        voice = parts[1]                   # e.g., 'amy'
        quality = parts[2] if len(parts) > 2 else "medium" # e.g., 'low'
        return f"{lang}/{locale}/{voice}/{quality}"
    except Exception as e:
        logger.warning(f"Could not parse voice format for '{voice_name}': {e}. Using flat structure.")
        return f"en/en_US/{clean_name}/low"


def download_file(url: str, destination: Path) -> bool:
    """Downloads a file from a URL to destination if not already present."""
    if destination.exists() and destination.stat().st_size > 0:
        logger.info(f"File already exists: {destination.name} ({destination.stat().st_size / (1024*1024):.2f} MB)")
        return True

    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_dest = destination.with_suffix(destination.suffix + ".tmp")

    logger.info(f"Downloading {url} -> {destination}")
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Render/Linux) PiperTTSDownloader/1.0"}
        )
        with urllib.request.urlopen(req, timeout=60) as response, open(temp_dest, "wb") as out_file:
            # Stream download to avoid loading entire model into RAM
            chunk_size = 1024 * 1024  # 1MB chunks
            total_size = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    logger.debug(f"Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)")

        temp_dest.rename(destination)
        size_mb = destination.stat().st_size / (1024 * 1024)
        logger.info(f"Successfully downloaded {destination.name} ({size_mb:.2f} MB)")
        return True
    except Exception as e:
        if temp_dest.exists():
            temp_dest.unlink()
        logger.error(f"Failed to download {url}: {e}")
        return False


def ensure_model_files(model_name: str, models_dir: Path) -> tuple[Path, Path]:
    """
    Ensures that both the .onnx model and .onnx.json config files exist locally.
    Downloads them if missing.
    Returns (onnx_path, config_path).
    """
    clean_name = model_name.replace(".onnx", "").replace(".json", "")
    onnx_file = models_dir / f"{clean_name}.onnx"
    json_file = models_dir / f"{clean_name}.onnx.json"

    if onnx_file.exists() and json_file.exists() and onnx_file.stat().st_size > 0 and json_file.stat().st_size > 0:
        logger.info(f"Voice model '{clean_name}' is verified locally in {models_dir}")
        return onnx_file, json_file

    url_path = resolve_voice_url_path(clean_name)
    onnx_url = f"{HF_BASE_URL}/{url_path}/{clean_name}.onnx"
    json_url = f"{HF_BASE_URL}/{url_path}/{clean_name}.onnx.json"

    logger.info(f"Downloading model '{clean_name}' from Hugging Face...")
    onnx_ok = download_file(onnx_url, onnx_file)
    json_ok = download_file(json_url, json_file)

    if not onnx_ok or not json_ok:
        raise RuntimeError(
            f"Failed to download voice model files for '{clean_name}'. "
            f"Please check your internet connection or verify the model name. "
            f"URLs tried: {onnx_url}, {json_url}"
        )

    return onnx_file, json_file


def main():
    parser = argparse.ArgumentParser(description="Download Piper TTS voice model and config from Hugging Face.")
    parser.add_argument(
        "model",
        nargs="?",
        default=os.getenv("PIPER_MODEL", "en_US-amy-low"),
        help="Voice model name (e.g. en_US-amy-low, en_US-lessac-low, en_US-amy-medium)"
    )
    parser.add_argument(
        "--dir",
        default=os.getenv("MODEL_DIR", str(Path(__file__).resolve().parent / "models")),
        help="Target directory for downloaded models"
    )
    args = parser.parse_args()

    models_dir = Path(args.dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Ensuring model '{args.model}' in '{models_dir}'...")
    try:
        onnx_path, config_path = ensure_model_files(args.model, models_dir)
        logger.info(f"Ready: ONNX={onnx_path}, Config={config_path}")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
