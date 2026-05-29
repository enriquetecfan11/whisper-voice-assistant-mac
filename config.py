import os
from dotenv import load_dotenv

load_dotenv()

# =======================
# CONFIGURACION DE WHISPER
# =======================
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # tiny, base, small, medium, large
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "es")  # es, en, etc.
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")  # cpu o cuda
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")  # int8, float16, float32

# =======================
# CONFIGURACION DE AUDIO
# =======================
AUDIO_SAMPLE_RATE = 16000  # Hz requerido por Whisper
AUDIO_CHANNELS = 1
AUDIO_CHUNK_DURATION = 5  # segundos por chunk de transcripcion

# =======================
# DIRECTORIOS
# =======================
SCREENSHOT_DIR = os.path.expanduser("~/Desktop")
NOTES_DIR = os.path.expanduser("~/Documents/VoiceNotes")

# =======================
# LOGGING
# =======================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR
LOG_TRANSCRIPTIONS = os.getenv("LOG_TRANSCRIPTIONS", "true").lower() == "true"
