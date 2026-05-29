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

# =======================
# GROQ API
# =======================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")  # llama3-70b-8192, mixtral-8x7b-32768, gemma-7b-it
GROQ_SYSTEM_PROMPT = os.getenv(
    "GROQ_SYSTEM_PROMPT",
    "Eres un asistente de voz para macOS. Responde siempre en el mismo idioma que el usuario. "
    "Tus respuestas deben ser cortas, claras y naturales para ser escuchadas en voz alta. "
    "No uses markdown, listas con guiones ni emojis. Habla como si fueras una persona."
)

# =======================
# TTS (Text to Speech)
# =======================
# Voz de macOS para el comando 'say'. Opciones en ES: Monica, Jorge
# Opciones en EN: Samantha, Alex
TTS_VOICE = os.getenv("TTS_VOICE", "Monica")
TTS_RATE = int(os.getenv("TTS_RATE", "175"))  # palabras por minuto (default macOS: 175)
