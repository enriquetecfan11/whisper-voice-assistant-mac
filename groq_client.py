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
    try:
        return path.read_text(encoding="utf-8").strip()
    except IOError as e:
        logger.warning(f"No se pudo leer {filename}: {e}")
        return ""


def _build_system_prompt() -> str:
    """
    Construye el system prompt completo combinando:
    1. SYSTEM.md  -> capacidades, reglas, entorno tecnico
    2. SOUL.md    -> personalidad, tono, caracter
    3. Memoria    -> hechos e info del usuario de sesiones anteriores
    4. Fallback   -> GROQ_SYSTEM_PROMPT del .env si los .md no existen
    """
    parts = []

    system_md = _load_md("SYSTEM.md")
    soul_md = _load_md("SOUL.md")
    memory_text = get_memory_as_text()

    if system_md:
        parts.append(system_md)
    if soul_md:
        parts.append(soul_md)

    if not parts:
        parts.append(GROQ_SYSTEM_PROMPT)

    if memory_text:
        parts.append(f"\n---\n{memory_text}")

    return "\n\n".join(parts)


def _handle_system_commands(text: str) -> Optional[str]:
    """
    Detecta comandos especiales de sistema en el texto transcrito.
    Devuelve la respuesta directa si es un comando, None si no lo es.
    """
    text_lower = text.lower().strip()

    if any(w in text_lower for w in ["borra el historial", "limpia el historial", "nueva conversacion"]):
        _conversation_history.clear()
        return "Historial limpiado. Empezamos de cero."

    if any(w in text_lower for w in ["que recuerdas", "que sabes de mi", "lo que recuerdas"]):
        return get_summary()

    if any(w in text_lower for w in ["olvida todo", "borra todo lo que sabes", "borra tu memoria"]):
        forget_all()
        return "Memoria borrada. Ya no recuerdo nada."

    return None


def ask_groq(user_text: str) -> str:
    """
    Envia el texto del usuario a la API de Groq y devuelve la respuesta del LLM.
    - Detecta comandos de sistema antes de llamar a la API
    - Carga SYSTEM.md + SOUL.md + memoria en el system prompt
    - Mantiene historial de conversacion durante la sesion
    """
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY no configurada en .env")
        return "No tengo configurada la clave de Groq. Revisa el archivo punto env."

    system_response = _handle_system_commands(user_text)
    if system_response is not None:
        return system_response

    client = _get_client()

    _conversation_history.append({"role": "user", "content": user_text})

    system_prompt = _build_system_prompt()
    messages = [{"role": "system", "content": system_prompt}] + _conversation_history

    try:
        logger.info(f"Enviando a Groq ({GROQ_MODEL}): '{user_text}'")
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=300,
        )
        assistant_reply = response.choices[0].message.content.strip()

        _conversation_history.append({"role": "assistant", "content": assistant_reply})

        if len(_conversation_history) > 20:
            _conversation_history.pop(0)
            _conversation_history.pop(0)

        logger.info(f"Respuesta Groq: '{assistant_reply}'")
        return assistant_reply

    except Exception as e:
        logger.error(f"Error llamando a Groq LLM: {e}")
        return "Ha ocurrido un error al consultar la inteligencia artificial."


def _speak_groq_tts(text: str) -> bool:
    """
    Convierte texto a voz usando la API TTS de Groq (canopylabs/orpheus).
    Solo soporta ingles. Devuelve True si tuvo exito, False si fallo.
    """
    if not GROQ_API_KEY:
        return False
    try:
        client = _get_client()
        label = f"'{text[:50]}...'" if len(text) > 50 else f"'{text}'"
        logger.info(f"Groq TTS ({GROQ_TTS_VOICE}): {label}")

        response = client.audio.speech.create(
            model=GROQ_TTS_MODEL,
            voice=GROQ_TTS_VOICE,
            input=text,
            response_format="wav",
        )

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(response.read())

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
    Convierte texto a voz eligiendo el motor segun configuracion.
    Groq TTS solo funciona en ingles; para otros idiomas usa macOS say.
    """
    if not text:
        return

    language_is_english = WHISPER_LANGUAGE.lower() in ("en", "english")

    if TTS_ENGINE == "groq" and language_is_english:
        success = _speak_groq_tts(text)
        if not success:
            _speak_macos_say(text)
    else:
        if TTS_ENGINE == "groq" and not language_is_english:
            logger.debug(f"Groq TTS solo soporta ingles. Usando macOS say para '{WHISPER_LANGUAGE}'.")
        _speak_macos_say(text)


def clear_history() -> None:
    """Limpia el historial de conversacion de la sesion actual."""
    _conversation_history.clear()
    logger.info("Historial de conversacion limpiado")
