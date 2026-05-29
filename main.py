#!/usr/bin/env python3
"""
Whisper Voice Assistant para macOS

Asistente de voz local que usa faster-whisper para transcripción
y detecta comandos de voz para ejecutar acciones en macOS.

Uso:
    python main.py              # Siempre escuchando (modo directo)
    python main.py --hotword    # Activado por hotword con Porcupine
"""

import argparse
import logging
import sys
import time
import queue
import threading
import numpy as np
import pyaudio
from faster_whisper import WhisperModel

from config import (
    WHISPER_MODEL, WHISPER_LANGUAGE, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE,
    AUDIO_SAMPLE_RATE, AUDIO_CHANNELS, AUDIO_CHUNK_DURATION,
    PORCUPINE_ACCESS_KEY, HOTWORD, ALWAYS_LISTEN, LOG_LEVEL, LOG_TRANSCRIPTIONS
)
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


class WhisperVoiceAssistant:
    def __init__(self, use_hotword: bool = False):
        self.use_hotword = use_hotword
        self.running = False
        self.audio_queue = queue.Queue()

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

        # Inicializar Porcupine si se usa hotword
        self.porcupine = None
        if use_hotword:
            self._init_porcupine()

    def _init_porcupine(self):
        """Inicializa la detección de hotword con Porcupine."""
        try:
            import pvporcupine
            if not PORCUPINE_ACCESS_KEY:
                logger.error("PORCUPINE_ACCESS_KEY no configurada en .env")
                logger.error("Obtén tu clave gratuita en: https://console.picovoice.ai/")
                sys.exit(1)
            self.porcupine = pvporcupine.create(
                access_key=PORCUPINE_ACCESS_KEY,
                keywords=[HOTWORD]
            )
            logger.info(f"Hotword activo: '{HOTWORD}'")
        except ImportError:
            logger.error("pvporcupine no instalado. Ejecuta: pip install pvporcupine")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error al inicializar Porcupine: {e}")
            sys.exit(1)

    def _record_audio(self, duration: float) -> np.ndarray:
        """Graba audio durante un número de segundos."""
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

    def _listen_with_hotword(self):
        """Modo con detección de hotword antes de escuchar."""
        frame_length = self.porcupine.frame_length
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.porcupine.sample_rate,
            input=True,
            frames_per_buffer=frame_length
        )
        logger.info(f"Esperando hotword '{HOTWORD}'... (Ctrl+C para salir)")
        try:
            while self.running:
                pcm = stream.read(frame_length, exception_on_overflow=False)
                pcm = np.frombuffer(pcm, dtype=np.int16)
                result = self.porcupine.process(pcm)
                if result >= 0:
                    logger.info(f"Hotword detectado! Escuchando comando...")
                    stream.stop_stream()
                    audio = self._record_audio(AUDIO_CHUNK_DURATION)
                    stream.start_stream()
                    text = self._transcribe(audio)
                    if text:
                        if LOG_TRANSCRIPTIONS:
                            logger.info(f"Transcripción: '{text}'")
                        result = process_command(text)
                        logger.info(f"Resultado: {result}")
        finally:
            stream.stop_stream()
            stream.close()

    def _listen_always(self):
        """Modo siempre escuchando, sin hotword."""
        logger.info(f"Escuchando continuamente... (Ctrl+C para salir)")
        logger.info("Comandos disponibles: captura, anota, busca, abre")
        while self.running:
            logger.info("-" * 40)
            logger.info(f"Grabando {AUDIO_CHUNK_DURATION}s...")
            audio = self._record_audio(AUDIO_CHUNK_DURATION)
            text = self._transcribe(audio)
            if text:
                if LOG_TRANSCRIPTIONS:
                    logger.info(f"Transcripción: '{text}'")
                result = process_command(text)
                logger.info(f"Resultado: {result}")
            else:
                logger.debug("No se detectó voz")

    def run(self):
        """Inicia el asistente de voz."""
        self.running = True
        logger.info("=" * 50)
        logger.info("Whisper Voice Assistant para macOS")
        logger.info("=" * 50)
        try:
            if self.use_hotword and self.porcupine:
                self._listen_with_hotword()
            else:
                self._listen_always()
        except KeyboardInterrupt:
            logger.info("\nDeteniendo asistente...")
        finally:
            self.stop()

    def stop(self):
        """Detiene el asistente y libera recursos."""
        self.running = False
        if self.porcupine:
            self.porcupine.delete()
        self.audio.terminate()
        logger.info("Asistente detenido.")


def main():
    parser = argparse.ArgumentParser(
        description="Asistente de voz local para macOS usando Whisper"
    )
    parser.add_argument(
        "--hotword",
        action="store_true",
        help=f"Activar mediante hotword '{HOTWORD}' (requiere PORCUPINE_ACCESS_KEY en .env)"
    )
    args = parser.parse_args()

    use_hotword = args.hotword
    assistant = WhisperVoiceAssistant(use_hotword=use_hotword)
    assistant.run()


if __name__ == "__main__":
    main()
