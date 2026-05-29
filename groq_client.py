import io
import logging
import subprocess
import tempfile
import os
from groq import Groq
from config import (
    GROQ_API_KEY, GROQ_MODEL, GROQ_SYSTEM_PROMPT,
    TTS_ENGINE, GROQ_TTS_MODEL, GROQ_TTS_VOICE,
    TTS_VOICE, TTS_RATE, WHISPER_LANGUAGE
)

logger = logging.getLogger(__name__)

# Historial de conversacion (mantiene contexto entre turnos)
_conversation_history = []

# Cliente Groq reutilizable
_groq_client = None


def _get_client() -> Groq:
    """Devuelve el cliente Groq, inicializandolo si es necesario."""
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=GROQ_API_KEY)
    return _groq_client


def ask_groq(user_text: str) -> str:
    """
    Envia el texto del usuario a la API de Groq y devuelve la respuesta del LLM.
    Mantiene historial de conversacion para contexto.
    """
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY no configurada en .env")
        return "No tengo configurada la API de Groq. Revisa el archivo punto env"

    client = _get_client()

    _conversation_history.append({"role": "user", "content": user_text})
    messages = [{"role": "system", "content": GROQ_SYSTEM_PROMPT}] + _conversation_history

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

        # Limitar historial a los ultimos 10 turnos
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
        logger.info(f"Groq TTS ({GROQ_TTS_VOICE}): '{text[:50]}...'" if len(text) > 50 else f"Groq TTS: '{text}'")

        response = client.audio.speech.create(
            model=GROQ_TTS_MODEL,
            voice=GROQ_TTS_VOICE,
            input=text,
            response_format="wav",
        )

        # Guardar en archivo temporal y reproducir con afplay (nativo macOS)
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
    Convierte texto a voz eligiendo el motor segun configuracion:
    - 'groq': Groq TTS API (orpheus, solo EN) con fallback automatico a say
    - 'say':  macOS say directamente (soporta ES y EN)

    Si el idioma configurado NO es 'en', siempre usa macOS say
    independientemente de TTS_ENGINE, ya que Groq TTS solo soporta ingles.
    """
    if not text:
        return

    # Groq TTS solo funciona en ingles
    language_is_english = WHISPER_LANGUAGE.lower() in ("en", "english")

    if TTS_ENGINE == "groq" and language_is_english:
        # Intentar Groq TTS, si falla usar say
        success = _speak_groq_tts(text)
        if not success:
            _speak_macos_say(text)
    else:
        # say para espanol u otros idiomas
        if TTS_ENGINE == "groq" and not language_is_english:
            logger.debug(
                "Groq TTS solo soporta ingles. Usando macOS say "
                f"para idioma '{WHISPER_LANGUAGE}'."
            )
        _speak_macos_say(text)


def clear_history() -> None:
    """Limpia el historial de conversacion."""
    _conversation_history.clear()
    logger.info("Historial de conversacion limpiado")
