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


def print_status(emoji: str, label: str, color: str, text: str = "") -> None:
    """Imprime una linea de estado con formato visual limpio."""
    msg = f"{color}{COLOR_BOLD}{emoji}  {label}{COLOR_RESET}"
    if text:
        msg += f"  {COLOR_GRAY}{text}{COLOR_RESET}"
    print(f"\r{msg}")


class WhisperVoiceAssistant:
    def __init__(self):
        self.running = False
        print_status("...", "Cargando modelo Whisper", COLOR_GRAY, WHISPER_MODEL)
        self.model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE
        )
        print_status("OK ", "Modelo Whisper listo", COLOR_GREEN)

        # Inicializar PyAudio
        self.audio = pyaudio.PyAudio()
        self.chunk_size = int(AUDIO_SAMPLE_RATE * 0.5)  # 500ms de buffer

    def _record_audio(self, duration: float) -> np.ndarray:
        """Graba audio durante un numero de segundos."""
        frames = []
        num_frames = int(AUDIO_SAMPLE_RATE / self.chunk_size * duration)
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=AUDIO_CHANNELS,
            rate=AUDIO_SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        for _ in range(num_frames):
            data = stream.read(self.chunk_size, exception_on_overflow=False)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
        return audio_data.astype(np.float32) / 32768.0

    def _has_speech(self, audio: np.ndarray, threshold: float = 0.01) -> bool:
        """Detecta si hay voz en el audio por nivel de energia RMS."""
        rms = np.sqrt(np.mean(audio ** 2))
        return rms > threshold

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

        # Cabecera de bienvenida
        print()
        print(f"{COLOR_BOLD}{COLOR_CYAN}{'=' * 50}{COLOR_RESET}")
        print(f"{COLOR_BOLD}{COLOR_CYAN}   Whisper Voice Assistant para macOS{COLOR_RESET}")
        print(f"{COLOR_BOLD}{COLOR_CYAN}{'=' * 50}{COLOR_RESET}")
        print(f"{COLOR_GRAY}  Modelo : {WHISPER_MODEL} | Idioma: {WHISPER_LANGUAGE}{COLOR_RESET}")
        print(f"{COLOR_GRAY}  Sal con Ctrl+C{COLOR_RESET}")
        print(f"{COLOR_BOLD}{COLOR_CYAN}{'=' * 50}{COLOR_RESET}")
        print()

        # Saludo inicial
        print_status(">>>", "Hablando", COLOR_BLUE, "Hola, estoy listo. Puedes hablarme.")
        speak("Hola, estoy listo. Puedes hablarme.")

        try:
            while self.running:
                # Estado: escuchando
                print_status("MIC", "Escuchando...", COLOR_CYAN)
                audio = self._record_audio(AUDIO_CHUNK_DURATION)

                # Filtro de silencio
                if not self._has_speech(audio):
                    print_status("---", "Silencio", COLOR_GRAY)
                    continue

                # Estado: transcribiendo
                print_status("...", "Transcribiendo...", COLOR_YELLOW)
                text = self._transcribe(audio)

                if not text:
                    print_status("---", "Sin texto detectado", COLOR_GRAY)
                    continue

                # Mostrar lo que dijo el usuario
                print_status("TU ", "Tu", COLOR_GREEN, f'"{text}"')
                if LOG_TRANSCRIPTIONS:
                    logger.debug(f"Transcripcion: {text}")

                # Estado: pensando (llamada a Groq)
                print_status("...", "Pensando...", COLOR_YELLOW)
                response = ask_groq(text)

                # Estado: hablando
                print_status(">>>", "Asistente", COLOR_BLUE, f'"{response}"')
                speak(response)

        except KeyboardInterrupt:
            print()
            print(f"{COLOR_GRAY}  Deteniendo asistente...{COLOR_RESET}")
        finally:
            self.stop()

    def stop(self):
        """Detiene el asistente y libera recursos."""
        self.running = False
        self.audio.terminate()
        print_status("BYE", "Hasta luego", COLOR_CYAN)
        speak("Hasta luego.")


if __name__ == "__main__":
    assistant = WhisperVoiceAssistant()
    assistant.run()
