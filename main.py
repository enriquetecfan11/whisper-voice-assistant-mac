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


class WhisperVoiceAssistant:
    def __init__(self):
        self.running = False
        logger.info(f"Cargando modelo Whisper: {WHISPER_MODEL}")
        self.model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE
        )
        logger.info("Modelo Whisper cargado")

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
        logger.info("=" * 50)
        logger.info("Whisper Voice Assistant para macOS")
        logger.info("Escuchando continuamente... (Ctrl+C para salir)")
        logger.info("Habla con normalidad, Groq respondera por voz")
        logger.info("=" * 50)

        # Saludo inicial
        speak("Hola, estoy listo. Puedes hablarme.")

        try:
            while self.running:
                logger.info("-" * 40)
                logger.info(f"Grabando {AUDIO_CHUNK_DURATION}s... habla ahora")
                audio = self._record_audio(AUDIO_CHUNK_DURATION)

                # Filtro de silencio: no enviar a Whisper ni a Groq si no hay voz
                if not self._has_speech(audio):
                    logger.debug("Silencio detectado, saltando...")
                    continue

                # Transcribir voz a texto
                text = self._transcribe(audio)

                if not text:
                    logger.debug("Transcripcion vacia")
                    continue

                if LOG_TRANSCRIPTIONS:
                    logger.info(f"Tu: '{text}'")

                # Enviar a Groq y obtener respuesta
                logger.info("Consultando Groq...")
                response = ask_groq(text)
                logger.info(f"Asistente: '{response}'")

                # Hablar la respuesta en voz alta
                speak(response)

        except KeyboardInterrupt:
            logger.info("\nDeteniendo asistente...")
        finally:
            self.stop()

    def stop(self):
        """Detiene el asistente y libera recursos."""
        self.running = False
        self.audio.terminate()
        speak("Hasta luego.")
        logger.info("Asistente detenido.")


if __name__ == "__main__":
    assistant = WhisperVoiceAssistant()
    assistant.run()
