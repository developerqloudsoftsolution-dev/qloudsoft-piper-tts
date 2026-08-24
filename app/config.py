import os
from pathlib import Path
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Application configuration loaded from environment variables."""

    # Default Voice model (Ultra-realistic Hindi & Hinglish Neural Voice: hi-IN-SwaraNeural)
    DEFAULT_VOICE: str = os.getenv("DEFAULT_VOICE", os.getenv("PIPER_MODEL", "hi-IN-SwaraNeural"))
    
    # Piper model for offline fallback
    PIPER_MODEL: str = os.getenv("PIPER_MODEL", "hi_IN-priyamvada-medium")

    # Directory where voice models (.onnx and .onnx.json) are stored
    MODEL_DIR: Path = Path(os.getenv("MODEL_DIR", str(Path(__file__).resolve().parent.parent / "models")))

    # Maximum allowed text length per request to prevent high latency & memory spikes
    MAX_TEXT_LENGTH: int = int(os.getenv("MAX_TEXT_LENGTH", "1000"))

    # Default voice speech rate (e.g. '+0%', '+10%', '-5%')
    DEFAULT_RATE: str = os.getenv("DEFAULT_RATE", "+0%")

    # Default voice pitch (e.g. '+0Hz', '+2Hz')
    DEFAULT_PITCH: str = os.getenv("DEFAULT_PITCH", "+0Hz")

    # Default output audio format ('mp3' or 'wav')
    DEFAULT_FORMAT: str = os.getenv("DEFAULT_FORMAT", "mp3")

    # Optional API key for Bearer token authentication (empty = open access)
    API_KEY: str = os.getenv("API_KEY", "").strip()

    # Server binding port (Render dynamically assigns $PORT)
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")

    # Logging level
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    @property
    def model_onnx_path(self) -> Path:
        """Returns the full path to the .onnx model file."""
        model_name = self.PIPER_MODEL
        if not model_name.endswith(".onnx"):
            model_name = f"{model_name}.onnx"
        return self.MODEL_DIR / model_name

    @property
    def model_config_path(self) -> Path:
        """Returns the full path to the .onnx.json config file."""
        model_name = self.PIPER_MODEL
        if model_name.endswith(".onnx"):
            config_name = f"{model_name}.json"
        else:
            config_name = f"{model_name}.onnx.json"
        return self.MODEL_DIR / config_name


settings = Settings()
