import logging
from typing import Optional
import subprocess
import tempfile
import os
from pathlib import Path
from groq import Groq
from config import (
    GROQ_API_KEY, GROQ_MODEL, GROQ_SYSTEM_PROMPT,
    TTS_ENGINE, GROQ_TTS_MODEL, GROQ_TTS_VOICE,
    TTS_VOICE, TTS_RATE, WHISPER_LANGUAGE
)
from memory import get_memory_as_text, remember, forget_all, get_summary

logger = logging.getLogger(__name__)

# Historial de conversacion en memoria de sesion
_conversation_history = []

# Cliente Groq reutilizable
_groq_client = None

# Directorio raiz del proyecto (donde estan SYSTEM.md y SOUL.md)
_BASE_DIR = Path(__file__).parent


def _get_client() -> Groq:
    """Devuelve el cliente Groq, inicializandolo si es necesario."""
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


def _load_md(filename: str) -> str:
    """Carga un archivo Markdown del proyecto. Devuelve string vacio si no existe."""
    path = _BASE_DIR / filename
    if not path.exists():
        logger.warning(f"{filename} no encontrado en {_BASE_DIR}")
        return ""
    return path.read_text(encoding="utf-8")


def _build_system_prompt() -> str:
    """Construye el system prompt combinando SYSTEM.md, SOUL.md y memoria persistente."""
    system_md = _load_md("SYSTEM.md")
    soul_md = _load_md("SOUL.md")
    memory_text = get_memory_as_text()

    parts = []
    if system_md:
        parts.append(system_md)
    if soul_md:
        parts.append(f"\n\n## Personalidad y alma\n{soul_md}")
    if memory_text:
        parts.append(f"\n\n## Memoria persistente del usuario\n{memory_text}")
    if not parts:
        parts.append(GROQ_SYSTEM_PROMPT)

    return "\n".join(parts)


def _handle_system_commands(text: str) -> Optional[str]:
    """Detecta comandos especiales y los ejecuta. Retorna respuesta o None."""
    t = text.lower().strip()
    if any(k in t for k in ["olvida todo", "borra tu memoria", "resetea tu memoria"]):
        forget_all()
        return "Memoria borrada. Empezamos de cero."
    if any(k in t for k in ["que recuerdas", "que sabes de mi", "resumen de memoria"]):
        summary = get_summary()
        return summary if summary else "No tengo nada guardado sobre ti todavia."
    return None


def ask_groq(user_input: str) -> str:
    """Envia el mensaje al LLM de Groq y devuelve la respuesta."""
    special = _handle_system_commands(user_input)
    if special:
        return special

    if len(user_input.split()) > 4:
        remember(f"Usuario dijo: {user_input}")

    system_prompt = _build_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(_conversation_history[-20:])
    messages.append({"role": "user", "content": user_input})

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=512,
        )
        reply = response.choices[0].message.content.strip()

        _conversation_history.append({"role": "user", "content": user_input})
        _conversation_history.append({"role": "assistant", "content": reply})

        if len(reply.split()) > 6:
            remember(f"Asistente respondio: {reply[:200]}")

        return reply
    except Exception as e:
        logger.error(f"Error en Groq API: {e}")
        return "Lo siento, hubo un error al procesar tu solicitud."


def _speak_groq_tts(text: str) -> bool:
    """Convierte texto a voz usando Groq TTS (PlayAI). Compatible con cualquier version del SDK."""
    try:
        client = _get_client()
        response = client.audio.speech.create(
            model=GROQ_TTS_MODEL,
            voice=GROQ_TTS_VOICE,
            input=text,
            response_format="wav",
        )

        # Compatibilidad con distintas versiones del SDK de Groq
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_path = f.name
            if hasattr(response, 'stream_to_file'):
                f.close()
                response.stream_to_file(tmp_path)
            elif hasattr(response, 'write_to_file'):
                f.close()
                response.write_to_file(tmp_path)
            else:
                # Fallback: leer el contenido directamente
                f.write(response.content)

        subprocess.run(["afplay", tmp_path], check=True)
        os.unlink(tmp_path)
        return True
    except Exception as e:
        logger.warning(f"Groq TTS fallo: {e}. Usando macOS say como fallback.")
        return False


def _speak_macos_say(text: str) -> None:
    """Convierte texto a voz usando el comando 'say' nativo de macOS."""
    try:
        subprocess.run(
            ["say", "-v", TTS_VOICE, "-r", str(TTS_RATE), text],
            check=True
        )
    except Exception as e:
        logger.error(f"Error en macOS say: {e}")


def speak(text: str) -> None:
    """
    Convierte texto a voz.
    Usa siempre Groq TTS (GROQ_TTS_VOICE) si TTS_ENGINE == 'groq'.
    Si Groq TTS falla, usa macOS say como fallback.
    Si TTS_ENGINE != 'groq', usa directamente macOS say.
    """
    if not text:
        return

    if TTS_ENGINE == "groq":
        success = _speak_groq_tts(text)
        if not success:
            _speak_macos_say(text)
    else:
        _speak_macos_say(text)


def clear_history() -> None:
    """Limpia el historial de conversacion de la sesion actual."""
    global _conversation_history
    _conversation_history = []
    logger.info("Historial de conversacion limpiado")
