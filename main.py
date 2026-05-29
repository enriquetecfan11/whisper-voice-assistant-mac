#!/usr/bin/env python3
"""
Whisper Voice Assistant para macOS

Asistente de voz local que usa faster-whisper para transcripcion,
Groq API para respuestas con LLM y macOS 'say' para hablar.

Uso:
    python main.py   # Escucha continuamente y responde por voz
"""
import logging
import sys
import numpy as np
import pyaudio
from faster_whisper import WhisperModel
from config import (
    WHISPER_MODEL, WHISPER_LANGUAGE, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE,
    AUDIO_SAMPLE_RATE, AUDIO_CHANNELS, AUDIO_CHUNK_DURATION,
    LOG_LEVEL, LOG_TRANSCRIPTIONS
)
from groq_client import ask_groq, speak
from actions import process_command

# Configurar logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Colores ANSI para la terminal
COLOR_RESET  = "\033[0m"
COLOR_CYAN   = "\033[96m"
COLOR_GREEN  = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_BLUE   = "\033[94m"
COLOR_GRAY   = "\033[90m"
COLOR_BOLD   = "\033[1m"

# Palabras clave que indican comandos de accion directa (no LLM)
ACTION_KEYWORDS = [
    "abre", "abrir", "captura", "screenshot", "pantalla",
    "anota", "apunta", "busca", "buscar", "googlea"
]


def print_status(icon: str, color: str, label: str, message: str = "") -> None:
    """Imprime una linea de estado con formato y color."""
    if message:
        print(f"{color}{COLOR_BOLD}{icon}  {label}{COLOR_RESET}  {message}")
    else:
        print(f"{color}{COLOR_BOLD}{icon}  {label}{COLOR_RESET}")


def is_action_command(text: str) -> bool:
    """Detecta si el texto es un comando de accion directa (abrir app, buscar, etc)."""
    text_lower = text.lower().strip()
    return any(kw in text_lower for kw in ACTION_KEYWORDS)


class WhisperVoiceAssistant:
    def __init__(self):
        print_status(">>>", COLOR_CYAN, "Cargando", f"Modelo Whisper '{WHISPER_MODEL}'...")
        self.model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE
        )
        self.audio = pyaudio.PyAudio()
        self.running = False
        print_status("OK ", COLOR_GREEN, "Listo", "Modelo cargado")

    def _record_audio(self, duration: int) -> np.ndarray:
        """Graba audio del microfono durante 'duration' segundos."""
        stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=AUDIO_CHANNELS,
            rate=AUDIO_SAMPLE_RATE,
            input=True,
            frames_per_buffer=1024
        )
        frames = []
        num_chunks = int(AUDIO_SAMPLE_RATE / 1024 * duration)
        for _ in range(num_chunks):
            data = stream.read(1024, exception_on_overflow=False)
            frames.append(np.frombuffer(data, dtype=np.float32))
        stream.stop_stream()
        stream.close()
        return np.concatenate(frames)

    def _has_speech(self, audio: np.ndarray) -> bool:
        """Detecta si hay voz en el audio por energia RMS."""
        rms = np.sqrt(np.mean(audio ** 2))
        return rms > 0.01

    def _transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio usando faster-whisper."""
        segments, info = self.model.transcribe(
            audio,
            language=WHISPER_LANGUAGE,
            beam_size=5,
            vad_filter=True
        )
        text = " ".join(segment.text for segment in segments).strip()
        return text

    def run(self):
        """Inicia el asistente de voz escuchando continuamente."""
        self.running = True

        print(f"\n{'='*50}")
        print(f"   {COLOR_BOLD}Whisper Voice Assistant para macOS{COLOR_RESET}")
        print(f"{'='*50}")
        print(f"  Modelo : {WHISPER_MODEL} | Idioma: {WHISPER_LANGUAGE}")
        print(f"  Sal con Ctrl+C")
        print(f"{'='*50}\n")

        # Saludo inicial
        greeting = "Hola, estoy listo. Puedes hablarme."
        print_status(">>>", COLOR_CYAN, " Hablando ", greeting)
        speak(greeting)

        try:
            while self.running:
                # Estado: escuchando
                print_status("MIC", COLOR_BLUE, " Escuchando...")
                audio = self._record_audio(AUDIO_CHUNK_DURATION)

                # Filtro de silencio
                if not self._has_speech(audio):
                    continue

                # Estado: transcribiendo
                print_status("...", COLOR_GRAY, " Transcribiendo...")
                text = self._transcribe(audio)

                if not text:
                    continue

                print_status("TU ", COLOR_GREEN, " Tu ", f'"{text}"')

                if LOG_TRANSCRIPTIONS:
                    logger.debug(f"Transcripcion: {text}")

                # Detectar si es un comando de accion directa
                if is_action_command(text):
                    print_status("CMD", COLOR_YELLOW, " Accion ", f'"{text}"')
                    action_result = process_command(text)
                    logger.info(f"Accion ejecutada: {action_result}")
                    # Confirmar la accion con el LLM para dar respuesta natural
                    response = ask_groq(f"[ACCION EJECUTADA: {action_result}] Confirma brevemente al usuario que realizaste: {text}")
                else:
                    # Conversacion normal con el LLM
                    print_status("...", COLOR_GRAY, " Pensando...")
                    response = ask_groq(text)

                # Estado: hablando
                print_status(">>>", COLOR_CYAN, " Asistente ", f'"{response}"')
                speak(response)

        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Detiene el asistente limpiamente."""
        self.running = False
        print(f"\n  {COLOR_YELLOW}Deteniendo asistente...{COLOR_RESET}")
        farewell = "Hasta luego"
        print_status("BYE", COLOR_CYAN, " Hasta luego")
        speak(farewell)
        self.audio.terminate()


if __name__ == "__main__":
    assistant = WhisperVoiceAssistant()
    assistant.run()
