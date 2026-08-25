import io
import re
import wave
import base64
import logging
import asyncio
import gc
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

from app.config import settings

logger = logging.getLogger("tts_service")

# PyTorch & Transformers for Meta MMS-TTS Hindi VITS
try:
    import torch
    from transformers import VitsModel, AutoTokenizer
    import numpy as np
    MMS_AVAILABLE = True
except ImportError as e:
    MMS_AVAILABLE = False
    logger.warning(f"MMS-TTS dependencies not available: {e}")

# Edge-TTS for Studio-Grade Uplifting Female Neural Voices
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logger.warning("edge-tts package is not installed.")


# Curated catalog: 100% Uplifting, Gen-Z, and Youthful Female Voices ONLY
VOICE_METADATA: Dict[str, Dict[str, Any]] = {
    "hi-IN-SwaraNeural": {
        "id": "hi-IN-SwaraNeural",
        "name": "Swara (Uplifting Gen-Z Hindi HD)",
        "language": "Hindi / Hinglish",
        "locale": "hi_IN",
        "gender": "Female",
        "quality": "Neural HD (Star Female)",
        "flag": "🇮🇳",
        "engine": "neural_azure",
        "is_star": True,
        "is_default": True,
        "description": "Ultra-realistic, youthful, and energetic Gen-Z Indian Hindi & Hinglish female voice with lively natural inflection."
    },
    "en-IN-NeerjaNeural": {
        "id": "en-IN-NeerjaNeural",
        "name": "Neerja (Cheerful Hinglish & English)",
        "language": "Indian English / Hinglish",
        "locale": "en_IN",
        "gender": "Female",
        "quality": "Neural HD (Upbeat Female)",
        "flag": "🇮🇳",
        "engine": "neural_azure",
        "is_star": True,
        "is_default": False,
        "description": "Vibrant, cheerful, and uplifting Indian female voice with modern conversational cadence."
    },
    "mms-uplifting-female": {
        "id": "mms-uplifting-female",
        "name": "Meta MMS Uplifting Hindi (VITS)",
        "language": "Hindi (हिंदी)",
        "locale": "hi_IN",
        "gender": "Female",
        "quality": "MMS VITS (1.2x Fast & Lively)",
        "flag": "🇮🇳",
        "engine": "meta_mms",
        "is_star": False,
        "is_default": False,
        "description": "Meta MMS Hindi neural model tuned with a 1.2x fast, upbeat tempo and expressive female prosody."
    },
    "mr-IN-AarohiNeural": {
        "id": "mr-IN-AarohiNeural",
        "name": "Aarohi (Cheerful Marathi Female)",
        "language": "Marathi",
        "locale": "mr_IN",
        "gender": "Female",
        "quality": "Neural HD",
        "flag": "🇮🇳",
        "engine": "neural_azure",
        "is_star": False,
        "is_default": False,
        "description": "Sweet, bright, and cheerful Marathi female voice."
    },
    "gu-IN-DhwaniNeural": {
        "id": "gu-IN-DhwaniNeural",
        "name": "Dhwani (Lively Gujarati Female)",
        "language": "Gujarati",
        "locale": "gu_IN",
        "gender": "Female",
        "quality": "Neural HD",
        "flag": "🇮🇳",
        "engine": "neural_azure",
        "is_star": False,
        "is_default": False,
        "description": "Bright and lively Gujarati female neural voice."
    },
    "bn-IN-TanishaaNeural": {
        "id": "bn-IN-TanishaaNeural",
        "name": "Tanishaa (Sweet Bengali Female)",
        "language": "Bengali",
        "locale": "bn_IN",
        "gender": "Female",
        "quality": "Neural HD",
        "flag": "🇮🇳",
        "engine": "neural_azure",
        "is_star": False,
        "is_default": False,
        "description": "Sweet, expressive, and melodic Bengali female neural voice."
    }
}


def clean_speech_text(text: str) -> str:
    """
    Cleans and normalizes text for optimal TTS pronunciation:
    - Removes markdown formatting (*bold*, _italic_, ~strike~, `code`, #, >)
    - Removes bullet points and formatting artifacts
    - Replaces URLs with 'link'
    - Normalizes whitespace
    """
    if not text:
        return ""
    t = re.sub(r'[*_~`#>]', '', text)
    t = re.sub(r'^\s*[-•*]\s+', '', t, flags=re.MULTILINE)
    t = re.sub(r'https?://\S+', 'link', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


class TTSService:
    """
    Unified High-Fidelity Uplifting Female TTS Service.
    Loads models once at startup. Zero fallback.
    """

    _instance: Optional["TTSService"] = None

    def __init__(self):
        self._default_voice: str = "hi-IN-SwaraNeural"
        self._mms_model_id: str = settings.MMS_MODEL_ID
        self._mms_model: Optional[Any] = None
        self._mms_tokenizer: Optional[Any] = None
        self._sampling_rate: int = 16000
        self._is_loaded: bool = False
        self._load_error: Optional[str] = None
        self._lock = asyncio.Lock()

        # Load Meta MMS model into memory once at startup
        self._load_mms_model()

    @classmethod
    def get_instance(cls) -> "TTSService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded or EDGE_TTS_AVAILABLE

    @property
    def default_voice(self) -> str:
        return self._default_voice

    @property
    def sample_rate(self) -> int:
        return self._sampling_rate

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def _load_mms_model(self) -> None:
        """Loads Meta MMS VITS model once into memory."""
        if not MMS_AVAILABLE:
            self._load_error = "PyTorch/Transformers not installed."
            return

        try:
            logger.info(f"Loading Meta MMS-TTS Hindi model from '{self._mms_model_id}'...")
            if hasattr(torch, "set_num_threads"):
                torch.set_num_threads(2)

            self._mms_tokenizer = AutoTokenizer.from_pretrained(self._mms_model_id)
            self._mms_model = VitsModel.from_pretrained(self._mms_model_id)
            self._mms_model.eval()

            if hasattr(self._mms_model.config, "sampling_rate"):
                self._sampling_rate = int(self._mms_model.config.sampling_rate)

            self._is_loaded = True
            logger.info(f"Meta MMS Hindi TTS loaded successfully ({self._sampling_rate} Hz).")
        except Exception as e:
            self._is_loaded = False
            self._load_error = str(e)
            logger.error(f"Failed to load MMS-TTS model: {e}", exc_info=True)

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Returns catalog of available uplifting female voices."""
        voice_list = []
        for voice_id, meta in VOICE_METADATA.items():
            voice_list.append({
                "id": voice_id,
                "name": meta["name"],
                "language": meta["language"],
                "locale": meta["locale"],
                "gender": meta["gender"],
                "quality": meta["quality"],
                "flag": meta["flag"],
                "engine": meta["engine"],
                "is_star": meta.get("is_star", False),
                "is_default": voice_id == self._default_voice or meta.get("is_default", False),
                "description": meta["description"]
            })
        return voice_list

    def _synthesize_mms_sync(self, text: str, speaking_rate: float = 1.2) -> bytes:
        """Synchronous CPU inference for Meta MMS Hindi VITS model."""
        if not self._is_loaded or self._mms_model is None or self._mms_tokenizer is None:
            raise RuntimeError(f"Meta MMS Hindi model not loaded: {self._load_error}")

        inputs = self._mms_tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            output = self._mms_model(**inputs, speaking_rate=speaking_rate).waveform

        waveform = output.squeeze().cpu().numpy()
        del inputs, output

        pcm_int16 = (np.clip(waveform, -1.0, 1.0) * 32767).astype(np.int16)
        del waveform

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self._sampling_rate)
            wf.writeframes(pcm_int16.tobytes())

        wav_bytes = wav_buffer.getvalue()
        del pcm_int16, wav_buffer
        gc.collect()
        return wav_bytes

    async def _synthesize_edge_tts(
        self,
        text: str,
        voice: str,
        rate: Optional[str] = None,
        pitch: Optional[str] = None
    ) -> bytes:
        """Synthesizes high-definition uplifting female voice using Microsoft Azure Neural via Edge-TTS."""
        if not EDGE_TTS_AVAILABLE:
            raise RuntimeError("edge-tts is not available.")

        rate_str = rate or "+0%"
        pitch_str = pitch or "+0Hz"

        target_voice = voice
        # If an English voice (en-IN) receives Devanagari Hindi characters, route to Swara Hindi female
        has_devanagari = any('\u0900' <= ch <= '\u097f' for ch in text)
        if 'en-IN' in target_voice and has_devanagari:
            target_voice = 'hi-IN-SwaraNeural'

        communicate = edge_tts.Communicate(
            text=text,
            voice=target_voice,
            rate=rate_str,
            pitch=pitch_str
        )

        audio_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])

        audio_bytes = audio_buffer.getvalue()
        if not audio_bytes:
            raise RuntimeError("Edge-TTS generated 0 bytes.")
        return audio_bytes

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
        output_format: Optional[str] = None
    ) -> Tuple[bytes, str]:
        """
        Direct neural speech synthesis (Zero Fallback).
        """
        clean_text = clean_speech_text(text)
        if not clean_text:
            raise ValueError("Input text cannot be empty.")

        target_voice = voice or self._default_voice

        # Check if target is Meta MMS model
        if target_voice in ("facebook/mms-tts-hin", "mms-hin", "mms-uplifting-female", "mms-genz-female"):
            speed = 1.25  # Upbeat, lively Gen-Z pace
            if rate:
                m = re.search(r'([+-]?\d+)', str(rate))
                if m:
                    speed *= (1.0 + float(m.group(1)) / 100.0)

            async with self._lock:
                wav_bytes = await asyncio.to_thread(self._synthesize_mms_sync, clean_text, speed)
            return wav_bytes, "audio/wav"

        # Direct synthesis using Studio-Grade Neural Female Voice
        audio_bytes = await self._synthesize_edge_tts(
            text=clean_text,
            voice=target_voice,
            rate=rate,
            pitch=pitch
        )
        return audio_bytes, "audio/mpeg"

    async def synthesize_base64(
        self,
        text: str,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        pitch: Optional[str] = None,
        output_format: Optional[str] = None
    ) -> Tuple[str, str]:
        audio_bytes, mime_type = await self.synthesize(
            text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            output_format=output_format
        )
        b64_str = base64.b64encode(audio_bytes).decode("utf-8")
        fmt = "mp3" if "mpeg" in mime_type else "wav"
        return b64_str, fmt


def get_tts_service() -> TTSService:
    return TTSService.get_instance()
